from app import format_currency, get_quarter_info


def test_format_currency_with_number():
    assert format_currency(1234.5) == "1.234,50"


def test_format_currency_with_br_string():
    assert format_currency("R$ 1.234,56") == "1.234,56"


def test_format_currency_with_invalid_value_returns_zero():
    assert format_currency("abc") == "0,00"


def test_get_quarter_info_structure():
    info = get_quarter_info()

    assert set(info.keys()) == {"quarter", "month_name", "year"}
    assert info["quarter"] in {1, 2, 3, 4}
    assert isinstance(info["year"], int)
    assert isinstance(info["month_name"], str)
