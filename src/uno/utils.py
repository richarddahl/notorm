# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import sys
import importlib
import decimal

from typing import Any
from datetime import datetime, timedelta, date
from babel import dates, numbers

from uno.settings import uno_settings


def import_from_path(module_name, file_path):
    """Import a module given its name and file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def snake_to_title(snake_str: str) -> str:
    components = snake_str.split("_")
    return " ".join(x.title() for x in components)


def snake_to_camel(snake_str: str) -> str:
    """Converts a snake_case string to a camelCase string."""
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def snake_to_caps_snake(snake_str: str) -> str:
    """Converts a snake_case string to an ALL_CAPS_SNAKE string.

    Used by graph data base to convert a snake_case string to
    an ALL_CAPS_SNAKE string for a Edge label.

    """
    components = snake_str.split("_")
    return "_".join(x.upper() for x in components)


# Mask functions
def boolean_to_string(boolean: bool) -> str:
    return "Yes" if boolean is True else "No"


def date_to_string(date: date | None) -> str | None:
    return dates.format_date(date, format="medium", locale="en_US") if date else None


def datetime_to_string(datetime: datetime | None) -> str | None:
    return (
        dates.format_datetime(datetime, format="medium", locale=config.LOCALE)
        if datetime
        else None
    )


def decimal_to_string(decimal: decimal.Decimal | None) -> str | None:
    return numbers.format_decimal(decimal, locale="en_US") if decimal else None


def obj_to_string(model: Any) -> str | None:
    return model.__str__() if model else None


def timedelta_to_string(time_delta: timedelta | None) -> str | None:
    return dates.format_timedelta(time_delta, locale="en_US") if time_delta else None


def boolean_to_okui(boolean: bool) -> dict[str, Any] | None:
    if boolean is None:
        return None
    return {
        "value": boolean,
        "type": "boolean",
        "element": "checkbox",
        "label": "FIGURE THIS OUT",
    }


def date_to_okui(date: date | None) -> str | None:
    return dates.format_date(date, format="medium", locale="en_US") if date else None


def datetime_to_okui(datetime: datetime | None) -> str | None:
    return (
        dates.format_datetime(datetime, format="medium", locale="en_US")
        if datetime
        else None
    )


def decimal_to_okui(decimal: decimal.Decimal | None) -> dict[str, Any] | None:
    return (
        {"value": decimal, "type": "decimal", "element": "imput"} if decimal else None
    )


def obj_to_okui(model: Any) -> str | None:
    return model.__str__() if model else None


def timedelta_to_okui(time_delta: timedelta | None) -> str | None:
    return (
        dates.format_timedelta(time_delta, locale=config.LOCALE) if time_delta else None
    )
