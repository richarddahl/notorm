# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from uno.model import UnoModel, PostgresTypes


class MetaTypeModel(UnoModel):
    __tablename__ = "meta_type"

    id: Mapped[PostgresTypes.String63] = mapped_column(
        primary_key=True,
        index=True,
        nullable=False,
        doc="The name of the table",
    )


class MetaRecordModel(UnoModel):
    __tablename__ = "meta_record"

    id: Mapped[PostgresTypes.String26] = mapped_column(
        primary_key=True,
        nullable=False,
        unique=True,
        index=True,
        doc="Primary Key",
    )
    meta_type_id: Mapped[PostgresTypes.String63] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "META_TYPE", "reverse_edge": "OBJECTS"},
        doc="The type of record",
    )
    meta_type = relationship("MetaTypeModel")
