# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import io
import sys
import contextlib
import importlib

from psycopg.sql import SQL
from sqlalchemy import text
from sqlalchemy.engine import create_engine, Engine

from uno.db.sql.sql_config import SQLConfig
from uno.db.sql.db_sql_emitters import (
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
from uno.api.app_def import app
from uno.db.base import meta_data
from uno.db.db import scoped_session
from uno.pkgs.auth.bases import UserBase
from uno.pkgs.fltr.models import create_filters
from uno.pkgs.meta.sql_configs import MetaTypeSQLConfig
from uno.config import settings

BASES_MODULE_NAME = "bases"
MODELS_MODULE_NAME = "models"
SQL_CONFIGS_MODULE_NAME = "sql_configs"


def import_models(pkg):
    print(pkg)
    name = pkg

    if module_has_submodule(pkg, MODELS_MODULE_NAME):
        models_module_name = "%s.%s" % (name, MODELS_MODULE_NAME)
        models_module = importlib.import_module(models_module_name)


def module_has_submodule(package, module_name):
    """See if 'module' is in 'package'."""
    print(package.__name__)
    print(package.__path__)
    print(module_name)
    try:
        package_name = package.__name__
        package_path = package.__path__
    except AttributeError:
        # package isn't a package.
        return False

    full_module_name = package_name + "." + module_name
    try:
        return importlib.util.find_spec(full_module_name, package_path) is not None
    except ModuleNotFoundError:
        # When module_name is an invalid dotted path, Python raises
        # ModuleNotFoundError.
        return False


def cached_import(module_path, class_name):
    # Check whether module is loaded and fully initialized.
    if not (
        (module := sys.modules.get(module_path))
        and (spec := getattr(module, "__spec__", None))
        and getattr(spec, "_initializing", False) is False
    ):
        module = importlib.import_module(module_path)
    return getattr(module, class_name)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    try:
        return cached_import(module_path, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err


for pkg in settings.LOAD_MODULES_FROM:
    import_models(pkg)
# Import all the bases in the settings.LOAD_MODULES_FROM list
# for pkg in settings.LOAD_MODULES_FROM:
#    globals()[f"{pkg.split('.')[-1]}._bases"] = importlib.import_module(f"{pkg}.bases")
#    globals()[f"{pkg.split('.')[-1]}._models"] = importlib.import_module(
#        f"{pkg}.models"
#    )
#    globals()[f"{pkg.split('.')[-1]}._sql_configs"] = importlib.import_module(
#        f"{pkg}.sql_configs"
#    )


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
