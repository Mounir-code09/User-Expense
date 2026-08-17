import os
from datetime import date, timedelta
import pytest
from core.user import User, Users
from core.data_manager import get_all_usernames, DEFAULT_CATEGORIES
from core.exceptions import (
    CategoryAlreadyExistsError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidDateError,
)
from core.theme import format_amount


@pytest.fixture
def mock_ram_db(monkeypatch):
    db = {
        "users": {
            "Alice": {
                "currency": "USD",
                "categories": DEFAULT_CATEGORIES.copy(),
                "budget_limits": {"food": 1500.0, "transport": 600.0},
                "transactions": [
                    {"id": "tx_1", "date": "2026-08-10", "category": "food", "amount": 450.0, "note": "Weekly grocery shopping at Lidl"},
                    {"id": "tx_2", "date": "2026-08-12", "category": "transport", "amount": 120.0, "note": "Monthly train commuter pass"},
                    {"id": "tx_3", "date": "2026-07-15", "category": "food", "amount": 200.0, "note": "July restaurant dinner"},
                ],
                "incomes": [
                    {"id": "inc_1", "date": "2026-08-01", "source": "Salary", "amount": 3500.0, "note": "August paycheck"},
                    {"id": "inc_2", "date": "2026-07-01", "source": "Salary", "amount": 3400.0, "note": "July paycheck"},
                ],
                "templates": {
                    "expenses": [],
                    "incomes": [],
                },
                "password_hash": "ab" * 16 + ":" + "cd" * 32,
                "failed_attempts": 0,
                "lockout_until": 0,
            }
        }
    }
    monkeypatch.setattr("core.data_manager.load_database", lambda: db)
    monkeypatch.setattr("core.data_manager.save_database", lambda data: db.update(data))
    monkeypatch.setattr(
        "core.currency_service.CurrencyService.convert",
        lambda self, amount, from_curr, to_curr: amount * (0.9 if to_curr == "EUR" else 1.0),
    )


def test_format_amount():
    assert format_amount(12345.67) == "12,345.67"
    assert format_amount(12345678.9) == "12,345,678.90"
    assert format_amount(50, "USD") == "50.00 USD"
    assert format_amount(-15200.5, "EUR") == "-15,200.50 EUR"
    assert format_amount("invalid") == "0.00"


def test_user_loads_correctly(mock_ram_db):
    user = User("Alice")
    assert user.name == "Alice"
    assert user.currency == "USD"
    assert user.budget_limits["food"] == 1500.0
    assert len(user.transactions) == 3
    assert len(user.incomes) == 2


def test_blank_username_raises(mock_ram_db):
    with pytest.raises(ValueError, match="blank"):
        User("")
    with pytest.raises(ValueError, match="blank"):
        User("   ")


def test_add_custom_category(mock_ram_db):
    user = User("Alice")
    user.add_custom_category("Subscriptions")
    assert user.is_valid_category("subscriptions")
    assert "subscriptions" in user.categories

    with pytest.raises(CategoryAlreadyExistsError):
        user.add_custom_category("subscriptions")
    with pytest.raises(InvalidCategoryError):
        user.add_custom_category("")


def test_add_and_delete_transaction(mock_ram_db):
    user = User("Alice")
    tx = user.add_transaction("food", 250.50, note="Family dinner", date_val="2026-08-14")
    assert tx["amount"] == 250.50
    assert tx["note"] == "Family dinner"
    assert len(user.transactions) == 4

    assert user.delete_transaction(tx["id"])
    assert len(user.transactions) == 3
    assert not user.delete_transaction("non_existent_id")


def test_future_date_rejected(mock_ram_db):
    user = User("Alice")
    future_day = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")

    with pytest.raises(InvalidDateError, match="future"):
        user.add_transaction("food", 50.0, date_val=future_day)

    with pytest.raises(InvalidDateError, match="future"):
        user.add_income("Salary", 500.0, date_val=future_day)

    with pytest.raises(InvalidDateError, match="1970"):
        user.add_transaction("food", 50.0, date_val="1960-01-01")

    with pytest.raises(InvalidDateError, match="format"):
        user.add_transaction("food", 50.0, date_val="invalid-date")


