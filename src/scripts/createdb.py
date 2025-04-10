# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import logging

from uno.settings import uno_settings
from uno.database.engine import SyncEngineFactory
from uno.database.manager import DBManager
from uno.sql.emitters.database import (
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    SetRole,
)
from uno.sql.emitters.table import InsertMetaRecordFunction
from uno.meta.sqlconfigs import MetaTypeSQLConfig

# Initialize a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize the engine factory with the logger
engine_factory = SyncEngineFactory(logger=logger)

# Define all needed SQL emitters
sql_emitters = {
    "drop_database_and_roles": DropDatabaseAndRoles,
    "create_roles_and_database": CreateRolesAndDatabase,
    "create_schemas_and_extensions": CreateSchemasAndExtensions,
    "revoke_and_grant_privileges": RevokeAndGrantPrivilegesAndSetSearchPaths,
    "set_role": SetRole,
    "create_token_secret": CreateTokenSecret,
    "create_pgulid": CreatePGULID,
    "grant_privileges": GrantPrivileges,
    "insert_meta_record": InsertMetaRecordFunction,
    "meta_type": MetaTypeSQLConfig,
}

# Instantiate DBManager with all required parameters
db_manager = DBManager(
    config=uno_settings,
    logger=logger,
    engine_factory=engine_factory,
    sql_emitters=sql_emitters,
)

# Now you can use db_manager.create_db() or other methods as needed
if __name__ == "__main__":
    # try:
    db_manager.create_db()
    # except Exception as e:
    #    logger.error("An error occurred while creating the database: %s", e)
