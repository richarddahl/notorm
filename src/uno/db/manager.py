# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import io
import sys
import contextlib

from psycopg.sql import SQL
from sqlalchemy import text
from sqlalchemy.engine import create_engine, Engine

from uno.db.sql.sqlconfig import SQLConfig
from uno.db.sql.dbsql import (
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    InsertMetaRecordFunction,
)
from uno.model.model import UnoModel
from uno.api.appdef import app
from uno.db.base import meta_data
from uno.db.db import scoped_session
from uno.pkgs.auth.bases import UserBase
from uno.pkgs.fltr.models import create_filters
from uno.pkgs.meta.sqlconfigs import MetaTypeSQLConfig
import uno.pkgs.attr.sqlconfigs as attr_sqlconfigs
import uno.pkgs.auth.sqlconfigs as auth_sqlconfigs
import uno.pkgs.fltr.sqlconfigs as fltr_sqlconfigs
import uno.pkgs.meta.sqlconfigs as meta_sqlconfigs

# import uno.pkgs.msg.sqlconfigs as msg_sqlconfigs
# import uno.pkgs.rprt.sqlconfigs as rpt_sqlconfigs
# import uno.pkgs.val.sqlconfigs as val_sqlconfigs
# import uno.pkgs.wkflw.sqlconfigs as wkflw_sqlconfigs

from uno.utilities import import_from_path
from uno.config import settings

if settings.APP_PATH:
    for pkg in settings.LOAD_PACKAGES:
        file_path = f"{settings.APP_PATH}/{pkg.replace('.', '/')}/sqlconfigs.py"
        mod_obj = import_from_path(pkg, file_path)


@contextlib.contextmanager
def no_stdout():
    save_stdout = sys.stdout
    sys.stdout = io.StringIO()
    yield
    sys.stdout = save_stdout


class DBManager:
    def create_db(self) -> None:
        # Redirect the stdout stream to a StringIO object when running tests
        # to prevent the print statements from being displayed in the test output.
        if settings.ENV == "test":
            with no_stdout():
                self.create_db_()
        else:
            self.create_db_()

    def create_db_(self) -> None:
        self.drop_db()
        self.create_roles_and_database()
        self.create_schemas_and_extensions()
        self.set_privileges_and_paths()
        self.create_functions_triggers_and_tables()
        self.emit_table_sql()
        print(f"Database created: {settings.DB_NAME}\n")

    def create_roles_and_database(self) -> None:
        engine = self.engine(
            db_role="postgres",
            db_password="postgreSQLR0ck%",
            db_name="postgres",
        )
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateRolesAndDatabase().emit_sql(connection=conn)
            print("Created the roles and the database\n")
            conn.close()
        engine.dispose()

    def create_schemas_and_extensions(self) -> None:
        engine = self.engine(db_role="postgres")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateSchemasAndExtensions().emit_sql(connection=conn)
            print("Created the schemas and extensions\n")
            conn.close()
        engine.dispose()

    def set_privileges_and_paths(self) -> None:
        engine = self.engine(db_role="postgres")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            RevokeAndGrantPrivilegesAndSetSearchPaths().emit_sql(connection=conn)
            print("Configured the privileges set the search paths\n")
            conn.close()
        engine.dispose()

    def create_functions_triggers_and_tables(self) -> None:
        engine = self.engine(db_role=f"{settings.DB_NAME}_login")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateTokenSecret().emit_sql(connection=conn)
            print("Created the token_secret table\n")

            CreatePGULID().emit_sql(connection=conn)
            print("Created the pgulid function\n")

            self.create_tables_functions_and_privileges(conn)
            conn.close()
        engine.dispose()

    def create_tables_functions_and_privileges(self, conn) -> None:
        meta_data.create_all(bind=conn)
        print("Created the database tables\n")

        GrantPrivileges().emit_sql(connection=conn)
        print("Set the table privileges\n")

        InsertMetaRecordFunction().emit_sql(connection=conn)
        print("Created the insert_meta function\n")

    def emit_table_sql(self) -> None:
        # Connect to the new database to emit the table specific SQL
        engine = self.engine(db_role=f"{settings.DB_NAME}_login")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Must emit the sql for the meta type table first
            # So that the triggger function can be fired each time
            # a new table is created to add the corresponding permissions
            print("\nEmitting SQL for: MetaType")
            MetaTypeSQLConfig.emit_sql(connection=conn)
            for name, config in SQLConfig.registry.items():
                if name == "MetaTypeSQLConfig":
                    continue  # Skip the MetaType since it is done
                print(f"\nEmitting SQL for: {name}")
                config.emit_sql(connection=conn)
            conn.close()
        engine.dispose()

    def drop_db(self) -> None:
        # Redirect the stdout stream to a StringIO object when running tests
        # to prevent the print statements from being displayed in the test output.

        if settings.ENV == "test":
            with no_stdout():
                self.drop_db_()
        else:
            self.drop_db_()

    def drop_db_(self) -> None:
        # Connect to the postgres database as the postgres user
        engine = self.engine(db_role="postgres", db_name="postgres")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print(
                f"\nDropping the db: {settings.DB_NAME} and all the roles for the application\n"
            )
            # Drop the Database
            DropDatabaseAndRoles().emit_sql(connection=conn)
            print("Dropped the database and the roles associated with it\n")
        engine.dispose()

    async def create_superuser(
        self,
        email: str = settings.SUPERUSER_EMAIL,
        handle: str = settings.SUPERUSER_HANDLE,
        full_name: str = settings.SUPERUSER_FULL_NAME,
    ) -> str:
        user = UserBase(
            email=email,
            handle=handle,
            full_name=full_name,
            is_superuser=True,
        )
        async with scoped_session() as session:
            await session.execute(
                text(
                    SQL("SET ROLE {db_name}_admin;")
                    .format(
                        db_name=SQL(settings.DB_NAME),
                    )
                    .as_string()
                )
            )
            session.add(user)
            await session.commit()
            await session.close()
        return user

    async def create_filters(self) -> None:
        filters = {}
        for model in UnoModel.registry.values():
            model.configure(app)
            for fltr in create_filters(model.base.__table__):
                if fltr.__str__() not in filters:
                    filters.update({fltr.__str__(): fltr.edit_data()})

        async with scoped_session() as session:
            await session.execute(
                text(
                    SQL("SET ROLE {db_name}_admin;")
                    .format(
                        db_name=SQL(settings.DB_NAME),
                    )
                    .as_string()
                )
            )
            session.add_all(filters.values())
            await session.commit()
            await session.close()

    def engine(
        self,
        db_role: str,
        db_driver: str = settings.DB_SYNC_DRIVER,
        db_password: str = settings.DB_USER_PW,
        db_host: str = settings.DB_HOST,
        db_name: str = settings.DB_NAME,
    ) -> Engine:

        engine = create_engine(
            f"{db_driver}://{db_role}:{db_password}@{db_host}/{db_name}",
        )
        return engine
