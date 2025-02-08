# uno/db/sql_emitters.py

The management.db_manager_sql.py file contains the following SQL Constants used by the DBManager to configure the database instance.


__NOTE__ - The use of f strings to provide the schema name and database name DOES NOT provide any protection against SQL injection. 

You cannot paramaterize postgres DDL statements.

The names are defined in the .env file or are derived from the mapped classes.
They are not user input, and are only used to create or update the db during developement, testing, and deployment.

__DON'T ALLOW UNTRUSTED USERS TO EDIT THE .env FILEs!__

## ::: uno.db.management.db_manager_sql.CONFIGURE_AGE_EXTENSION

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CONFIGURE_ROLE_SCHEMA_PRIVILEGES

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CONFIGURE_ROLE_TABLE_PRIVILEGES

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_AUTHORIZE_USER_FUNCTION

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_CAN_INSERT_GROUP_FUNCTION

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_DATABASE

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_EXTENSIONS

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_GET_PERMISSIBLE_TABLEPERMISSIONS_FUNCTION

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_INSERT_GROUP_CONSTRAINT

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_INSERT_GROUP_FOR_TENANT_FUNCTION_AND_TRIGGER

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_INSERT_RELATED_OBJECT_FUNCTION

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_INSERT_TABLEPERMISSION_FUNCTION_AND_TRIGGER

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_PGULID

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_ROLES

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_SCHEMAS

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_SET_OWNER_AND_MODIFIED_FUNCTION

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_TOKEN_SECRET

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_TOKEN_SECRET_TABLE

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_USER_TABLE_RLS_SELECT_POLICY

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.CREATE_VALIDATE_DELETE_FUNCTION

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.DROP_DATABASE

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.DROP_ROLES

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: tru

## ::: uno.db.management.db_manager_sql.REVOKE_ACCESS

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.SET_PGMETA_CONFIG

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true

## ::: uno.db.management.db_manager_sql.SET_SEARCH_PATHS

    handler: python
    options:
      show_root_heading: true
      show_source: true
      separate_signature: true
