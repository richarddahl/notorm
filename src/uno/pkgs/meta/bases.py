# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from uno.db.base import UnoBase, str_63, str_26
from uno.config import settings


class MetaTypeBase(UnoBase):
    __tablename__ = "meta_type"

    id: Mapped[str_63] = mapped_column(
        primary_key=True,
        index=True,
        nullable=False,
        doc="The name of the table",
    )


class MetaBase(UnoBase):
    __tablename__ = "meta"

    id: Mapped[str_26] = mapped_column(
        primary_key=True,
        nullable=False,
        unique=True,
        index=True,
        doc="Primary Key",
    )
    meta_type_id: Mapped[str_63] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "META_TYPE", "reverse_edge": "OBJECTS"},
        doc="The type of record",
    )
    meta_type = relationship("MetaTypeBase")
