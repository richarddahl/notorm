# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio

from uno.dbmanager import DBManager


if __name__ == "__main__":
    db = DBManager()
    db.drop_db()
