# File Structure and Code Style

## File Structure

uno has (what I think is) a typical python library "src" structure

    uno
    | docs
    | src
      | uno
    | Tests

### App Modules

App modules generally contain the following files:

- objects.py: Contains the UnoObjs for the entities
- models.py:  Contains the sqlalchemy DeclarativeBase models for the entities
- sqlconfigs.py Contains the configuration of custom SQL executed for the entities

## Code Style
