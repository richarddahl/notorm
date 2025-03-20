# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from datetime import date, datetime, time
from decimal import Decimal

from uno.apps.val.enums import object_lookups, numeric_lookups, text_lookups
from uno.model.model import UnoModel
from uno.db.base import UnoBase
from uno.apps.fltr.filter import Filter
from uno.utilities import convert_snake_to_all_caps_snake, convert_snake_to_camel
from uno.config import settings


def create_filters(base: UnoBase, parent: Filter = None) -> None:
    if not parent:
        print("")
        print(f"Filters for {base.__tablename__}")
    source_model = (
        UnoModel.registry[base.__tablename__]
        if not parent
        else UnoModel.registry[parent.remote_node.lower()]
    )
    if source_model.exclude_from_filters or parent and source_model.terminate_filters:
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
        remote_model = UnoModel.registry[base.__tablename__]
        filter = Filter(
            source_node=convert_snake_to_camel(base.__tablename__),
            label=convert_snake_to_all_caps_snake(column_name),
            remote_node=convert_snake_to_camel(column_name),
            data_type=column.type.python_type.__name__,
            filter_type="Column",
            lookups=lookups,
            parent=parent,
        )
        filters.append(filter)
        print(filter.path)

    for relationship in source_model.relationships():
        remote_model = UnoModel.registry[relationship.mapper.class_.__tablename__]
        if (
            remote_model.exclude_from_filters
            or parent
            and source_model.terminate_filters
        ):
            continue
        if relationship.key in source_model.filter_excludes:
            continue
        if relationship.key in source_model.terminate_field_filters and parent:
            continue
        label = convert_snake_to_all_caps_snake(relationship.key)
        source_model = UnoModel.registry[list(relationship.local_columns)[0].table.name]
        filter = Filter(
            source_node=convert_snake_to_camel(base.__tablename__),
            label=label,
            remote_node=convert_snake_to_camel(
                relationship.mapper.class_.__tablename__
            ),
            data_type="str",
            filter_type="Relationship",
            lookups=object_lookups,
            parent=parent,
        )
        print(filter.path)
        filters.extend(create_filters(remote_model.base, parent=filter))
    return filters
