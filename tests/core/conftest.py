"""
Test fixtures for core framework tests.
"""
import asyncio
import pytest
from typing import Dict, Any, Callable, Awaitable, Generator, AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_config():
    """Create a mock configuration provider for testing."""
    config_values = {
        "database.url": "postgresql://test:test@localhost:5432/test_db",
        "database.pool.min_size": 2,
        "database.pool.max_size": 10,
        "api.host": "localhost",
        "api.port": 8000,
        "logging.level": "INFO",
        "features.vector_search": True,
    }
    
    class MockConfig:
        def get(self, key: str, default: Any = None) -> Any:
            return config_values.get(key, default)
            
        def all(self) -> Dict[str, Any]:
            return config_values.copy()
            
        def set(self, key: str, value: Any) -> None:
            config_values[key] = value
            
        def load(self, path: str) -> None:
            pass
            
        def reload(self) -> None:
            pass
            
        def get_section(self, section: str) -> Dict[str, Any]:
            prefix = f"{section}."
            return {
                k[len(prefix):]: v 
                for k, v in config_values.items() 
                if k.startswith(prefix)
            }
    
    return MockConfig()


@pytest.fixture
async def mock_event_bus():
    """Create a mock event bus for testing."""
    published_events = []
    subscribers: Dict[str, list] = {}
    
    class MockEventBus:
        async def publish(self, event: Any) -> None:
            published_events.append(event)
            event_type = getattr(event, "event_type", event.__class__.__name__)
            if event_type in subscribers:
                for handler in subscribers[event_type]:
                    await handler(event)
        
        async def subscribe(self, event_type: str, handler: Callable[[Any], Awaitable[None]]) -> None:
            if event_type not in subscribers:
                subscribers[event_type] = []
            subscribers[event_type].append(handler)
        
        async def unsubscribe(self, event_type: str, handler: Callable[[Any], Awaitable[None]]) -> None:
            if event_type in subscribers and handler in subscribers[event_type]:
                subscribers[event_type].remove(handler)
        
        def get_published_events(self) -> list:
            return published_events.copy()
        
        def clear_published_events(self) -> None:
            published_events.clear()
    
    return MockEventBus()


@pytest.fixture
async def mock_database():
    """Create a mock database provider for testing."""
    class MockTransaction:
        def __init__(self):
            self.committed = False
            self.rolled_back = False
            self.queries = []
            
        async def execute(self, query: str, *args, **kwargs) -> str:
            self.queries.append((query, args))
            return "OK"
            
        async def fetch(self, query: str, *args, **kwargs) -> list:
            self.queries.append((query, args))
            return []
            
        async def fetchrow(self, query: str, *args, **kwargs) -> Dict[str, Any]:
            self.queries.append((query, args))
            return {}
            
        async def fetchval(self, query: str, *args, **kwargs) -> Any:
            self.queries.append((query, args))
            return None
            
        async def commit(self) -> None:
            self.committed = True
            
        async def rollback(self) -> None:
            self.rolled_back = True
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
    
    class MockDatabase:
        def __init__(self):
            self.queries = []
            self.initialized = False
            self.closed = False
            
        async def initialize(self) -> None:
            self.initialized = True
            
        async def close(self) -> None:
            self.closed = True
            
        async def execute(self, query: str, *args, **kwargs) -> str:
            self.queries.append((query, args))
            return "OK"
            
        async def fetch(self, query: str, *args, **kwargs) -> list:
            self.queries.append((query, args))
            return []
            
        async def fetchrow(self, query: str, *args, **kwargs) -> Dict[str, Any]:
            self.queries.append((query, args))
            return {}
            
        async def fetchval(self, query: str, *args, **kwargs) -> Any:
            self.queries.append((query, args))
            return None
            
        async def begin(self) -> MockTransaction:
            return MockTransaction()
            
        def get_queries(self) -> list:
            return self.queries.copy()
            
        def clear_queries(self) -> None:
            self.queries.clear()
    
    return MockDatabase()