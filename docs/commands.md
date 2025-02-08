# uno/db/cmd

The uno/db/cmd folder contains the following:

## create_db.py

```python
from uno.db.management.db_tool import DBManager


if __name__ == "__main__":
    db = DBManager()
    db.drop_db()
    db.create_db()
```

## drop_db.py

```python
from uno.db.management.db_tool import DBManager


if __name__ == "__main__":
    db = DBManager()
    db.drop_db()
```
