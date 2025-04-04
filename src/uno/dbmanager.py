# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import io
import sys
import contextlib

from psycopg import sql
from sqlalchemy import text
from sqlalchemy.engine import create_engine, Engine

from uno.sqlemitter import (
    SQLConfig,
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    InsertMetaRecordFunction,
)
from uno.model import UnoModel
from uno.apidef import app
from uno.db import meta_data, scoped_session
from uno.auth.bases import UserBase
from uno.meta.sqlconfigs import MetaTypeSQLConfig
from uno.filter import UnoFilter
from uno.qry.bases import QueryPathBase
import uno.attr.sqlconfigs
import uno.auth.sqlconfigs
import uno.qry.sqlconfigs
import uno.meta.sqlconfigs
import uno.msg.sqlconfigs
import uno.rprt.sqlconfigs
import uno.val.sqlconfigs

# import uno.wkflw.sqlconfigs
from uno.attr import models
from uno.auth import models
from uno.qry import models
from uno.meta import models

from uno.msg import models

from uno.rprt import models
from uno.val import models

# from uno.wkflw import models

from uno.utilities import import_from_path
from uno.config import settings


if settings.APP_PATH:
    for pkg in settings.LOAD_PACKAGES:
        file_path = f"{settings.APP_PATH}/{pkg.replace('.', '/')}/models.py"
        import_from_path(pkg, file_path)
        file_path = f"{settings.APP_PATH}/{pkg.replace('.', '/')}/sqlconfigs.py"
        import_from_path(pkg, file_path)


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
        # Connect to the new database to emit the table specific sql.SQL
        engine = self.engine(db_role=f"{settings.DB_NAME}_login")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Must emit the sql for the meta_record type table first
            # So that the triggger function can be fired each time
            # a new table is created to add the corresponding permissions
            print("\nEmitting sql.SQL for: MetaType")
            MetaTypeSQLConfig.emit_sql(connection=conn)
            for name, config in SQLConfig.registry.items():
                if name == "MetaTypeSQLConfig":
                    continue  # Skip the MetaType since it is done
                print(f"\nEmitting sql.SQL for: {name}")
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

    async def create_superuser(
        self,
        email: str = settings.SUPERUSER_EMAIL,
        handle: str = settings.SUPERUSER_HANDLE,
        full_name: str = settings.SUPERUSER_FULL_NAME,
    ) -> str:
        """
        Creates a superuser with the specified email, handle, and full name.

        This method initializes a superuser instance and saves it to the database
        with elevated privileges. The database role is temporarily elevated to
        the admin role during the operation.

        Args:
            email (str): The email address of the superuser. Defaults to the value
                of `settings.SUPERUSER_EMAIL`.
            handle (str): The unique handle/username for the superuser. Defaults to
                the value of `settings.SUPERUSER_HANDLE`.
            full_name (str): The full name of the superuser. Defaults to the value
                of `settings.SUPERUSER_FULL_NAME`.

        Returns:
            str: The handle of the created superuser.

        Raises:
            Exception: If an error occurs during the creation of the superuser,
                it is caught and logged, and the exception is raised.
        """
        user = UserBase(
            email=email,
            handle=handle,
            full_name=full_name,
            is_superuser=True,
        )
        try:
            async with scoped_session() as session:
                await session.execute(
                    text(
                        sql.SQL("SET ROLE {db_name}_admin;")
                        .format(
                            db_name=sql.SQL(settings.DB_NAME),
                        )
                        .as_string()
                    )
                )
                session.add(user)
                await session.commit()
            await session.close()
            print(f"Superuser created: {user.handle} with email: {user.email}")
            return user.handle
        except Exception as e:
            print(f"Error creating superuser: {e}")

    async def create_query_paths(self) -> None:

        def create_query_path(
            filter: UnoFilter, parent: UnoFilter = None
        ) -> QueryPathBase:
            print(
                f"Creating query path for filter: {filter.label} with parent: {parent.label if parent else None}"
            )
            source_meta_type = (
                parent.source_meta_type_id if parent else filter.source_meta_type_id
            )
            return QueryPathBase(
                source_meta_type_id=source_meta_type,
                destination_meta_type_id=filter.target_meta_type_id,
                path=filter.path(parent=parent),
                data_type=filter.data_type,
            )

        query_paths = []
        for model in UnoModel.registry.values():
            model.configure(app)
            for fltr in model.filters.values():
                query_paths.append(create_query_path(fltr))
                if fltr.source_meta_type_id != fltr.target_meta_type_id:
                    child_model = UnoModel.registry[fltr.target_meta_type_id]
                    child_model.configure(app)
                    for child_fltr in fltr.children(model=child_model):
                        query_paths.append(
                            create_query_path(
                                child_fltr,
                                parent=fltr,
                            )
                        )

        async with scoped_session() as session:
            await session.execute(
                text(
                    sql.SQL("SET ROLE {db_name}_admin;")
                    .format(
                        db_name=sql.SQL(settings.DB_NAME),
                    )
                    .as_string()
                )
            )
            session.add_all(query_paths)
            await session.commit()
        await session.close()
