import pytest
import decimal
from datetime import datetime, timedelta, date
from src.uno import utils

# --- import_from_path ---
def test_import_from_path(tmp_path):
    # Create a dummy module file
    code = "VAR = 42"
    modfile = tmp_path / "dummy.py"
    modfile.write_text(code)
    mod = utils.import_from_path("dummy_mod", str(modfile))
    assert hasattr(mod, "VAR")
    assert mod.VAR == 42

# --- snake_to_title ---
def test_snake_to_title():
    assert utils.snake_to_title("foo_bar_baz") == "Foo Bar Baz"
    assert utils.snake_to_title("") == ""
    assert utils.snake_to_title("single") == "Single"

# --- snake_to_camel ---
def test_snake_to_camel():
    assert utils.snake_to_camel("foo_bar_baz") == "FooBarBaz"
    assert utils.snake_to_camel("") == ""
    assert utils.snake_to_camel("single") == "Single"

# --- snake_to_caps_snake ---
def test_snake_to_caps_snake():
    assert utils.snake_to_caps_snake("foo_bar_baz") == "FOO_BAR_BAZ"
    assert utils.snake_to_caps_snake("") == ""
    assert utils.snake_to_caps_snake("single") == "SINGLE"

# --- boolean_to_string ---
def test_boolean_to_string():
    assert utils.boolean_to_string(True) == "Yes"
    assert utils.boolean_to_string(False) == "No"

# --- date_to_string ---
def test_date_to_string(monkeypatch):
    d = date(2024, 4, 20)
    # Patch babel.dates.format_date
    monkeypatch.setattr(utils.dates, "format_date", lambda d, format, locale: f"{d.isoformat()}|{format}|{locale}")
    assert utils.date_to_string(d) == "2024-04-20|medium|en_US"
    assert utils.date_to_string(None) is None

# --- datetime_to_string ---
def test_datetime_to_string(monkeypatch):
    dt = datetime(2024, 4, 20, 12, 30, 0)
    monkeypatch.setattr(utils.dates, "format_datetime", lambda d, format, locale: f"{d.isoformat()}|{format}|en_US")
    # Patch config.LOCALE if needed
    import types
    utils.config = types.SimpleNamespace(LOCALE="en_US")
    assert utils.datetime_to_string(dt) == "2024-04-20T12:30:00|medium|en_US"
    assert utils.datetime_to_string(None) is None

# --- decimal_to_string ---
def test_decimal_to_string(monkeypatch):
    monkeypatch.setattr(utils.numbers, "format_decimal", lambda d, locale: f"{d}|{locale}")
    assert utils.decimal_to_string(decimal.Decimal("123.45")) == "123.45|en_US"
    assert utils.decimal_to_string(None) is None

# --- obj_to_string ---
def test_obj_to_string():
    class Dummy:
        def __str__(self):
            return "dummy!"
    assert utils.obj_to_string(Dummy()) == "dummy!"
    assert utils.obj_to_string(None) is None

# --- timedelta_to_string ---
def test_timedelta_to_string(monkeypatch):
    td = timedelta(days=2, hours=3)
    monkeypatch.setattr(utils.dates, "format_timedelta", lambda td, locale: f"{td}|{locale}")
    assert utils.timedelta_to_string(td) == f"2 days, 3:00:00|en_US"
    assert utils.timedelta_to_string(None) is None

# --- boolean_to_okui ---
def test_boolean_to_okui():
    assert utils.boolean_to_okui(True) == {"value": True, "type": "boolean", "element": "checkbox", "label": "FIGURE THIS OUT"}
    assert utils.boolean_to_okui(False) == {"value": False, "type": "boolean", "element": "checkbox", "label": "FIGURE THIS OUT"}
    assert utils.boolean_to_okui(None) is None

# --- date_to_okui ---
def test_date_to_okui(monkeypatch):
    d = date(2024, 4, 20)
    monkeypatch.setattr(utils.dates, "format_date", lambda d, format, locale: f"{d.isoformat()}|{format}|{locale}")
    assert utils.date_to_okui(d) == "2024-04-20|medium|en_US"
    assert utils.date_to_okui(None) is None

# --- datetime_to_okui ---
def test_datetime_to_okui(monkeypatch):
    dt = datetime(2024, 4, 20, 12, 30, 0)
    monkeypatch.setattr(utils.dates, "format_datetime", lambda d, format, locale: f"{d.isoformat()}|{format}|en_US")
    assert utils.datetime_to_okui(dt) == "2024-04-20T12:30:00|medium|en_US"
    assert utils.datetime_to_okui(None) is None

# --- decimal_to_okui ---
def test_decimal_to_okui():
    dec = decimal.Decimal("123.45")
    assert utils.decimal_to_okui(dec) == {"value": dec, "type": "decimal", "element": "imput"}
    assert utils.decimal_to_okui(None) is None

# --- obj_to_okui ---
def test_obj_to_okui():
    class Dummy:
        def __str__(self):
            return "dummy!"
    assert utils.obj_to_okui(Dummy()) == "dummy!"
    assert utils.obj_to_okui(None) is None

# --- timedelta_to_okui ---
def test_timedelta_to_okui(monkeypatch):
    td = timedelta(days=2, hours=3)
    # Patch config.LOCALE if needed
    import types
    utils.config = types.SimpleNamespace(LOCALE="en_US")
    monkeypatch.setattr(utils.dates, "format_timedelta", lambda td, locale: f"{td}|{locale}")
    assert utils.timedelta_to_okui(td) == f"2 days, 3:00:00|en_US"
    assert utils.timedelta_to_okui(None) is None
