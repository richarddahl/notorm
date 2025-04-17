"""
Base declarative class for SQLAlchemy ORM models.
"""
from sqlalchemy.orm import declarative_base

# Base class for all ORM models in client applications
Base = declarative_base()