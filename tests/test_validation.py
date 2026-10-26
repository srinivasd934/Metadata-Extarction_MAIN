from app.validation import valid_date, normalize_value, normalize_notice


def test_invalid_dates():
    assert valid_date("05.12.2008") == "05.12.2008"
    assert valid_date("31.11.2009") is None
    assert valid_date("31.04.2011") is None
    assert valid_date("31.02.2011") is None


def test_value():
    assert normalize_value("4000") == "4000"


def test_notice():
    assert normalize_notice("90") == "90"
    assert normalize_notice("90.0") == "90"
