from datetime import date, datetime
import re
from .exceptions import InvalidAmountError, InvalidCategoryError
from .theme import format_amount


class ExpenseTracker:

    def __init__(self, user):
        self.user = user

    @property
    def expense_report(self):
        return self.user.get_category_expenses()

    # Backward-compatible alias
    @property
    def expenseReport(self):
        return self.expense_report

    def add_expense(self, category_lower, amount, note="", date_val=None):
        self.user.add_transaction(category_lower, amount, note, date_val)
        return self.user.get_category_expenses().get(category_lower.lower().strip(), 0.0)

    def remove_expense(self, category_lower, amount):
        category = category_lower.lower().strip()
        if not self.user.is_valid_category(category):
            raise InvalidCategoryError(f"'{category}' is not a recognized category.")
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            raise InvalidAmountError("Removal amount must be a valid number.")
        if amount_float <= 0:
            raise InvalidAmountError("Removal amount must be greater than zero.")

        current = self.expense_report.get(category, 0.0)
        # Round both sides to avoid IEEE 754 false positives (e.g. 20.000000000000004 > 20.0)
        if round(amount_float, 2) > round(current, 2):
            raise InvalidAmountError(
                f"Cannot remove {format_amount(amount_float, self.user.currency)}. "
                f"Current spending in '{category}' is only {format_amount(current, self.user.currency)}."
            )

        self.user.add_transaction(
            category, -amount_float, note="Expense removal adjustment", allow_negative=True
        )

    def get_status_report(self, month=None):
        period_title = f" (Period: {month})" if month else " (All Time)"
        report = [
            f"===== Financial Summary for {self.user.name}{period_title} =====",
            f"Account Base Currency: {self.user.currency}",
            "-" * 66,
            f"{'Category':<16} | {'Spent':<12} | {'Limit':<14} | {'Status':<16}",
            "-" * 66,
        ]

        category_expenses = self.user.get_category_expenses(month=month)
        for category in self.user.categories:
            spent = category_expenses.get(category, 0.0)
            limit = self.user.budget_limits.get(category, "No Limit")
            status = "✅ OK" if limit == "No Limit" or spent <= limit else "❌ OVER"
            limit_str = f"{limit:,.2f}" if isinstance(limit, (int, float)) else limit
            report.append(
                f"{category.capitalize():<16} | {spent:<12,.2f} | {limit_str:<14} | {status:<16}"
            )

        report.append("-" * 66)
        total_spent = self.user.total_expenses(month=month)
        total_income = self.user.total_income(month=month)
        net_savings = self.user.get_net_savings(month=month)
        savings_rate = self.user.get_savings_rate(month=month)
        total_budget = sum(self.user.budget_limits.values())

        report.append(
            f"Total Spent:    {format_amount(total_spent, self.user.currency)}\n"
            f"Total Income:   {format_amount(total_income, self.user.currency)}\n"
            f"Net Savings:    {format_amount(net_savings, self.user.currency)} ({savings_rate}%)\n"
            f"Total Budget:   {format_amount(total_budget, self.user.currency)}"
        )
        return "\n".join(report)

    def total_expenses_of_user(self):
        return self.user.total_expenses()


class StatementParser:

    @staticmethod
    def _parse_date(raw_date):
        if not raw_date:
            return None
        today = date.today()
        min_date = date(1970, 1, 1)
        raw_str = raw_date.strip()
        clean = raw_str.replace("'", "20").replace("-", "").replace("/", "")
        for fmt in ("%Y%m%d", "%m%d%Y", "%d%m%Y", "%Y%m%d%H%M%S"):
            try:
                dt = datetime.strptime(clean[:8] if len(clean) >= 8 else clean, fmt[:len(clean)]).date()
                if min_date <= dt <= today:
                    return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%y", "%d/%m/%y"):
            try:
                dt = datetime.strptime(raw_str, fmt).date()
                if min_date <= dt <= today:
                    return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @classmethod
    def parse_qif(cls, content):
        lines = content.splitlines()
        transactions = []
        current = {}
        date_rejected = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line == "^":
                if current and "amount" in current and not date_rejected:
                    current.setdefault("date", date.today().strftime("%Y-%m-%d"))
                    transactions.append(current)
                current = {}
                date_rejected = False
                continue
            code = line[0]
            val = line[1:].strip()
            if code == "D":
                parsed_d = cls._parse_date(val)
                if parsed_d:
                    current["date"] = parsed_d
                else:
                    date_rejected = True
            elif code in ("T", "U"):
                try:
                    current["amount"] = float(val.replace(",", ""))
                except ValueError:
                    pass
            elif code == "P":
                current["payee"] = val
            elif code in ("L", "M"):
                current["memo"] = val

        if current and "amount" in current and not date_rejected:
            current.setdefault("date", date.today().strftime("%Y-%m-%d"))
            transactions.append(current)
        return transactions

    @classmethod
    def parse_ofx(cls, content):
        blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", content, re.DOTALL | re.IGNORECASE)
        if not blocks:
            blocks = re.split(r"<STMTTRN>", content, flags=re.IGNORECASE)[1:]

        transactions = []
        for block in blocks:
            trn = {}
            amt_match = re.search(r"<TRNAMT>\s*([+-]?\d+(?:\.\d+)?|\.\d+)", block, re.IGNORECASE)
            date_match = re.search(r"<DTPOSTED>\s*(\d+)", block, re.IGNORECASE)
            name_match = re.search(r"<NAME>\s*([^<\r\n]+)", block, re.IGNORECASE)
            memo_match = re.search(r"<MEMO>\s*([^<\r\n]+)", block, re.IGNORECASE)

            if amt_match:
                try:
                    trn["amount"] = float(amt_match.group(1))
                except ValueError:
                    continue

            date_rejected = False
            if date_match:
                parsed_d = cls._parse_date(date_match.group(1))
                if parsed_d:
                    trn["date"] = parsed_d
                else:
                    date_rejected = True

            if date_rejected:
                continue

            payee = []
            if name_match:
                payee.append(name_match.group(1).strip())
            if memo_match:
                payee.append(memo_match.group(1).strip())
            trn["payee"] = " - ".join(payee) if payee else "Bank Statement Transaction"

            if "amount" in trn:
                trn.setdefault("date", date.today().strftime("%Y-%m-%d"))
                transactions.append(trn)
        return transactions

    @classmethod
    def parse_file(cls, filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        lower = filepath.lower()
        if lower.endswith(".qif") or "!Type:" in content:
            return cls.parse_qif(content)
        return cls.parse_ofx(content)