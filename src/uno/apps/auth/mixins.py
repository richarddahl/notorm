# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from pydantic import BaseModel

from uno.config import settings


class RecordAuditMixin(BaseModel):
    created_by_id: Optional[str] = None
    created_by: Optional["User"] = None
    modified_by_id: Optional[str] = None
    modified_by: Optional["User"] = None
    deleted_by_id: Optional[str] = None
    deleted_by: Optional["User"] = None
