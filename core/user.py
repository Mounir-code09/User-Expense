import copy
import csv
from datetime import date, datetime
import uuid

from .currency_service import currency_service
from .data_manager import (
    DEFAULT_CATEGORIES,
    delete_user_data,
    get_all_usernames,
    load_user,
    normalize_username,
    save_user,
)
from .exceptions import (
    CategoryAlreadyExistsError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
)


class User:

    def __init__(self, name):
        self.name = normalize_username(name)
        if not self.name:
            raise ValueError("Username cannot be blank.")

        is_existing = self.name in get_all_usernames()
        user_data = load_user(self.name)

        self.currency = user_data.get("currency", "USD")
        self.categories = copy.deepcopy(user_data.get("categories", DEFAULT_CATEGORIES.copy()))
        self.budget_limits = copy.deepcopy(user_data.get("budget_limits", {}))
        self.transactions = copy.deepcopy(user_data.get("transactions", []))
        self.incomes = copy.deepcopy(user_data.get("incomes", []))
        self.templates = copy.deepcopy(user_data.get("templates", {"expenses": [], "incomes": []}))
        self.templates.setdefault("expenses", [])
        self.templates.setdefault("incomes", [])
        self.password_hash = user_data.get("password_hash", "")
        self.security_question = user_data.get("security_question", "")
        self.security_answer_hash = user_data.get("security_answer_hash", "")
        self.failed_attempts = user_data.get("failed_attempts", 0)
        self.lockout_until = user_data.get("lockout_until", 0)
        self.payee_rules = copy.deepcopy(user_data.get("payee_rules", {}))
        self.savings_goals = copy.deepcopy(user_data.get("savings_goals", []))

        if not is_existing:
            self.save()

    @property
    def budget_limit(self):
        return self.budget_limits

    @budget_limit.setter
    def budget_limit(self, value):
        self.budget_limits = value

    @property
    def current_expenses(self):
        return self.get_category_expenses()

    def to_dict(self):
        return {
            "currency": self.currency,
            "categories": self.categories,
            "budget_limits": self.budget_limits,
            "transactions": self.transactions,
            "incomes": self.incomes,
            "templates": self.templates,
            "password_hash": self.password_hash,
            "security_question": self.security_question,
            "security_answer_hash": self.security_answer_hash,
            "failed_attempts": self.failed_attempts,
            "lockout_until": self.lockout_until,
            "payee_rules": self.payee_rules,
            "savings_goals": self.savings_goals,
        }

    def save(self):
        save_user(self.name, self.to_dict())

    def is_valid_category(self, category):
        if not category:
            return False
        return category.lower().strip() in [c.lower() for c in self.categories]

    def add_custom_category(self, category_name):
        clean = category_name.lower().strip()
        if not clean:
            raise InvalidCategoryError("Category name cannot be blank.")
        if clean in [c.lower() for c in self.categories]:
            raise CategoryAlreadyExistsError(f"Category '{clean}' already exists.")
        self.categories.append(clean)
        self.save()
        return clean

    def set_budget_limit(self, category_clean, limit):
        category = category_clean.lower().strip()
        if not self.is_valid_category(category):
            raise InvalidCategoryError(f"'{category}' is not a recognized category.")
        try:
            limit_float = float(limit)
        except (ValueError, TypeError):
            raise InvalidAmountError("Budget limit must be a valid number.")
        if limit_float < 0:
            raise InvalidAmountError("Budget limit cannot be negative.")
        self.budget_limits[category] = round(limit_float, 2)
        self.save()
        return self

    def check_budget(self, category):
        return self.budget_limits.get(category.lower().strip(), 0.0)

    def add_transaction(self, category_clean, amount, note="", date_val=None, allow_negative=False):
        category = category_clean.lower().strip()
        if not self.is_valid_category(category):
            raise InvalidCategoryError(f"'{category}' is not a recognized category.")

        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            raise InvalidAmountError("Expense amount must be a valid number.")

        if not allow_negative and amount_float <= 0:
            raise InvalidAmountError("Expense amount must be greater than zero.")
        elif allow_negative and amount_float == 0:
            raise InvalidAmountError("Adjustment amount cannot be zero.")

        date_str = self._parse_date(date_val)

        tx = {
            "id": f"tx_{uuid.uuid4().hex[:8]}",
            "date": date_str,
            "category": category,
            "amount": round(amount_float, 2),
            "note": note.strip() if note else "",
        }
        self.transactions.append(tx)
        self.save()
        return tx

    def delete_transaction(self, transaction_id):
        before = len(self.transactions)
        self.transactions = [tx for tx in self.transactions if tx.get("id") != transaction_id]
        if len(self.transactions) < before:
            self.save()
            return True
        return False

    def get_transactions(self, category=None, month=None):
        txs = self.transactions
        if category:
            cat = category.lower().strip()
            txs = [tx for tx in txs if tx.get("category") == cat]
        if month:
            txs = [tx for tx in txs if tx.get("date", "").startswith(month)]
        return sorted(txs, key=lambda tx: tx.get("date", ""), reverse=True)

    def add_income(self, source, amount, note="", date_val=None):
        source_clean = source.strip().title() if source else "General Income"
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            raise InvalidAmountError("Income amount must be a valid number.")
        if amount_float <= 0:
            raise InvalidAmountError("Income amount must be greater than zero.")

        income_entry = {
            "id": f"inc_{uuid.uuid4().hex[:8]}",
            "date": self._parse_date(date_val),
            "source": source_clean,
            "amount": round(amount_float, 2),
            "note": note.strip() if note else "",
        }
        self.incomes.append(income_entry)
        self.save()
        return income_entry

    def delete_income(self, income_id):
        before = len(self.incomes)
        self.incomes = [inc for inc in self.incomes if inc.get("id") != income_id]
        if len(self.incomes) < before:
            self.save()
            return True
        return False

    def get_incomes(self, month=None):
        entries = self.incomes
        if month:
            entries = [inc for inc in entries if inc.get("date", "").startswith(month)]
        return sorted(entries, key=lambda inc: inc.get("date", ""), reverse=True)

    def total_income(self, month=None):
        entries = self.get_incomes(month=month) if month else self.incomes
        return round(sum(inc.get("amount", 0.0) for inc in entries), 2)

    def total_income_of_user(self):
        return self.total_income()

    def get_category_expenses(self, month=None):
        totals = {cat.lower(): 0.0 for cat in self.categories}
        txs = self.get_transactions(month=month) if month else self.transactions
        for tx in txs:
            cat = tx.get("category", "").lower()
            totals[cat] = totals.get(cat, 0.0) + tx.get("amount", 0.0)
        return {cat: round(amt, 2) for cat, amt in totals.items()}

    def total_expenses(self, month=None):
        txs = self.get_transactions(month=month) if month else self.transactions
        return round(sum(tx.get("amount", 0.0) for tx in txs), 2)

    def total_expenses_of_user(self):
        return self.total_expenses()

    def get_remaining_budget(self, month=None):
        return round(sum(self.budget_limits.values()) - self.total_expenses(month=month), 2)

    def get_net_savings(self, month=None):
        return round(self.total_income(month=month) - self.total_expenses(month=month), 2)

    def get_savings_rate(self, month=None):
        inc = self.total_income(month=month)
        if inc <= 0:
            return 0.0
        return round((self.get_net_savings(month=month) / inc) * 100, 1)

    def get_top_category(self, month=None):
        expenses = self.get_category_expenses(month=month)
        active = {c: amt for c, amt in expenses.items() if amt > 0}
        if not active:
            return "None", 0.0
        top = max(active, key=active.get)
        return top.capitalize(), active[top]

    def get_category_budget_progress(self, month=None):
        expenses = self.get_category_expenses(month=month)
        progress = []
        for cat, limit in self.budget_limits.items():
            if limit <= 0:
                continue
            spent = expenses.get(cat, 0.0)
            pct = round((spent / limit) * 100, 1)
            status = "danger" if pct > 100 else ("warning" if pct >= 75 else "success")
            progress.append({
                "category": cat.capitalize(),
                "spent": spent,
                "limit": limit,
                "percentage": pct,
                "ratio": max(0.0, min(spent / limit, 1.0)),
                "status": status,
            })
        return progress

    def get_budget_alerts(self, month=None):
        expenses = self.get_category_expenses(month=month)
        alerts = []
        for cat, limit in self.budget_limits.items():
            if limit <= 0:
                continue
            spent = expenses.get(cat, 0.0)
            pct = round((spent / limit) * 100, 1)
            if pct >= 100:
                alerts.append({
                    "category": cat.capitalize(),
                    "spent": spent,
                    "limit": limit,
                    "percentage": pct,
                    "level": "danger",
                    "message": f"Budget for {cat.capitalize()} has been exceeded ({pct}% spent).",
                })
            elif pct >= 90:
                alerts.append({
                    "category": cat.capitalize(),
                    "spent": spent,
                    "limit": limit,
                    "percentage": pct,
                    "level": "warning",
                    "message": f"Budget for {cat.capitalize()} is nearing limit ({pct}% spent).",
                })
        return alerts

    def add_template(self, template_type, name, category_or_source, amount, note=""):
        tpl_type = template_type.lower().strip()
        if tpl_type not in ("expense", "income"):
            raise ValueError("Template type must be 'expense' or 'income'.")

        name_clean = name.strip()
        if not name_clean:
            raise ValueError("Template name cannot be blank.")

        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            raise InvalidAmountError("Template amount must be a valid number.")
        if amount_float <= 0:
            raise InvalidAmountError("Template amount must be greater than zero.")

        if tpl_type == "expense":
            target = category_or_source.lower().strip()
            if not self.is_valid_category(target):
                raise InvalidCategoryError(f"'{target}' is not a recognized category.")
        else:
            target = category_or_source.strip().title() if category_or_source else "General Income"

        tpl = {
            "id": f"tpl_{uuid.uuid4().hex[:8]}",
            "name": name_clean,
            "type": tpl_type,
            "target": target,
            "amount": round(amount_float, 2),
            "note": note.strip() if note else "",
        }
        section = "expenses" if tpl_type == "expense" else "incomes"
        self.templates[section].append(tpl)
        self.save()
        return tpl

    def delete_template(self, template_id):
        deleted = False
        for section in ("expenses", "incomes"):
            before = len(self.templates[section])
            self.templates[section] = [t for t in self.templates[section] if t.get("id") != template_id]
            if len(self.templates[section]) < before:
                deleted = True
        if deleted:
            self.save()
        return deleted

    def get_templates(self, template_type=None):
        if template_type == "expense":
            return self.templates.get("expenses", [])
        if template_type == "income":
            return self.templates.get("incomes", [])
        return self.templates.get("expenses", []) + self.templates.get("incomes", [])

    def execute_template(self, template_id, date_val=None):
        all_tpls = self.get_templates()
        matched = next((t for t in all_tpls if t.get("id") == template_id), None)
        if not matched:
            raise ValueError("Template not found.")

        if matched["type"] == "expense":
            return self.add_transaction(
                matched["target"], matched["amount"], note=matched.get("note", ""), date_val=date_val
            )
        else:
            return self.add_income(
                matched["target"], matched["amount"], note=matched.get("note", ""), date_val=date_val
            )

    def change_currency(self, amount, from_currency, to_currency):
        return currency_service.convert(amount, from_currency, to_currency)

    def convert_account_currency(self, new_currency):
        if self.currency == new_currency:
            return
        for cat in self.budget_limits:
            self.budget_limits[cat] = self.change_currency(
                self.budget_limits[cat], self.currency, new_currency
            )
        for tx in self.transactions:
            tx["amount"] = self.change_currency(tx["amount"], self.currency, new_currency)
        for inc in self.incomes:
            inc["amount"] = self.change_currency(inc["amount"], self.currency, new_currency)
        for section in ("expenses", "incomes"):
            for tpl in self.templates.get(section, []):
                tpl["amount"] = self.change_currency(tpl["amount"], self.currency, new_currency)
        for goal in self.savings_goals:
            goal["target"] = self.change_currency(goal["target"], self.currency, new_currency)
            goal["current"] = self.change_currency(goal["current"], self.currency, new_currency)
        self.currency = new_currency
        self.save()

    def get_payee_category(self, payee):
        key = (payee or "").strip().lower()
        return self.payee_rules.get(key)

    def learn_payee_category(self, payee, category):
        key = (payee or "").strip().lower()
        cat = (category or "").lower().strip()
        if key and cat and self.is_valid_category(cat):
            self.payee_rules[key] = cat
            self.save()

    def add_savings_goal(self, name, target_amount, current_amount=0.0, target_date=None):
        name_clean = (name or "").strip()
        if not name_clean:
            raise ValueError("Savings goal name cannot be blank.")
        try:
            target = round(float(target_amount), 2)
        except (ValueError, TypeError):
            raise InvalidAmountError("Target amount must be a valid number.")
        if target <= 0:
            raise InvalidAmountError("Target amount must be greater than zero.")
        try:
            current = round(float(current_amount), 2)
        except (ValueError, TypeError):
            current = 0.0
        if current < 0:
            raise InvalidAmountError("Initial saved amount cannot be negative.")

        clean_tdate = ""
        if target_date and str(target_date).strip():
            clean_tdate = str(target_date).strip()

        goal = {
            "id": f"sg_{uuid.uuid4().hex[:8]}",
            "name": name_clean,
            "target": target,
            "current": current,
            "target_date": clean_tdate,
        }
        self.savings_goals.append(goal)
        self.save()
        return goal

    def get_savings_goals(self):
        return list(self.savings_goals)

    def deposit_savings_goal(self, goal_id, amount):
        try:
            amt = round(float(amount), 2)
        except (ValueError, TypeError):
            raise InvalidAmountError("Deposit amount must be a valid number.")
        if amt <= 0:
            raise InvalidAmountError("Deposit amount must be greater than zero.")
        goal = next((g for g in self.savings_goals if g["id"] == goal_id), None)
        if not goal:
            raise ValueError("Savings goal not found.")
        goal["current"] = round(goal["current"] + amt, 2)
        self.save()
        return goal

    def withdraw_savings_goal(self, goal_id, amount):
        goal = next((g for g in self.savings_goals if g["id"] == goal_id), None)
        if not goal:
            raise ValueError("Savings goal not found.")
        if goal["current"] <= 0:
            raise InvalidAmountError("No funds available to withdraw in this savings goal.")
        try:
            amt = round(float(amount), 2)
        except (ValueError, TypeError):
            raise InvalidAmountError("Withdrawal amount must be a valid number.")
        if amt <= 0:
            raise InvalidAmountError("Withdrawal amount must be greater than zero.")
        if amt > goal["current"]:
            raise InvalidAmountError(f"Cannot withdraw {amt:.2f}. Maximum available balance is {goal['current']:.2f}.")
        goal["current"] = round(goal["current"] - amt, 2)
        self.save()
        return goal

    def update_savings_goal(self, goal_id, name=None, target_amount=None, target_date=None):
        goal = next((g for g in self.savings_goals if g["id"] == goal_id), None)
        if not goal:
            raise ValueError("Savings goal not found.")
        if name is not None:
            name_clean = name.strip()
            if not name_clean:
                raise ValueError("Goal name cannot be blank.")
            goal["name"] = name_clean
        if target_amount is not None:
            try:
                t = round(float(target_amount), 2)
            except (ValueError, TypeError):
                raise InvalidAmountError("Target amount must be a valid number.")
            if t <= 0:
                raise InvalidAmountError("Target amount must be greater than zero.")
            goal["target"] = t
        if target_date is not None:
            goal["target_date"] = str(target_date).strip()
        self.save()
        return goal

    def delete_savings_goal(self, goal_id):
        before = len(self.savings_goals)
        self.savings_goals = [g for g in self.savings_goals if g["id"] != goal_id]
        if len(self.savings_goals) < before:
            self.save()
            return True
        return False

    def reset_category(self, category_lower):
        category = category_lower.lower().strip()
        removed_budget = self.budget_limits.pop(category, None)
        removed_expenses = sum(
            tx["amount"] for tx in self.transactions if tx.get("category") == category
        )
        self.transactions = [tx for tx in self.transactions if tx.get("category") != category]
        self.save()
        return {"budget_limit": removed_budget, "expense": round(removed_expenses, 2)}

    def export_to_csv(self, filepath, month=None):
        txs = self.get_transactions(month=month) if month else self.transactions
        incomes = self.get_incomes(month=month) if month else self.incomes

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "ID", "Date", "Category/Source", "Amount", "Currency", "Note"])
            for tx in sorted(txs, key=lambda t: t.get("date") or ""):
                writer.writerow([
                    "Expense", tx.get("id", ""), tx.get("date", ""),
                    tx.get("category", "").capitalize(),
                    f"{tx.get('amount', 0.0):.2f}", self.currency, tx.get("note", ""),
                ])
            for inc in sorted(incomes, key=lambda i: i.get("date") or ""):
                writer.writerow([
                    "Income", inc.get("id", ""), inc.get("date", ""),
                    inc.get("source", "Income"),
                    f"{inc.get('amount', 0.0):.2f}", self.currency, inc.get("note", ""),
                ])
        return filepath

    @staticmethod
    def _parse_date(date_val):
        today = date.today()
        if date_val is None:
            return today.strftime("%Y-%m-%d")

        if isinstance(date_val, (datetime, date)):
            d = date_val.date() if isinstance(date_val, datetime) else date_val
            if d < date(1970, 1, 1):
                raise InvalidDateError("Date cannot be prior to year 1970.")
            if d > today:
                raise InvalidDateError("Transaction date cannot be in the future.")
            return d.strftime("%Y-%m-%d")

        s = str(date_val).strip()
        if not s:
            return today.strftime("%Y-%m-%d")

        try:
            parsed = datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            raise InvalidDateError("Date must be in YYYY-MM-DD format (e.g. 2026-08-14).")

        if parsed < date(1970, 1, 1):
            raise InvalidDateError("Date cannot be prior to year 1970.")
        if parsed > today:
            raise InvalidDateError("Transaction date cannot be in the future.")

        return s


class Users:

    def show_users(self):
        return get_all_usernames()

    def delete_user(self, name):
        return delete_user_data(name)

    def get_user(self, name):
        norm = normalize_username(name)
        if norm and norm in self.show_users():
            return User(norm)
        return None

    def add_user(self, name):
        norm = normalize_username(name)
        if not norm or norm in self.show_users():
            return False
        return User(norm)