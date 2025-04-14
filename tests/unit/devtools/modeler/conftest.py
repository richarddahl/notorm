"""
Pytest configuration for modeler tests.
"""

import pytest
import sys
from unittest.mock import MagicMock

# Mock any problematic modules to avoid dependencies
sys.modules['uno.core.di'] = MagicMock()
sys.modules['uno.database.db'] = MagicMock()
sys.modules['uno.database.manager'] = MagicMock()
sys.modules['uno.core.result'] = MagicMock()
sys.modules['uno.core.errors'] = MagicMock()

@pytest.fixture
def mock_environment(monkeypatch):
    """Mock Environment for template testing."""
    class MockEnvironment:
        def __init__(self, *args, **kwargs):
            self.filters = {}
            self.templates = {}
        
        def get_template(self, name):
            mock_template = MagicMock()
            mock_template.render.return_value = f"Rendered template: {name}"
            return mock_template
    
    monkeypatch.setattr('uno.devtools.modeler.generator.Environment', MockEnvironment)
    return MockEnvironment

@pytest.fixture
def temp_project_structure(tmp_path):
    """Create a temporary project structure for testing."""
    # Create project directories
    domain_dir = tmp_path / "src" / "testapp" / "domain"
    domain_dir.mkdir(parents=True)
    
    # Create a sample entity file
    entity_file = domain_dir / "user.py"
    entity_file.write_text("""
from pydantic import BaseModel
from typing import Optional, List

class User(BaseModel):
    id: str
    username: str
    email: str
    active: bool = True
    """)
    
    # Create a relationship file
    relation_file = domain_dir / "order.py"
    relation_file.write_text("""
from pydantic import BaseModel
from typing import Optional, List
from .user import User

class Order(BaseModel):
    id: str
    user_id: str
    amount: float
    user: Optional[User] = None
    items: List[str] = []
    """)
    
    return tmp_path