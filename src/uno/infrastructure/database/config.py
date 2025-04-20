from pydantic import BaseModel, ConfigDict
from typing import Optional

from uno.settings import uno_settings


class ConnectionConfig(BaseModel):
    """Configuration for database connections."""

    db_role: str = uno_settings.DB_USER  # Use DB_USER by default
    db_name: str | None = uno_settings.DB_NAME
    db_user_pw: str | None = uno_settings.DB_USER_PW
    db_host: str | None = uno_settings.DB_HOST
    db_port: Optional[int] = uno_settings.DB_PORT
    db_driver: str | None = uno_settings.DB_ASYNC_DRIVER
    db_schema: str | None = uno_settings.DB_SCHEMA

    # Connection pooling parameters
    pool_size: Optional[int] = 5
    max_overflow: Optional[int] = 0
    pool_timeout: Optional[int] = 30
    pool_recycle: Optional[int] = 90

    # Additional driver-specific arguments
    connect_args: Optional[dict] = None

    model_config = ConfigDict(frozen=True)

    def get_uri(self) -> str:
        """
        Construct a SQLAlchemy database URI from connection config.

        Returns:
            str: SQLAlchemy connection URI string
        """
        import urllib.parse

        # Determine driver to use - strip any 'postgresql+' prefix to avoid duplication
        driver = self.db_driver
        if driver.startswith("postgresql+"):
            driver = driver.replace("postgresql+", "")

        # URL encode the password to handle special characters like %
        encoded_pw = urllib.parse.quote_plus(self.db_user_pw)

        # Build the connection string
        if "psycopg" in driver or "postgresql" in driver:
            # PostgreSQL URI format
            uri = f"postgresql+{driver}://{self.db_role}:{encoded_pw}@{self.db_host}:{self.db_port}/{self.db_name}"
            return uri
        else:
            # Generic SQLAlchemy URI format
            uri = f"{driver}://{self.db_role}:{encoded_pw}@{self.db_host}:{self.db_port}/{self.db_name}"
            return uri
