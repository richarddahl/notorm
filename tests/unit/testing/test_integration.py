# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the integration testing module.

These tests verify the functionality of the integration testing utilities.
"""

import pytest
import os
import subprocess
from unittest.mock import patch, MagicMock

from uno.testing.integration import IntegrationTestHarness
from uno.testing.integration.harness import ServiceConfig


class TestIntegrationTestHarness:
    """Tests for the IntegrationTestHarness class."""
    
    @patch("uno.testing.integration.harness.subprocess.run")
    def test_start_with_compose(self, mock_run):
        """Test starting services with Docker Compose."""
        # Mock the subprocess.run function
        mock_run.return_value = MagicMock(stdout="container_id")
        
        # Create a temporary docker-compose file
        compose_file = "docker-compose.test.yaml"
        with open(compose_file, "w") as f:
            f.write("version: '3'\nservices:\n  postgres:\n    image: postgres:13\n")
        
        try:
            # Create a harness with the compose file
            harness = IntegrationTestHarness(
                docker_compose_file=compose_file,
                project_name="test_project"
            )
            
            # Start services
            with harness.start_services():
                # Check that docker-compose was called correctly
                mock_run.assert_called_with(
                    [
                        "docker-compose",
                        "-f", compose_file,
                        "-p", "test_project",
                        "up", "-d"
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
            
            # Check that docker-compose down was called
            mock_run.assert_called_with(
                [
                    "docker-compose",
                    "-f", compose_file,
                    "-p", "test_project",
                    "down", "-v"
                ],
                check=True,
                capture_output=True,
                text=True
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(compose_file):
                os.remove(compose_file)
    
    @patch("uno.testing.integration.harness.subprocess.run")
    def test_start_individual_services(self, mock_run):
        """Test starting individual Docker services."""
        # Mock the subprocess.run function
        mock_run.return_value = MagicMock(stdout="container_id\n")
        
        # Create service configurations
        postgres_config = ServiceConfig(
            name="postgres",
            image="postgres:13",
            ports={5432: 5432},
            environment={"POSTGRES_PASSWORD": "test"}
        )
        
        redis_config = ServiceConfig(
            name="redis",
            image="redis:latest",
            ports={6379: 6379}
        )
        
        # Create a harness with the services
        harness = IntegrationTestHarness(
            services=[postgres_config, redis_config],
            project_name="test_project"
        )
        
        # Start services
        with harness.start_services():
            # Check that docker run was called for each service
            assert mock_run.call_count >= 2
            
            # Check the calls for postgres
            postgres_args = [
                arg for call in mock_run.call_args_list
                if "postgres" in str(call)
            ][0][0][0]
            assert "docker" in postgres_args
            assert "run" in postgres_args
            assert "--name" in postgres_args
            assert "test_project_postgres" in postgres_args
            assert "-p" in postgres_args
            assert "5432:5432" in postgres_args
            assert "-e" in postgres_args
            assert "POSTGRES_PASSWORD=test" in postgres_args
            
            # Check the calls for redis
            redis_args = [
                arg for call in mock_run.call_args_list
                if "redis" in str(call)
            ][0][0][0]
            assert "docker" in redis_args
            assert "run" in redis_args
            assert "--name" in redis_args
            assert "test_project_redis" in redis_args
            assert "-p" in redis_args
            assert "6379:6379" in redis_args
    
    def test_get_connection_string(self):
        """Test getting connection strings for services."""
        # Create service configurations
        postgres_config = ServiceConfig(
            name="postgres",
            image="postgres:13",
            ports={5432: 5432},
            environment={
                "POSTGRES_USER": "test_user",
                "POSTGRES_PASSWORD": "test_password",
                "POSTGRES_DB": "test_db"
            }
        )
        
        redis_config = ServiceConfig(
            name="redis",
            image="redis:latest",
            ports={6379: 6379}
        )
        
        # Create a harness with the services
        harness = IntegrationTestHarness(
            services=[postgres_config, redis_config]
        )
        
        # Get connection strings
        postgres_conn = harness.get_connection_string("postgres")
        redis_conn = harness.get_connection_string("redis")
        
        # Check the connection strings
        assert postgres_conn == "postgresql://test_user:test_password@localhost:5432/test_db"
        assert redis_conn == "redis://localhost:6379/0"
        
        # Check error for non-existent service
        with pytest.raises(ValueError):
            harness.get_connection_string("non_existent")
    
    def test_get_service_url(self):
        """Test getting URLs for services."""
        # Create service configurations
        web_config = ServiceConfig(
            name="webapp",
            image="nginx:latest",
            ports={8080: 80}
        )
        
        api_config = ServiceConfig(
            name="api",
            image="python:3.9",
            ports={8000: 8000}
        )
        
        # Create a harness with the services
        harness = IntegrationTestHarness(
            services=[web_config, api_config]
        )
        
        # Get service URLs
        web_url = harness.get_service_url("webapp")
        api_url = harness.get_service_url("api", path="/v1/users")
        
        # Check the URLs
        assert web_url == "http://localhost:8080/"
        assert api_url == "http://localhost:8000/v1/users"
        
        # Check error for non-existent service
        with pytest.raises(ValueError):
            harness.get_service_url("non_existent")
    
    def test_get_postgres_config(self):
        """Test the get_postgres_config helper method."""
        config = IntegrationTestHarness.get_postgres_config()
        
        assert config.name == "postgres"
        assert "postgres:16" in config.image
        assert 5432 in config.ports
        assert "POSTGRES_USER" in config.environment
        assert "POSTGRES_PASSWORD" in config.environment
        assert "POSTGRES_DB" in config.environment
        assert "database system is ready" in config.ready_log_message
    
    def test_get_redis_config(self):
        """Test the get_redis_config helper method."""
        config = IntegrationTestHarness.get_redis_config()
        
        assert config.name == "redis"
        assert "redis:" in config.image
        assert 6379 in config.ports
        assert "Ready to accept connections" in config.ready_log_message