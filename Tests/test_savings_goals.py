import pytest
from core.user import User
from core.exceptions import InvalidAmountError


@pytest.fixture
def user_with_clean_db(tmp_path, monkeypatch):
    import json
    f = tmp_path / "test_db.json"
    with open(f, "w", encoding="utf-8") as fp:
        json.dump({"users": {}}, fp)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(f))
    return User("TestUser")


def test_add_savings_goal(user_with_clean_db):
    u = user_with_clean_db
    goal = u.add_savings_goal("Vacation", 1500.0, current_amount=300.0, target_date="2026-12-31")
    assert goal["name"] == "Vacation"
    assert goal["target"] == 1500.0
    assert goal["current"] == 300.0
    assert goal["target_date"] == "2026-12-31"
    assert len(u.get_savings_goals()) == 1


def test_add_savings_goal_validations(user_with_clean_db):
    u = user_with_clean_db
    with pytest.raises(ValueError, match="blank"):
        u.add_savings_goal("", 1000.0)
    with pytest.raises(InvalidAmountError, match="greater than zero"):
        u.add_savings_goal("House", 0)
    with pytest.raises(InvalidAmountError, match="greater than zero"):
        u.add_savings_goal("House", -50)
    with pytest.raises(InvalidAmountError, match="valid number"):
        u.add_savings_goal("House", "invalid_num")


def test_deposit_and_withdraw_savings_goal(user_with_clean_db):
    u = user_with_clean_db
    goal = u.add_savings_goal("Car", 5000.0, current_amount=1000.0)
    gid = goal["id"]

    updated = u.deposit_savings_goal(gid, 500.0)
    assert updated["current"] == 1500.0

    with pytest.raises(InvalidAmountError, match="greater than zero"):
        u.deposit_savings_goal(gid, 0)
    with pytest.raises(InvalidAmountError, match="greater than zero"):
        u.deposit_savings_goal(gid, -100)

    updated2 = u.withdraw_savings_goal(gid, 200.0)
    assert updated2["current"] == 1300.0

    with pytest.raises(InvalidAmountError, match="Maximum available balance is"):
        u.withdraw_savings_goal(gid, 5000.0)


def test_update_and_delete_savings_goal(user_with_clean_db):
    u = user_with_clean_db
    goal = u.add_savings_goal("Emergency Fund", 3000.0)
    gid = goal["id"]

    u.update_savings_goal(gid, name="Rainy Day Fund", target_amount=4000.0, target_date="2027-01-01")
    goals = u.get_savings_goals()
    assert goals[0]["name"] == "Rainy Day Fund"
    assert goals[0]["target"] == 4000.0
    assert goals[0]["target_date"] == "2027-01-01"

    deleted = u.delete_savings_goal(gid)
    assert deleted is True
    assert len(u.get_savings_goals()) == 0


def test_savings_goals_currency_conversion(user_with_clean_db, monkeypatch):
    u = user_with_clean_db
    goal = u.add_savings_goal("Laptop", 1000.0, current_amount=500.0)
    gid = goal["id"]

    monkeypatch.setattr("core.currency_service.currency_service.convert", lambda amt, f, t: round(amt * 0.9, 2))
    u.convert_account_currency("EUR")
    assert u.currency == "EUR"
    g = u.get_savings_goals()[0]
    assert g["target"] == 900.0
    assert g["current"] == 450.0


def test_withdraw_zero_balance_goal_rejected(user_with_clean_db):
    u = user_with_clean_db
    goal = u.add_savings_goal("ZeroGoal", 1000.0, current_amount=0.0)
    with pytest.raises(InvalidAmountError, match="No funds available"):
        u.withdraw_savings_goal(goal["id"], 50.0)


def test_add_goal_rejects_negative_current_amount(user_with_clean_db):
    u = user_with_clean_db
    with pytest.raises(InvalidAmountError, match="cannot be negative"):
        u.add_savings_goal("NegativeCurrent", 1000.0, current_amount=-100.0)

