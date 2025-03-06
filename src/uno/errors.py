# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
from fastapi import HTTPException, status


class UnoError(Exception):
    message: str
    error_code: str

    def __init__(self, message, error_code):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class UnoRegistryError(UnoError):
    pass


class DataExistsError(HTTPException):
    status_code = 400
    detail = "Record matching data already exists in database."


class UnauthorizedError(HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid user credentials"
    headers = {"WWW-enticate": "Bearer"}


class ForbiddenError(HTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You do not have permission to access this resource."
