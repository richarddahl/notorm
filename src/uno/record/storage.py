# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import ClassVar, Optional
from pydantic import BaseModel
from sqlalchemy.engine import Connection

from uno.errors import UnoRegistryError

from uno.config import settings


class UnoStorage(BaseModel):
    registry: ClassVar[dict[str, "UnoStorage"]] = {}
    table_name: Optional[str] = None
    sql_emitters: list[BaseModel] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # sql_emitters = []
        # for kls in cls.mro():
        #    if hasattr(kls, "sql_emitters"):
        #        for sql_emitter in kls.sql_emitters:
        #            if sql_emitter not in sql_emitters:
        #                sql_emitters.append(sql_emitter)
        # cls.sql_emitters = sql_emitters

        if cls.__name__ not in cls.registry:
            cls.registry.update({cls.__name__: cls})
        else:
            # Raise an error if a class with the same table name already exists in the registry
            raise UnoRegistryError(
                f"A Storage class with the table name {cls.__name__} already exists in the registry.",
                "CLASS_NAME_EXISTS_IN_REGISTRY",
            )

    def emit_sql(self) -> None:
        return [sql_emitter for sql_emitter in self.sql_emitters]
