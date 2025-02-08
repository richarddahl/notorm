# File Structure and Code Style

## File Structure

uno has (what I think is) a typical python library "src" structure

    uno
    | docs
    | src
      | uno
        | attr
        | auth
        | cmd
        | db
        | fltr
        | msg
        | rltd
        | rprt
        | wkflw
    | Tests

### App Modules

Each module within uno that provides database tables and associated functionailty is considered an app module.

App modules generally contain the following files:

- enums.py: Contains enums used as values in the database
- models.py: Contains the UN0Schema objects for the database tables
- tables.py:  Contains the sqlalchemy DeclarativeBase tables

## Code Style