def test_transaction_with_date_object(mock_ram_db):
    user = User("Alice")
    tx = user.add_transaction("food", 10.0, date_val=date(2026, 8, 14))
    assert tx["date"] == "2026-08-14"


def test_add_and_delete_income(mock_ram_db):
    user = User("Alice")
    inc = user.add_income("Freelance", 500.0, note="Website design", date_val="2026-08-14")
    assert inc["source"] == "Freelance"
    assert inc["amount"] == 500.0
    assert len(user.incomes) == 3

    assert user.delete_income(inc["id"])
    assert len(user.incomes) == 2
    assert not user.delete_income("invalid_id")


def test_financial_totals_and_period_filtering(mock_ram_db):
    user = User("Alice")
    # All time totals
    assert user.total_income() == 6900.0
    assert user.total_expenses() == 770.0
    assert user.get_net_savings() == 6130.0

    # August period
    assert user.total_income(month="2026-08") == 3500.0
    assert user.total_expenses(month="2026-08") == 570.0
    assert user.get_net_savings(month="2026-08") == 2930.0
    assert user.get_savings_rate(month="2026-08") == 83.7

    # July period
    assert user.total_income(month="2026-07") == 3400.0
    assert user.total_expenses(month="2026-07") == 200.0
    assert user.get_net_savings(month="2026-07") == 3200.0


def test_budget_progress_clamping(mock_ram_db):
    user = User("Alice")
    user.transactions.append({"id": "adj", "date": "2026-08-13", "category": "food", "amount": -10000.0, "note": "adj"})
    progress = user.get_category_budget_progress()
    food_item = next(p for p in progress if p["category"] == "Food")
    assert food_item["ratio"] == 0.0


def test_category_budget_progress(mock_ram_db):
    user = User("Alice")
    progress = user.get_category_budget_progress(month="2026-08")
    assert len(progress) == 2

    food_item = next(p for p in progress if p["category"] == "Food")
    assert food_item["spent"] == 450.0
    assert food_item["limit"] == 1500.0
    assert food_item["percentage"] == 30.0
    assert food_item["status"] == "success"


def test_transaction_filter(mock_ram_db):
    user = User("Alice")
    assert len(user.get_transactions(category="food")) == 2
    assert len(user.get_transactions(month="2026-08")) == 2
    assert len(user.get_transactions(month="2026-07")) == 1


def test_dynamic_metrics(mock_ram_db):
    user = User("Alice")
    top_cat, top_amt = user.get_top_category(month="2026-08")
    assert top_cat == "Food"
    assert top_amt == 450.0


def test_set_budget_limit(mock_ram_db):
    user = User("Alice")
    user.set_budget_limit("food", 2000.0)
    assert user.budget_limits["food"] == 2000.0
    user.set_budget_limit("Transport", 750.0)
    assert user.check_budget("transport") == 750.0

    with pytest.raises(InvalidAmountError):
        user.set_budget_limit("food", -50.0)
    with pytest.raises(InvalidCategoryError):
        user.set_budget_limit("unknown_cat", 100.0)


def test_recurring_templates_crud_and_execute(mock_ram_db):
    user = User("Alice")

    # Add expense template
    exp_tpl = user.add_template("expense", "Monthly Rent", "housing", 800.0, "Apartment rent")
    assert exp_tpl["name"] == "Monthly Rent"
    assert exp_tpl["amount"] == 800.0
    assert len(user.get_templates(template_type="expense")) == 1

    # Add income template
    inc_tpl = user.add_template("income", "Salary Paycheck", "Salary", 3500.0, "Monthly salary")
    assert inc_tpl["target"] == "Salary"
    assert len(user.get_templates(template_type="income")) == 1

    # Execute expense template
    tx = user.execute_template(exp_tpl["id"], date_val="2026-08-14")
    assert tx["category"] == "housing"
    assert tx["amount"] == 800.0
    assert tx["note"] == "Apartment rent"

    # Execute income template
    inc = user.execute_template(inc_tpl["id"], date_val="2026-08-14")
    assert inc["source"] == "Salary"
    assert inc["amount"] == 3500.0

    # Delete template
    assert user.delete_template(exp_tpl["id"]) is True
    assert len(user.get_templates(template_type="expense")) == 0


