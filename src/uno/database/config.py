from pydantic import BaseModel, ConfigDict
from typing import Optional

from uno.settings import uno_settings


class ConnectionConfig(BaseModel):
    """Configuration for database connections."""

    db_role: str = f"{uno_settings.DB_NAME}_login"
    db_name: Optional[str] = uno_settings.DB_NAME
    db_user_pw: Optional[str] = uno_settings.DB_USER_PW
    db_host: Optional[str] = uno_settings.DB_HOST
    db_port: Optional[int] = uno_settings.DB_PORT
    db_driver: Optional[str] = uno_settings.DB_ASYNC_DRIVER
    db_schema: Optional[str] = uno_settings.DB_SCHEMA

    # Connection pooling parameters
    pool_size: Optional[int] = 5
    max_overflow: Optional[int] = 0
    pool_timeout: Optional[int] = 30
    pool_recycle: Optional[int] = 90

    # Additional driver-specific arguments
    connect_args: Optional[dict] = None

    model_config = ConfigDict({"frozen": True})
