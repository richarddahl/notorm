"""
Tests for the modeler module server.
"""

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from uno.devtools.modeler.server import app

class TestModelerServer:
    """Tests for the modeler server."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    def test_read_root(self, client):
        """Test the root endpoint returns the main page."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check for key HTML elements
        content = response.text
        assert "<title>" in content
        assert "data-modeler-app" in content
    
    @patch('uno.devtools.modeler.server.CodeGenerator')
    def test_generate_code(self, mock_code_generator, client):
        """Test the code generation endpoint."""
        # Setup mock
        mock_generator_instance = MagicMock()
        mock_code_generator.return_value = mock_generator_instance
        mock_generator_instance.generate.return_value = {
            "entities": {"Test": "class Test:\n    pass"},
            "repositories": {},
            "services": {}
        }
        
        # Test data
        test_data = {
            "projectName": "TestProject",
            "entities": [
                {
                    "id": "entity1",
                    "name": "Test",
                    "fields": [
                        {"name": "id", "type": "uuid", "primaryKey": True}
                    ]
                }
            ],
            "relationships": []
        }
        
        # Make request
        response = client.post("/api/devtools/model/generate", json=test_data)
        
        # Check response
        assert response.status_code == 200
        assert "entities" in response.json()
        assert "Test" in response.json()["entities"]
        
        # Verify mock was called correctly
        mock_code_generator.assert_called_once_with("TestProject")
        mock_generator_instance.generate.assert_called_once()
    
    @patch('uno.devtools.modeler.server.AnalyzeCodebase')
    def test_analyze_codebase(self, mock_analyze_codebase, client):
        """Test the codebase analysis endpoint."""
        # Setup mock
        mock_analyzer_instance = MagicMock()
        mock_analyze_codebase.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze.return_value = {
            "entities": [
                {
                    "id": "entity1",
                    "name": "TestEntity",
                    "fields": [
                        {"name": "id", "type": "str", "primaryKey": True}
                    ]
                }
            ],
            "relationships": []
        }
        
        # Make request
        response = client.post(
            "/api/devtools/model/analyze",
            params={"project_path": "/test/path", "model_type": "entity"}
        )
        
        # Check response
        assert response.status_code == 200
        assert "entities" in response.json()
        assert len(response.json()["entities"]) == 1
        
        # Verify mock was called correctly
        mock_analyze_codebase.assert_called_once_with("/test/path")
        mock_analyzer_instance.analyze.assert_called_once()
    
    def test_list_projects(self, client):
        """Test the list projects endpoint."""
        response = client.get("/api/devtools/model/projects")
        
        # Check response structure
        assert response.status_code == 200
        assert "projects" in response.json()
        assert isinstance(response.json()["projects"], list)
    
    @patch('uno.devtools.modeler.server.uvicorn')
    @patch('uno.devtools.modeler.server.webbrowser')
    @patch('uno.devtools.modeler.server.threading')
    def test_start_server_with_browser(self, mock_threading, mock_webbrowser, mock_uvicorn):
        """Test starting the server with browser."""
        from uno.devtools.modeler.server import start_server
        
        # Call with default parameters
        start_server(host="localhost", port=8765, open_browser=True)
        
        # Check if browser was launched
        mock_threading.Thread.assert_called_once()
        
        # Check if server was started
        mock_uvicorn.run.assert_called_once_with(app, host="localhost", port=8765)
    
    @patch('uno.devtools.modeler.server.uvicorn')
    @patch('uno.devtools.modeler.server.webbrowser')
    def test_start_server_without_browser(self, mock_webbrowser, mock_uvicorn):
        """Test starting the server without browser."""
        from uno.devtools.modeler.server import start_server
        
        # Call with browser disabled
        start_server(host="localhost", port=8765, open_browser=False)
        
        # Check if browser was not launched
        mock_webbrowser.open.assert_not_called()
        
        # Check if server was started
        mock_uvicorn.run.assert_called_once_with(app, host="localhost", port=8765)