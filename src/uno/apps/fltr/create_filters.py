# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from datetime import date, datetime, time
from decimal import Decimal

from uno.apps.val.enums import object_lookups, numeric_lookups, text_lookups
from uno.model.model import UnoModel
from uno.db.base import UnoBase
from uno.apps.fltr.models import Filter
from uno.apps.fltr.enums import FilterType
from uno.utilities import convert_snake_to_all_caps_snake, convert_snake_to_camel
from uno.config import settings


async def create_filters(base: UnoBase) -> None:
    print(f"Filters for {base.__tablename__}")
    source_model = UnoModel.registry[base.__tablename__]
    if source_model.exclude_from_filters:
        return []
    filters = []
    for column_name, column in base.__table__.columns.items():
        if column_name in source_model.filter_excludes:
            continue
        if column.type.python_type in [str, bytes]:
            lookups = text_lookups
        elif column.type.python_type in [int, Decimal, float, date, datetime, time]:
            lookups = numeric_lookups
        else:
            lookups = object_lookups
        filter = Filter(
            source_meta_type_id=base.__tablename__,
            label_string=column_name,
            remote_meta_type_id=base.__tablename__,
            data_type=column.type.python_type.__name__,
            lookups=lookups,
        )
        filters.append(filter)

    for relationship in source_model.relationships():
        if relationship.key in source_model.filter_excludes:
            continue
        filter = Filter(
            source_meta_type_id=base.__tablename__,
            label_string=relationship.key,
            remote_meta_type_id=relationship.mapper.class_.__tablename__,
            data_type="str",
            lookups=object_lookups,
        )
        filters.append(filter)
    return filters
