# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from pydantic import BaseModel

from uno.config import settings


class GeneralModelMixin(BaseModel):
    """Mixin for General Objects"""

    is_active: Optional[bool] = True
    is_deleted: Optional[bool] = False
