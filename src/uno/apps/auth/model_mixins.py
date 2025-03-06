# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional

from pydantic import BaseModel


class ModelAuditMixin(BaseModel):

    created_at: Optional[datetime.datetime] = None
    created_by: Optional["User"] = None
    modified_at: Optional[datetime.datetime] = None
    modified_by: Optional["User"] = None
    deleted_at: Optional[datetime.datetime] = None
    deleted_by: Optional["User"] = None
