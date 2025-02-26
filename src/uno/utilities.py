# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations
from typing import Any
import decimal
from datetime import datetime, timedelta, date

from babel import dates, numbers  # type: ignore

from uno.config import settings  # type: ignore


def convert_snake_to_capital_word(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0].title() + "".join(x.title() for x in components[1:])


def convert_snake_to_title(snake_str: str) -> str:
    components = snake_str.split("_")
    return " ".join(x.title() for x in components)


def convert_snake_to_camel(snake_str: str) -> str:
    """
    Convert a snake_case string to a CamelCase label.

    This function takes a string in snake_case format (words separated by underscores)
    and converts it to a CamelCase format by capitalizing the first letter of each word
    and removing the underscores.

    Args:
        snake_str (str): The input string in snake_case format.

    Returns:
        str: The converted string in CamelCase format.

    Examples:
        >>> convert_snake_to_camel("hello_world")
        'HelloWorld'
        >>> convert_snake_to_camel("user_first_name")
        'UserFirstName'
    """
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


# Mask functions
def boolean_to_string(boolean: bool) -> str:
    return "Yes" if boolean is True else "No"


def date_to_string(date: date | None) -> str | None:
    return dates.format_date(date, format="medium", locale="en_US") if date else None


def datetime_to_string(datetime: datetime | None) -> str | None:
    return (
        dates.format_datetime(datetime, format="medium", locale=settings.LOCALE)
        if datetime
        else None
    )


def decimal_to_string(dec: decimal.Decimal | None) -> str | None:
    return numbers.format_decimal(dec, locale="en_US") if dec else None


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


def decimal_to_okui(dec: decimal.Decimal | None) -> dict[str, Any] | None:
    return {"value": dec, "type": "decimal", "element": "imput"} if dec else None


def obj_to_okui(model: Any) -> str | None:
    return model.__str__() if model else None


def timedelta_to_okui(time_delta: timedelta | None) -> str | None:
    return (
        dates.format_timedelta(time_delta, locale=settings.LOCALE)
        if time_delta
        else None
    )
