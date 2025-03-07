# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import ForeignKey, Identity
from sqlalchemy.orm import relationship, Mapped, mapped_column

from uno.record.record import UnoRecord, str_63, str_26
from uno.config import settings


class MetaTypeRecord(UnoRecord):
    __tablename__ = "meta_type"
    id: Mapped[int] = mapped_column(
        Identity(start=1, cycle=True),
        primary_key=True,
        index=True,
        nullable=False,
        doc="Primary Key",
    )
    name: Mapped[str_63] = mapped_column(
        nullable=False,
        doc="The name of the table",
    )


class MetaRecord(UnoRecord):
    __tablename__ = "meta"
    id: Mapped[str_26] = mapped_column(
        primary_key=True,
        nullable=False,
        unique=True,
        index=True,
        doc="Primary Key",
    )
    meta_type_id = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meta_type = relationship("MetaTypeRecord")


"""
class MetaTypeRecord(UnoRecord):
    table_def = UnoTableDef(
        table_name="meta_type",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                VARCHAR(63),
                primary_key=True,
                unique=True,
                index=True,
                nullable=False,
            ),
        ],
    )


class MetaRecord(UnoRecord):
    table_def = UnoTableDef(
        table_name="meta_record",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                VARCHAR(26),
                primary_key=True,
                nullable=False,
                unique=True,
                index=True,
            ),
            Column(
                "meta_type_id",
                ForeignKey("meta_type.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
        ],
    )
"""
