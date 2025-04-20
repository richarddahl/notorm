import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uno.core.errors import (
    FrameworkError,
    ErrorCategory,
    ErrorSeverity,
)
from uno.core.errors.framework import ErrorDetail, ErrorCatalog
from uno.core.errors.middleware import ErrorHandlingMiddleware


def test_framework_error_handling():
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/test")
    async def test_endpoint():
        raise FrameworkError(
            code="TEST_ERROR",
            message="Test error message",
            details={"key": "value"},
            category=ErrorCategory.BUSINESS,
            severity=ErrorSeverity.ERROR,
            http_status_code=400,
        )

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "TEST_ERROR",
            "message": "Test error message",
            "details": {"key": "value"},
            "category": "BUSINESS",
            "severity": "ERROR",
            "timestamp": response.json()["error"]["timestamp"],
        }
    }


def test_validation_error_handling():
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.post("/test")
    async def test_endpoint(data: dict):
        return data

    client = TestClient(app)
    response = client.post("/test", json={"invalid": "data"})

    assert response.status_code == 400
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "errors" in response.json()["error"]["details"]


def test_internal_error_handling():
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/test")
    async def test_endpoint():
        raise Exception("Internal error")

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {"message": "Internal error"},
        }
    }