def test_convert_account_currency_updates_templates(mock_ram_db, monkeypatch):
    user = User("Alice")
    tpl = user.add_template("expense", "Coffee", "food", 100.0)
    assert tpl["amount"] == 100.0

    monkeypatch.setattr("core.currency_service.currency_service.convert", lambda amt, f, t: round(amt * 0.9, 2))
    user.convert_account_currency("EUR")
    assert user.currency == "EUR"
    updated_tpl = user.get_templates("expense")[0]
    assert updated_tpl["amount"] == 90.0


def test_reset_category(mock_ram_db):
    user = User("Alice")
    removed = user.reset_category("food")
    assert removed["budget_limit"] == 1500.0
    assert removed["expense"] == 650.0
    assert "food" not in user.budget_limits
    assert all(tx["category"] != "food" for tx in user.transactions)


def test_csv_export(tmp_path, mock_ram_db):
    user = User("Alice")
    f = tmp_path / "alice_export.csv"
    user.export_to_csv(str(f), month="2026-08")
    assert os.path.exists(f)

    content = f.read_text(encoding="utf-8")
    assert "Type,ID,Date,Category/Source,Amount,Currency,Note" in content
    assert "Expense" in content
    assert "Income" in content
    assert "Weekly grocery shopping" in content
    assert "July restaurant" not in content  # filtered by August


def test_users_container(mock_ram_db):
    container = Users()
    alice = container.get_user("Alice")
    assert alice.name == "Alice"
    assert "Alice" in get_all_usernames()

    assert container.add_user("Alice") is False
    assert container.get_user("NonExistent") is None

    assert container.delete_user("Alice")
    assert "Alice" not in get_all_usernames()


def test_budget_alerts_warning_threshold(mock_ram_db):
    user = User("Alice")
    # food limit is 1500, currently 650 spent (450 Aug + 200 Jul)
    # Add enough to hit exactly 91% to trigger warning
    user.add_transaction("food", 715.0, note="push to 91%")
    alerts = user.get_budget_alerts()
    food_alerts = [a for a in alerts if a["category"].lower() == "food"]
    assert len(food_alerts) == 1
    assert food_alerts[0]["level"] in ("warning", "danger")
    assert food_alerts[0]["percentage"] >= 90


def test_budget_alerts_danger_threshold(mock_ram_db):
    user = User("Alice")
    # food limit is 1500, push it over 100%
    user.add_transaction("food", 1100.0, note="push over 100%")
    alerts = user.get_budget_alerts()
    food_alerts = [a for a in alerts if a["category"].lower() == "food"]
    assert len(food_alerts) == 1
    assert food_alerts[0]["level"] == "danger"
    assert food_alerts[0]["percentage"] >= 100


def test_budget_alerts_no_alerts_when_under_threshold(mock_ram_db):
    user = User("Alice")
    # food has 650 spent against 1500 limit — well under 90%
    alerts = user.get_budget_alerts()
    food_alerts = [a for a in alerts if a["category"].lower() == "food"]
    assert food_alerts == []


def test_budget_alerts_ignores_categories_without_limit(mock_ram_db):
    user = User("Alice")
    user.add_transaction("entertainment", 9999.0, note="huge entertainment bill")
    alerts = user.get_budget_alerts()
    ent_alerts = [a for a in alerts if a["category"].lower() == "entertainment"]
    assert ent_alerts == []
