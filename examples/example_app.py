# example_app.py
from fastapi import FastAPI
from src.uno.dependencies import get_service_provider, register_singleton
from src.uno.errors import UnoError

# --- Service Declarations ---


@register_singleton
class MyDatabaseService:
    dependencies = []

    def __init__(self):
        print("MyDatabaseService initialized.")


@register_singleton
class MyApplicationService:
    dependencies = [MyDatabaseService]

    def __init__(self, db_service: MyDatabaseService):
        self.db_service = db_service
        print("MyApplicationService initialized.")


# --- Dependency Validation Function ---


def validate_dependencies(provider):
    services = provider.get_all_registered_services()

    # Build the dependency graph
    dependency_graph = {
        service: getattr(service, "dependencies", []) for service in services
    }

    # Check for missing dependencies
    for service, deps in dependency_graph.items():
        for dep in deps:
            if dep not in services:
                raise UnoError(f"Missing dependency: {dep} for {service}")

    # Detect circular dependencies
    visited = set()
    rec_stack = set()

    def visit(node):
        if node in rec_stack:
            raise UnoError(f"Circular dependency detected at {node}")
        if node in visited:
            return
        rec_stack.add(node)
        for neighbor in dependency_graph.get(node, []):
            visit(neighbor)
        rec_stack.remove(node)
        visited.add(node)

    for service in dependency_graph:
        visit(service)
    print("All dependencies validated successfully.")


# --- FastAPI Lifecycle Integration ---

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    provider = get_service_provider()
    print("Starting application: Validating dependencies...")
    validate_dependencies(provider)
    print("Initializing services...")
    await provider.initialize()
    print("Application startup complete.")


@app.on_event("shutdown")
async def on_shutdown():
    provider = get_service_provider()
    print("Shutting down services...")
    await provider.shutdown()
    print("Application shutdown complete.")


@app.get("/")
async def root():
    return {"message": "Hello, World!"}
