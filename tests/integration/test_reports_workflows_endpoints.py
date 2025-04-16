"""
Integration tests for reports and workflows domain endpoints.

This module contains tests that validate the entire flow from API endpoints
through services and repositories to ensure domain-driven endpoints are
working correctly for the reports and workflows modules.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
import json
from typing import Dict, Any, List, Optional

from uno.core.di import get_container, clear_container
from uno.dependencies.testing import configure_test_container
from uno.domain.api_integration import create_domain_router

# Import domain entities and services
from uno.reports.domain_endpoints import create_reports_router
from uno.workflows.domain_endpoints import create_workflows_router


@pytest.fixture
def test_client():
    """Create a test client for FastAPI with domain routers."""
    # Set up the test container with mocks
    configure_test_container()
    
    # Create the FastAPI application
    app = FastAPI()
    
    # Add domain routers
    app.include_router(create_reports_router())
    app.include_router(create_workflows_router())
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clean up
    clear_container()


class TestReportsEndpoints:
    """Tests for the reports endpoints."""
    
    def test_create_report_template(self, test_client):
        """Test creating a report template."""
        # Arrange
        template_data = {
            "name": "Test Report Template",
            "description": "A test report template",
            "template_type": "standard",
            "config": {"title": "Test Report", "fields": []}
        }
        
        # Act
        response = test_client.post("/report-templates", json=template_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == template_data["name"]
        assert data["description"] == template_data["description"]
        assert "id" in data
    
    def test_get_report_template(self, test_client):
        """Test retrieving a report template."""
        # Arrange - Create a report template first
        template_data = {
            "name": "Test Report Template",
            "description": "A test report template",
            "template_type": "standard",
            "config": {"title": "Test Report", "fields": []}
        }
        create_response = test_client.post("/report-templates", json=template_data)
        created_data = create_response.json()
        template_id = created_data["id"]
        
        # Act
        response = test_client.get(f"/report-templates/{template_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == template_data["name"]
        assert data["description"] == template_data["description"]
    
    def test_execute_report(self, test_client):
        """Test executing a report."""
        # Arrange - Create a report template first
        template_data = {
            "name": "Test Execution Template",
            "description": "A template for testing execution",
            "template_type": "standard",
            "config": {"title": "Test Report", "fields": []}
        }
        create_response = test_client.post("/report-templates", json=template_data)
        created_data = create_response.json()
        template_id = created_data["id"]
        
        # Act - Execute the report
        execution_data = {
            "template_id": template_id,
            "parameters": {"date_range": "2024-01-01,2024-12-31"}
        }
        response = test_client.post("/report-executions", json=execution_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["template_id"] == template_id
        assert "id" in data
        assert "status" in data


class TestWorkflowsEndpoints:
    """Tests for the workflows endpoints."""
    
    def test_create_workflow_definition(self, test_client):
        """Test creating a workflow definition."""
        # Arrange
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "step1",
                    "name": "First Step",
                    "type": "task",
                    "config": {}
                },
                {
                    "id": "step2",
                    "name": "Second Step",
                    "type": "task",
                    "config": {}
                }
            ],
            "transitions": [
                {
                    "from_step_id": "step1",
                    "to_step_id": "step2",
                    "condition": "true"
                }
            ]
        }
        
        # Act
        response = test_client.post("/workflows", json=workflow_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == workflow_data["name"]
        assert data["description"] == workflow_data["description"]
        assert "id" in data
    
    def test_get_workflow_definition(self, test_client):
        """Test retrieving a workflow definition."""
        # Arrange - Create a workflow first
        workflow_data = {
            "name": "Test Workflow Get",
            "description": "A test workflow for get operation",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "step1",
                    "name": "First Step",
                    "type": "task",
                    "config": {}
                }
            ],
            "transitions": []
        }
        create_response = test_client.post("/workflows", json=workflow_data)
        created_data = create_response.json()
        workflow_id = created_data["id"]
        
        # Act
        response = test_client.get(f"/workflows/{workflow_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == workflow_data["name"]
        assert data["description"] == workflow_data["description"]
    
    def test_start_workflow_execution(self, test_client):
        """Test starting a workflow execution."""
        # Arrange - Create a workflow first
        workflow_data = {
            "name": "Test Workflow Execution",
            "description": "A test workflow for execution",
            "version": "1.0.0",
            "steps": [
                {
                    "id": "step1",
                    "name": "First Step",
                    "type": "task",
                    "config": {}
                }
            ],
            "transitions": []
        }
        create_response = test_client.post("/workflows", json=workflow_data)
        created_data = create_response.json()
        workflow_id = created_data["id"]
        
        # Act - Start a workflow execution
        execution_data = {
            "workflow_id": workflow_id,
            "input_data": {"test": "value"}
        }
        response = test_client.post("/workflow-executions", json=execution_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert "id" in data
        assert "status" in data