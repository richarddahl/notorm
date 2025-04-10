# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio

from uno.database.manager import DBManager


if __name__ == "__main__":
    db_manager = DBManager()
    asyncio.run(db_manager.create_query_paths())
