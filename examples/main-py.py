# main.py
import asyncio
from fastapi import FastAPI
from src.uno.dependencies import get_service_provider, validate_dependencies

app = FastAPI()


@app.on_event("startup")
async def on_app_startup():
    provider = get_service_provider()
    # Validate dependencies before startup
    validate_dependencies(provider)
    # Initialize services
    await provider.initialize()
    print("Application startup complete.")


@app.on_event("shutdown")
async def on_app_shutdown():
    provider = get_service_provider()
    # Gracefully shutdown services
    await provider.shutdown()
    print("Application shutdown complete.")


# Your route definitions below
@app.get("/")
async def read_root():
    return {"message": "Hello, world!"}


"""
### How to use:
* Save this as your main application entry point (e.g., `main.py`)
* Run it with `uvicorn main:app --reload`
* The events will handle dependency validation, initialization, and cleanup automatically.
"""
