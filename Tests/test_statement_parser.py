from core.expense_tracker import StatementParser


QIF_SAMPLE = """\
!Type:Bank
D08/01/2026
T-45.50
PSupermarket
LFood
^
D07/15/2026
T2000.00
PSalary
LIncome
^
D01/01/9999
T-99.00
PFuture charge
LMiscellaneous
^
"""

OFX_SAMPLE = """\
<OFX>
<STMTTRNRS>
<STMTTRN>
<DTPOSTED>20260802
<TRNAMT>-120.00
<NAME>Landlord
<MEMO>Rent payment
</STMTTRN>
<STMTTRN>
<DTPOSTED>20260803
<TRNAMT>500.00
<NAME>Client ABC
<MEMO>Freelance invoice
</STMTTRN>
<STMTTRN>
<DTPOSTED>99990101
<TRNAMT>-50.00
<NAME>Future transaction
</STMTTRN>
</STMTTRNRS>
</OFX>
"""


def test_qif_parses_expense_and_income():
    txs = StatementParser.parse_qif(QIF_SAMPLE)
    # Future date record must be excluded (9999-01-01 > today)
    amounts = [t["amount"] for t in txs]
    assert -45.50 in amounts
    assert 2000.00 in amounts
    assert -99.00 not in amounts


def test_qif_dates_are_strings():
    txs = StatementParser.parse_qif(QIF_SAMPLE)
    for t in txs:
        assert isinstance(t["date"], str)
        assert len(t["date"]) == 10  # YYYY-MM-DD


def test_ofx_parses_expense_and_income():
    txs = StatementParser.parse_ofx(OFX_SAMPLE)
    amounts = [t["amount"] for t in txs]
    assert -120.00 in amounts
    assert 500.00 in amounts
    # Future date (9999) must be excluded
    assert not any(a == -50.00 for a in amounts)


def test_ofx_payee_name():
    txs = StatementParser.parse_ofx(OFX_SAMPLE)
    names = [t["payee"] for t in txs]
    assert any("Landlord" in n for n in names)


def test_parse_file_detects_qif(tmp_path):
    f = tmp_path / "stmt.qif"
    f.write_text(QIF_SAMPLE)
    txs = StatementParser.parse_file(str(f))
    assert len(txs) >= 1


def test_parse_file_detects_ofx(tmp_path):
    f = tmp_path / "stmt.ofx"
    f.write_text(OFX_SAMPLE)
    txs = StatementParser.parse_file(str(f))
    assert len(txs) >= 1


def test_empty_qif_returns_empty():
    assert StatementParser.parse_qif("") == []


def test_qif_missing_amount_skipped():
    content = "!Type:Bank\nDPPayee only\n^\n"
    txs = StatementParser.parse_qif(content)
    assert txs == []


def test_payee_rules_memory(tmp_path, monkeypatch):
    import json
    from core.user import User
    f = tmp_path / "test_rules_db.json"
    with open(f, "w", encoding="utf-8") as fp:
        json.dump({"users": {}}, fp)
    monkeypatch.setattr("core.data_manager.DATABASE_FILE", str(f))

    u = User("RulesUser")
    assert u.get_payee_category("Netflix") is None

    u.learn_payee_category("Netflix", "entertainment")
    assert u.get_payee_category("netflix") == "entertainment"
    assert u.get_payee_category("Netflix") == "entertainment"

    # Invalid category is ignored
    u.learn_payee_category("SomePayee", "NonExistentCategory")
    assert u.get_payee_category("SomePayee") is None

