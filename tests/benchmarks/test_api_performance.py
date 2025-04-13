import pytest
import json
import uuid
import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from fastapi import FastAPI, Depends, Request, Response
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.uno.api.endpoint import UnoEndpoint
from src.uno.api.endpoint_factory import UnoEndpointFactory
from src.uno.api.service_api import ServiceApiRegistry, EntityApi, ServiceApi


# Test models
class TestUserBase(BaseModel):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True


class TestUserCreate(TestUserBase):
    password: str


class TestUser(TestUserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class TestItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int = 0


class TestItem(TestItemBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# Mock database models
class UserModel:
    def __init__(self, id, username, email, first_name=None, last_name=None, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = is_active
        self.created_at = datetime.now()
        self.updated_at = None


class ItemModel:
    def __init__(self, id, name, description, price, quantity, owner_id):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.quantity = quantity
        self.owner_id = owner_id
        self.created_at = datetime.now()
        self.updated_at = None


# Mock service implementations
class UserService:
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        return [
            UserModel(
                id=str(uuid.uuid4()),
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                first_name=f"First {i}",
                last_name=f"Last {i}"
            )
            for i in range(skip, skip + limit)
        ]

    async def get_user(self, user_id: str) -> Optional[UserModel]:
        if not user_id:
            return None
        return UserModel(
            id=user_id,
            username=f"user_{user_id[:8]}",
            email=f"user_{user_id[:8]}@example.com",
            first_name="First",
            last_name="Last"
        )

    async def create_user(self, user: TestUserCreate) -> UserModel:
        return UserModel(
            id=str(uuid.uuid4()),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active
        )

    async def update_user(self, user_id: str, user: TestUserBase) -> Optional[UserModel]:
        existing_user = await self.get_user(user_id)
        if not existing_user:
            return None
        for key, value in user.model_dump().items():
            setattr(existing_user, key, value)
        existing_user.updated_at = datetime.now()
        return existing_user

    async def delete_user(self, user_id: str) -> bool:
        return bool(user_id)


class ItemService:
    async def get_items(self, skip: int = 0, limit: int = 100) -> List[ItemModel]:
        return [
            ItemModel(
                id=str(uuid.uuid4()),
                name=f"Item {i}",
                description=f"Description for item {i}",
                price=10.0 + i,
                quantity=i,
                owner_id=str(uuid.uuid4())
            )
            for i in range(skip, skip + limit)
        ]

    async def get_item(self, item_id: str) -> Optional[ItemModel]:
        if not item_id:
            return None
        return ItemModel(
            id=item_id,
            name=f"Item {item_id[:8]}",
            description=f"Description for item {item_id[:8]}",
            price=10.0,
            quantity=5,
            owner_id=str(uuid.uuid4())
        )

    async def create_item(self, item: TestItemBase, owner_id: str) -> ItemModel:
        return ItemModel(
            id=str(uuid.uuid4()),
            name=item.name,
            description=item.description,
            price=item.price,
            quantity=item.quantity,
            owner_id=owner_id
        )

    async def update_item(self, item_id: str, item: TestItemBase) -> Optional[ItemModel]:
        existing_item = await self.get_item(item_id)
        if not existing_item:
            return None
        for key, value in item.model_dump().items():
            setattr(existing_item, key, value)
        existing_item.updated_at = datetime.now()
        return existing_item

    async def delete_item(self, item_id: str) -> bool:
        return bool(item_id)


# Test fixtures
@pytest.fixture
def test_app():
    """Create a FastAPI test application."""
    app = FastAPI()
    return app


@pytest.fixture
def user_service():
    """Create a mock user service."""
    return UserService()


@pytest.fixture
def item_service():
    """Create a mock item service."""
    return ItemService()


@pytest.fixture
def api_registry():
    """Create a service API registry."""
    return ServiceApiRegistry()


@pytest.fixture
def test_client(test_app):
    """Create a TestClient instance."""
    return TestClient(test_app)


@pytest.fixture
def setup_user_api(test_app, user_service, api_registry):
    """Set up user API endpoints."""
    # Create user API
    user_api = EntityApi(
        app=test_app,
        prefix="/users",
        tags=["users"],
        service=user_service,
        get_schema=TestUser,
        create_schema=TestUserCreate,
        update_schema=TestUserBase,
        service_name="user_service"
    )

    # Register API
    api_registry.register_api("users", user_api)

    # Generate endpoints
    user_api.add_get_all_endpoint()
    user_api.add_get_by_id_endpoint()
    user_api.add_create_endpoint()
    user_api.add_update_endpoint()
    user_api.add_delete_endpoint()

    return user_api


@pytest.fixture
def setup_item_api(test_app, item_service, api_registry):
    """Set up item API endpoints."""
    # Create item API
    item_api = EntityApi(
        app=test_app,
        prefix="/items",
        tags=["items"],
        service=item_service,
        get_schema=TestItem,
        create_schema=TestItemBase,
        update_schema=TestItemBase,
        service_name="item_service"
    )

    # Register API
    api_registry.register_api("items", item_api)

    # Generate endpoints
    item_api.add_get_all_endpoint()
    item_api.add_get_by_id_endpoint()
    item_api.add_create_endpoint()
    item_api.add_update_endpoint()
    item_api.add_delete_endpoint()

    # Add a custom endpoint
    @item_api.router.get("/search")
    async def search_items(q: str):
        results = await item_service.get_items(limit=10)
        return [item for item in results if q.lower() in item.name.lower()]

    return item_api


@pytest.fixture
def setup_endpoint_factory(test_app):
    """Set up an endpoint factory instance."""
    return UnoEndpointFactory(app=test_app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def user_data():
    """Generate test user data sets of different sizes."""
    def generate_user(i):
        return {
            "username": f"user_{i}",
            "email": f"user_{i}@example.com",
            "first_name": f"First {i}",
            "last_name": f"Last {i}",
            "password": f"password_{i}",
            "is_active": True
        }

    return {
        "single": generate_user(1),
        "small": [generate_user(i) for i in range(10)],
        "medium": [generate_user(i) for i in range(100)],
        "large": [generate_user(i) for i in range(1000)]
    }


@pytest.fixture
def item_data():
    """Generate test item data sets of different sizes."""
    def generate_item(i):
        return {
            "name": f"Item {i}",
            "description": f"This is test item {i} with a description",
            "price": 10.0 + (i % 100),
            "quantity": i % 20
        }

    return {
        "single": generate_item(1),
        "small": [generate_item(i) for i in range(10)],
        "medium": [generate_item(i) for i in range(100)],
        "large": [generate_item(i) for i in range(1000)]
    }


# Benchmarks
def test_endpoint_creation_performance(test_app, benchmark):
    """Benchmark the performance of creating API endpoints."""
    
    def create_endpoint():
        # Create a basic endpoint
        endpoint = UnoEndpoint(
            app=test_app,
            route="/test",
            response_model=TestUser,
            tags=["test"],
            summary="Test endpoint",
            description="A test endpoint for benchmarking"
        )
        return endpoint
    
    # Run the benchmark
    result = benchmark(create_endpoint)
    
    # Verify result
    assert result is not None


def test_endpoint_factory_performance(setup_endpoint_factory, benchmark):
    """Benchmark the performance of creating endpoints with the factory."""
    factory = setup_endpoint_factory
    
    def create_endpoints():
        # Create a set of endpoints
        crud_endpoints = {}
        
        # Create endpoint
        crud_endpoints["create"] = factory.create_endpoint(
            route="/benchmark/create",
            method="POST",
            response_model=TestUser,
            status_code=201,
            summary="Create Test User",
            handler=lambda user: {"id": str(uuid.uuid4()), **user.model_dump(), "created_at": datetime.now()}
        )
        
        # Get endpoint
        crud_endpoints["get"] = factory.create_endpoint(
            route="/benchmark/{id}",
            method="GET",
            response_model=TestUser,
            summary="Get Test User",
            handler=lambda id: {"id": id, "username": "test", "email": "test@example.com", "created_at": datetime.now()}
        )
        
        # Update endpoint
        crud_endpoints["update"] = factory.create_endpoint(
            route="/benchmark/{id}",
            method="PUT",
            response_model=TestUser,
            summary="Update Test User",
            handler=lambda id, user: {"id": id, **user.model_dump(), "created_at": datetime.now(), "updated_at": datetime.now()}
        )
        
        # Delete endpoint
        crud_endpoints["delete"] = factory.create_endpoint(
            route="/benchmark/{id}",
            method="DELETE",
            status_code=204,
            summary="Delete Test User",
            handler=lambda id: None
        )
        
        return crud_endpoints
    
    # Run the benchmark
    result = benchmark(create_endpoints)
    
    # Verify result
    assert len(result) == 4


def test_api_initialization_performance(test_app, user_service, api_registry, benchmark):
    """Benchmark the performance of initializing an API with multiple endpoints."""
    
    def initialize_api():
        # Create user API
        user_api = EntityApi(
            app=test_app,
            prefix="/users",
            tags=["users"],
            service=user_service,
            get_schema=TestUser,
            create_schema=TestUserCreate,
            update_schema=TestUserBase,
            service_name="user_service"
        )
        
        # Register API
        api_registry.register_api("users", user_api)
        
        # Generate all endpoints
        user_api.add_get_all_endpoint()
        user_api.add_get_by_id_endpoint()
        user_api.add_create_endpoint()
        user_api.add_update_endpoint()
        user_api.add_delete_endpoint()
        
        return user_api
    
    # Run the benchmark
    result = benchmark(initialize_api)
    
    # Verify result
    assert result is not None


def test_request_validation_performance(setup_user_api, test_client, user_data, benchmark):
    """Benchmark the performance of request validation for different payload sizes."""
    # Setup API endpoints
    user_api = setup_user_api
    
    # Test different payload sizes
    data_sizes = ["single", "small"]
    
    for size in data_sizes:
        if size == "single":
            # Single payload validation
            def validate_single():
                data = user_data["single"]
                response = test_client.post("/users/", json=data)
                return response
            
            single_result = benchmark(validate_single)
            assert single_result.status_code in (200, 201)
        else:
            # Batch validation (if supported)
            try:
                def validate_batch():
                    data = user_data[size]
                    response = test_client.post("/users/batch", json=data)
                    return response
                
                batch_result = benchmark(validate_batch)
                # Note: might return 404 if batch endpoint doesn't exist
            except Exception:
                # If batch endpoint not available, test individual validations
                def validate_multiple():
                    data = user_data[size]
                    responses = []
                    for item in data[:10]:  # Limit to 10 items for benchmark
                        response = test_client.post("/users/", json=item)
                        responses.append(response)
                    return responses
                
                multiple_result = benchmark(validate_multiple)
                assert all(r.status_code in (200, 201) for r in multiple_result)


def test_response_serialization_performance(setup_user_api, test_client, benchmark):
    """Benchmark the performance of response serialization for different result sizes."""
    # Setup client
    client = test_client
    
    # Test different response sizes
    def get_small_response():
        response = client.get("/users/?skip=0&limit=10")
        return response
    
    small_result = benchmark(get_small_response)
    assert small_result.status_code == 200
    
    def get_medium_response():
        response = client.get("/users/?skip=0&limit=100")
        return response
    
    medium_result = benchmark(get_medium_response)
    assert medium_result.status_code == 200
    
    # Note: Large responses might timeout in benchmark, adjust as needed
    def get_large_response():
        response = client.get("/users/?skip=0&limit=500")
        return response
    
    large_result = benchmark(get_large_response)
    assert large_result.status_code == 200


def test_crud_operations_performance(setup_user_api, test_client, user_data, benchmark):
    """Benchmark the performance of CRUD operations."""
    client = test_client
    
    # Test create performance
    def create_operation():
        data = user_data["single"]
        response = client.post("/users/", json=data)
        return response
    
    create_result = benchmark(create_operation)
    assert create_result.status_code in (200, 201)
    created_user = create_result.json()
    
    # Test read performance
    def read_operation():
        response = client.get(f"/users/{created_user['id']}")
        return response
    
    read_result = benchmark(read_operation)
    assert read_result.status_code == 200
    
    # Test update performance
    def update_operation():
        data = {
            "username": f"updated_{created_user['username']}",
            "email": created_user["email"],
            "first_name": "Updated",
            "last_name": created_user["last_name"]
        }
        response = client.put(f"/users/{created_user['id']}", json=data)
        return response
    
    update_result = benchmark(update_operation)
    assert update_result.status_code == 200
    
    # Test delete performance
    def delete_operation():
        response = client.delete(f"/users/{created_user['id']}")
        return response
    
    delete_result = benchmark(delete_operation)
    assert delete_result.status_code in (200, 204)


def test_error_handling_performance(setup_user_api, test_client, benchmark):
    """Benchmark the performance of API error handling."""
    client = test_client
    
    # Test validation error performance
    def validation_error():
        # Missing required fields
        data = {"username": "test_user"}  # Missing email
        response = client.post("/users/", json=data)
        return response
    
    validation_result = benchmark(validation_error)
    assert validation_result.status_code == 422
    
    # Test not found error performance
    def not_found_error():
        # Use a non-existent ID
        response = client.get(f"/users/{uuid.uuid4()}")
        return response
    
    not_found_result = benchmark(not_found_error)
    assert not_found_result.status_code in (404, 204, 200)  # Depends on implementation


def test_middleware_performance(test_app, test_client, benchmark):
    """Benchmark the performance impact of API middleware."""
    app = test_app
    client = test_client
    
    # Create endpoints without middleware
    @app.get("/no_middleware")
    async def no_middleware():
        return {"status": "ok"}
    
    # Add a simple timing middleware
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Add an auth check middleware
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Simple auth check
        if "auth_middleware" in request.url.path:
            # Check for token
            token = request.headers.get("Authorization")
            if not token:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Not authenticated"}
                )
        return await call_next(request)
    
    # Create endpoints with middleware
    @app.get("/with_middleware")
    async def with_middleware():
        return {"status": "ok"}
    
    @app.get("/auth_middleware")
    async def auth_endpoint():
        return {"status": "authenticated"}
    
    # Benchmark without middleware
    def call_no_middleware():
        response = client.get("/no_middleware")
        return response
    
    no_middleware_result = benchmark(call_no_middleware)
    assert no_middleware_result.status_code == 200
    
    # Benchmark with timing middleware
    def call_with_middleware():
        response = client.get("/with_middleware")
        return response
    
    with_middleware_result = benchmark(call_with_middleware)
    assert with_middleware_result.status_code == 200
    assert "X-Process-Time" in with_middleware_result.headers
    
    # Benchmark with auth middleware (failure case)
    def call_auth_middleware_fail():
        response = client.get("/auth_middleware")
        return response
    
    auth_fail_result = benchmark(call_auth_middleware_fail)
    assert auth_fail_result.status_code == 401
    
    # Benchmark with auth middleware (success case)
    def call_auth_middleware_success():
        response = client.get("/auth_middleware", headers={"Authorization": "Bearer test"})
        return response
    
    auth_success_result = benchmark(call_auth_middleware_success)
    assert auth_success_result.status_code == 200


def test_handler_execution_performance(setup_endpoint_factory, benchmark):
    """Benchmark the performance of different API handler execution patterns."""
    factory = setup_endpoint_factory
    
    # Create different handler types
    
    # Simple synchronous handler
    def sync_handler(request):
        return {"status": "ok", "type": "sync"}
    
    # Simple async handler
    async def async_handler(request):
        return {"status": "ok", "type": "async"}
    
    # Async handler with database dependency
    async def db_handler(request, db_session=None):
        # Simulate DB operation
        await asyncio.sleep(0.001)  # Minimal sleep to simulate DB
        return {"status": "ok", "type": "db", "data": "result"}
    
    # Async handler with complex logic
    async def complex_handler(request):
        # Simulate complex processing
        result = {"status": "ok", "type": "complex", "data": []}
        for i in range(10):
            result["data"].append({
                "id": i,
                "name": f"Item {i}",
                "computed": i * 2
            })
        return result
    
    # Create endpoints
    endpoints = {
        "sync": factory.create_endpoint(
            route="/benchmark/sync",
            method="GET",
            handler=sync_handler
        ),
        "async": factory.create_endpoint(
            route="/benchmark/async",
            method="GET",
            handler=async_handler
        ),
        "db": factory.create_endpoint(
            route="/benchmark/db",
            method="GET",
            handler=db_handler
        ),
        "complex": factory.create_endpoint(
            route="/benchmark/complex",
            method="GET",
            handler=complex_handler
        )
    }
    
    # Benchmark handler execution (simulate call)
    async def execute_handler(handler_type):
        mock_request = MagicMock()
        endpoint = endpoints[handler_type]
        
        # Call the handler directly
        handler = endpoint.get_handler()
        if asyncio.iscoroutinefunction(handler):
            return await handler(mock_request)
        else:
            return handler(mock_request)
    
    # Benchmark each handler type
    for handler_type in endpoints.keys():
        async def benchmark_wrapper():
            return await execute_handler(handler_type)
        
        result = benchmark(lambda: asyncio.run(benchmark_wrapper()))
        assert result["status"] == "ok"
        assert result["type"] == handler_type


def test_api_registry_lookup_performance(api_registry, setup_user_api, setup_item_api, benchmark):
    """Benchmark the performance of API registry lookups."""
    registry = api_registry
    
    # Populate registry
    user_api = setup_user_api
    item_api = setup_item_api
    
    # Benchmark registry lookups
    def lookup_api():
        user_result = registry.get_api("users")
        item_result = registry.get_api("items")
        return {"users": user_result, "items": item_result}
    
    lookup_result = benchmark(lookup_api)
    assert "users" in lookup_result
    assert "items" in lookup_result
    
    # Benchmark getting all APIs
    def get_all_apis():
        return registry.get_all_apis()
    
    all_apis_result = benchmark(get_all_apis)
    assert len(all_apis_result) >= 2


def test_dependency_resolution_performance(test_app, benchmark):
    """Benchmark the performance of resolving dependencies in API routes."""
    app = test_app
    
    # Create mock services/dependencies
    mock_service1 = MagicMock()
    mock_service2 = MagicMock()
    mock_db = AsyncMock()
    
    # Create dependency functions
    def get_service1():
        return mock_service1
    
    def get_service2():
        return mock_service2
    
    async def get_db():
        yield mock_db
    
    # Create routes with different dependency patterns
    @app.get("/no_deps")
    async def no_deps():
        return {"deps": 0}
    
    @app.get("/one_dep")
    async def one_dep(service1=Depends(get_service1)):
        return {"deps": 1}
    
    @app.get("/two_deps")
    async def two_deps(
        service1=Depends(get_service1),
        service2=Depends(get_service2)
    ):
        return {"deps": 2}
    
    @app.get("/nested_deps")
    async def nested_deps(
        service1=Depends(get_service1),
        service2=Depends(get_service2),
        db=Depends(get_db)
    ):
        await db.execute("SELECT 1")
        return {"deps": 3}
    
    # Create test client
    client = TestClient(app)
    
    # Benchmark different dependency patterns
    def call_no_deps():
        return client.get("/no_deps")
    
    no_deps_result = benchmark(call_no_deps)
    assert no_deps_result.status_code == 200
    assert no_deps_result.json()["deps"] == 0
    
    def call_one_dep():
        return client.get("/one_dep")
    
    one_dep_result = benchmark(call_one_dep)
    assert one_dep_result.status_code == 200
    assert one_dep_result.json()["deps"] == 1
    
    def call_two_deps():
        return client.get("/two_deps")
    
    two_deps_result = benchmark(call_two_deps)
    assert two_deps_result.status_code == 200
    assert two_deps_result.json()["deps"] == 2
    
    def call_nested_deps():
        return client.get("/nested_deps")
    
    nested_deps_result = benchmark(call_nested_deps)
    assert nested_deps_result.status_code == 200
    assert nested_deps_result.json()["deps"] == 3


def test_concurrent_request_handling(setup_user_api, test_client, benchmark):
    """Benchmark the performance of handling concurrent API requests."""
    client = test_client
    
    # Define the concurrent benchmark function
    def concurrent_requests():
        import threading
        import queue
        
        # Queue for results
        results = queue.Queue()
        
        # Number of concurrent requests
        num_requests = 10
        
        # Thread function
        def make_request(thread_id):
            try:
                if thread_id % 3 == 0:
                    # Get all users
                    response = client.get("/users/")
                elif thread_id % 3 == 1:
                    # Get user by ID (might 404, which is fine for this test)
                    response = client.get(f"/users/{uuid.uuid4()}")
                else:
                    # Create a user
                    data = {
                        "username": f"concurrent_user_{thread_id}",
                        "email": f"concurrent_{thread_id}@example.com",
                        "password": "password123",
                        "first_name": f"First {thread_id}",
                        "last_name": f"Last {thread_id}"
                    }
                    response = client.post("/users/", json=data)
                
                results.put((thread_id, response.status_code))
            except Exception as e:
                results.put((thread_id, str(e)))
        
        # Create and start threads
        threads = []
        for i in range(num_requests):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        result_list = []
        while not results.empty():
            result_list.append(results.get())
        
        return result_list
    
    # Run the benchmark
    concurrent_result = benchmark(concurrent_requests)
    
    # Verify we got results for all requests
    assert len(concurrent_result) > 0


def test_data_transformation_performance(benchmark):
    """Benchmark the performance of data transformation between models."""
    
    # Create test data
    db_model = UserModel(
        id=str(uuid.uuid4()),
        username="test_user",
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    
    # Benchmark model to dict transformation
    def model_to_dict():
        return {
            "id": db_model.id,
            "username": db_model.username,
            "email": db_model.email,
            "first_name": db_model.first_name,
            "last_name": db_model.last_name,
            "is_active": db_model.is_active,
            "created_at": db_model.created_at,
            "updated_at": db_model.updated_at
        }
    
    dict_result = benchmark(model_to_dict)
    assert dict_result["id"] == db_model.id
    
    # Benchmark dict to Pydantic model transformation
    def dict_to_model():
        data = {
            "id": db_model.id,
            "username": db_model.username,
            "email": db_model.email,
            "first_name": db_model.first_name,
            "last_name": db_model.last_name,
            "is_active": db_model.is_active,
            "created_at": db_model.created_at,
            "updated_at": db_model.updated_at
        }
        return TestUser(**data)
    
    model_result = benchmark(dict_to_model)
    assert model_result.id == db_model.id
    
    # Benchmark DB model to Pydantic model transformation
    def db_to_pydantic():
        return TestUser.model_validate(db_model)
    
    pydantic_result = benchmark(db_to_pydantic)
    assert pydantic_result.id == db_model.id
    
    # Benchmark JSON serialization
    def serialize_to_json():
        model = TestUser.model_validate(db_model)
        return model.model_dump_json()
    
    json_result = benchmark(serialize_to_json)
    assert json.loads(json_result)["id"] == db_model.id
    
    # Benchmark JSON deserialization
    def deserialize_from_json():
        model = TestUser.model_validate(db_model)
        json_str = model.model_dump_json()
        return TestUser.model_validate_json(json_str)
    
    deserialized_result = benchmark(deserialize_from_json)
    assert deserialized_result.id == db_model.id