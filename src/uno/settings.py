# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import os

from typing import Type
from os.path import abspath, dirname

from pydantic_settings import BaseSettings, SecretsSettingsSource, SettingsConfigDict


class General(BaseSettings):
    # GENERAL SETTINGS
    UNO_ROOT: str = dirname(dirname(abspath(__file__)))
    SITE_NAME: str
    DEBUG: bool = True
    LOCALE: str = "en_US"
    ENV: str = "prod"
    API_VERSION: str = "v1.0"

    # DATABASE SETTINGS
    DB_USER: str = "postgres"  # Default to postgres, override in env files
    DB_USER_PW: str = ""
    DB_HOST: str
    DB_PORT: int
    DB_SCHEMA: str
    DB_NAME: str
    DB_SYNC_DRIVER: str
    DB_ASYNC_DRIVER: str

    # DATABASE QUERY SETTINGS
    DEFAULT_LIMIT: int = 100
    DEFAULT_OFFSET: int = 0
    DEFAULT_PAGE_SIZE: int = 25

    # SECURITY SETTINGS
    # jwt related settings
    TOKEN_EXPIRE_MINUTES: int = 15
    TOKEN_REFRESH_MINUTES: int = 30
    TOKEN_ALGORITHM: str = "HS256"
    TOKEN_SECRET: str
    LOGIN_URL: str
    FORCE_RLS: bool = True

    # APPLICATION SETTINGS
    # Max Groups and Users for each type of tenant
    ENFORCE_MAX_GROUPS: bool = True
    ENFORCE_MAX_USERS: bool = True
    MAX_INDIVIDUAL_GROUPS: int = 1
    MAX_INDIVIDUAL_USERS: int = 1
    MAX_BUSINESS_GROUPS: int = 5
    MAX_BUSINESS_USERS: int = 5
    MAX_CORPORATE_GROUPS: int = 25
    MAX_CORPORATE_USERS: int = 25
    MAX_ENTERPRISE_GROUPS: int = -1
    MAX_ENTERPRISE_USERS: int = -1

    # Superuser settings
    SUPERUSER_EMAIL: str
    SUPERUSER_HANDLE: str
    SUPERUSER_FULL_NAME: str

    # VECTOR SEARCH SETTINGS
    VECTOR_DIMENSIONS: int = 1536
    VECTOR_INDEX_TYPE: str = "hnsw"
    VECTOR_BATCH_SIZE: int = 10
    VECTOR_UPDATE_INTERVAL: float = 1.0
    VECTOR_AUTO_START: bool = True
    VECTOR_ENTITIES: dict = {}

    # Modules to load
    LOAD_PACKAGES: list[str] = []
    APP_PATH: str = ""


class Prod(General):
    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env")


class Dev(General):
    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env_dev")


class Test(General):
    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env_test")


# Create a dictionary of environment settings
env_settings: dict[str, Type[General]] = {"dev": Dev, "test": Test, "prod": Prod}
# Select the environment settings based on the ENV variable
uno_settings: Dev | Test | Prod = env_settings[os.environ.get("ENV", "dev").lower()]()
