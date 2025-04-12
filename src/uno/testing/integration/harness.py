# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Integration test harness for Uno applications.

This module provides a test harness for running integration tests with
containerized dependencies such as PostgreSQL, Redis, and other services.
"""

import asyncio
import logging
import os
import subprocess
import time
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pytest
from pydantic import BaseModel, Field


class ServiceConfig(BaseModel):
    """Configuration for a containerized service."""
    
    name: str
    image: str
    ports: Dict[int, int] = Field(default_factory=dict)  # host_port: container_port
    environment: Dict[str, str] = Field(default_factory=dict)
    volumes: Dict[str, str] = Field(default_factory=dict)  # host_path: container_path
    command: Optional[str] = None
    health_check_url: Optional[str] = None
    health_check_port: Optional[int] = None
    ready_log_message: Optional[str] = None
    startup_timeout: int = 30  # seconds


class IntegrationTestHarness:
    """
    Harness for integration tests with containerized dependencies.
    
    This class provides utilities for starting and managing containerized services
    for integration testing, such as PostgreSQL, Redis, and other dependencies.
    
    Example:
        ```python
        @pytest.fixture(scope="session")
        def test_harness():
            harness = IntegrationTestHarness()
            with harness.start_services():
                yield harness
                
        def test_database_connection(test_harness):
            db = test_harness.get_database()
            # Test using the database
        ```
    """
    
    def __init__(
        self,
        docker_compose_file: Optional[Union[str, Path]] = None,
        services: Optional[List[ServiceConfig]] = None,
        project_name: str = "uno_test",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the integration test harness.
        
        Args:
            docker_compose_file: Path to a docker-compose.yaml file
            services: List of service configurations
            project_name: Docker Compose project name
            logger: Logger to use
        """
        self.docker_compose_file = docker_compose_file
        self.services = services or []
        self.project_name = project_name
        self.logger = logger or logging.getLogger(__name__)
        self.running_services = []
        
        # Configure logger
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @contextmanager
    def start_services(self) -> "IntegrationTestHarness":
        """
        Start all required services for testing.
        
        This is a context manager that starts the required services using
        Docker or Docker Compose, and ensures they are properly shut down
        after the tests are complete.
        
        Returns:
            The harness instance for method chaining
            
        Example:
            ```python
            with harness.start_services():
                # Run tests with services available
            # Services are automatically stopped
            ```
        """
        try:
            if self.docker_compose_file:
                self._start_with_compose()
            else:
                self._start_individual_services()
                
            # Wait for services to be ready
            self._wait_for_services()
            
            yield self
        finally:
            self._stop_services()
    
    def _start_with_compose(self) -> None:
        """Start services using Docker Compose."""
        self.logger.info(f"Starting services with Docker Compose from {self.docker_compose_file}")
        
        # Ensure compose file exists
        if not os.path.exists(self.docker_compose_file):
            raise FileNotFoundError(f"Docker Compose file not found: {self.docker_compose_file}")
        
        # Start services with docker-compose
        cmd = [
            "docker-compose",
            "-f", str(self.docker_compose_file),
            "-p", self.project_name,
            "up", "-d"
        ]
        
        try:
            subprocess.run(
                cmd, 
                check=True, 
                capture_output=True,
                text=True
            )
            self.logger.info("Docker Compose services started successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to start Docker Compose services: {e.stderr}")
            raise
    
    def _start_individual_services(self) -> None:
        """Start individual Docker services."""
        if not self.services:
            raise ValueError("No services configured for testing")
            
        for service in self.services:
            self.logger.info(f"Starting service: {service.name}")
            
            # Prepare the Docker run command
            cmd = ["docker", "run", "-d", "--name", f"{self.project_name}_{service.name}"]
            
            # Add port mappings
            for host_port, container_port in service.ports.items():
                cmd.extend(["-p", f"{host_port}:{container_port}"])
            
            # Add environment variables
            for name, value in service.environment.items():
                cmd.extend(["-e", f"{name}={value}"])
            
            # Add volumes
            for host_path, container_path in service.volumes.items():
                cmd.extend(["-v", f"{host_path}:{container_path}"])
            
            # Add image name
            cmd.append(service.image)
            
            # Add command if specified
            if service.command:
                cmd.extend(service.command.split())
            
            try:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True
                )
                container_id = result.stdout.strip()
                self.running_services.append(container_id)
                self.logger.info(f"Started {service.name} with container ID: {container_id}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to start {service.name}: {e.stderr}")
                raise
    
    def _wait_for_services(self) -> None:
        """Wait for all services to be ready."""
        for service in self.services:
            if service.health_check_url:
                self._wait_for_http_service(service)
            elif service.ready_log_message:
                self._wait_for_log_message(service)
            else:
                self.logger.info(f"No health check defined for {service.name}, assuming it's ready")
    
    def _wait_for_http_service(self, service: ServiceConfig) -> None:
        """Wait for an HTTP service to be ready."""
        import urllib.request
        
        url = service.health_check_url
        timeout = service.startup_timeout
        start_time = time.time()
        
        self.logger.info(f"Waiting for {service.name} to be ready at {url}")
        
        while time.time() - start_time < timeout:
            try:
                urllib.request.urlopen(url, timeout=2)
                self.logger.info(f"{service.name} is ready")
                return
            except Exception:
                time.sleep(1)
        
        self.logger.error(f"Timed out waiting for {service.name} to be ready")
        raise TimeoutError(f"Service {service.name} did not become ready within {timeout} seconds")
    
    def _wait_for_log_message(self, service: ServiceConfig) -> None:
        """Wait for a specific log message indicating the service is ready."""
        container_name = f"{self.project_name}_{service.name}"
        message = service.ready_log_message
        timeout = service.startup_timeout
        start_time = time.time()
        
        self.logger.info(f"Waiting for {service.name} log message: {message}")
        
        while time.time() - start_time < timeout:
            try:
                logs = subprocess.run(
                    ["docker", "logs", container_name],
                    check=True,
                    capture_output=True,
                    text=True
                ).stdout
                
                if message in logs:
                    self.logger.info(f"{service.name} is ready")
                    return
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(1)
        
        self.logger.error(f"Timed out waiting for {service.name} log message")
        raise TimeoutError(f"Service {service.name} did not become ready within {timeout} seconds")
    
    def _stop_services(self) -> None:
        """Stop all running services."""
        if self.docker_compose_file:
            self._stop_with_compose()
        else:
            self._stop_individual_services()
    
    def _stop_with_compose(self) -> None:
        """Stop services using Docker Compose."""
        self.logger.info("Stopping Docker Compose services")
        
        cmd = [
            "docker-compose",
            "-f", str(self.docker_compose_file),
            "-p", self.project_name,
            "down", "-v"
        ]
        
        try:
            subprocess.run(
                cmd, 
                check=True, 
                capture_output=True,
                text=True
            )
            self.logger.info("Docker Compose services stopped successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to stop Docker Compose services: {e.stderr}")
    
    def _stop_individual_services(self) -> None:
        """Stop individually started Docker containers."""
        for container_id in self.running_services:
            self.logger.info(f"Stopping container: {container_id}")
            try:
                subprocess.run(
                    ["docker", "stop", container_id],
                    check=True,
                    capture_output=True,
                    text=True
                )
                subprocess.run(
                    ["docker", "rm", container_id],
                    check=True,
                    capture_output=True,
                    text=True
                )
                self.logger.info(f"Stopped and removed container: {container_id}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to stop container {container_id}: {e.stderr}")
    
    def get_connection_string(self, service_name: str) -> str:
        """
        Get a connection string for a service.
        
        Args:
            service_name: Name of the service to get a connection string for
            
        Returns:
            A connection string for the service
        """
        for service in self.services:
            if service.name == service_name:
                if "postgres" in service.image:
                    user = service.environment.get("POSTGRES_USER", "postgres")
                    password = service.environment.get("POSTGRES_PASSWORD", "postgres")
                    db = service.environment.get("POSTGRES_DB", "postgres")
                    host = "localhost"
                    port = next(iter(service.ports.keys()), 5432)
                    return f"postgresql://{user}:{password}@{host}:{port}/{db}"
                elif "redis" in service.image:
                    host = "localhost"
                    port = next(iter(service.ports.keys()), 6379)
                    return f"redis://{host}:{port}/0"
        
        raise ValueError(f"No connection string available for service: {service_name}")
    
    def get_service_url(self, service_name: str, path: str = "/") -> str:
        """
        Get a URL for a service.
        
        Args:
            service_name: Name of the service to get a URL for
            path: Path to append to the URL
            
        Returns:
            A URL for the service
        """
        for service in self.services:
            if service.name == service_name:
                host = "localhost"
                port = next(iter(service.ports.keys()))
                return f"http://{host}:{port}{path}"
        
        raise ValueError(f"No URL available for service: {service_name}")
    
    @staticmethod
    def get_postgres_config() -> ServiceConfig:
        """
        Get a pre-configured PostgreSQL service configuration.
        
        Returns:
            A PostgreSQL service configuration
        """
        return ServiceConfig(
            name="postgres",
            image="postgres:16",
            ports={5432: 5432},
            environment={
                "POSTGRES_USER": "uno_test",
                "POSTGRES_PASSWORD": "uno_test",
                "POSTGRES_DB": "uno_test_db"
            },
            ready_log_message="database system is ready to accept connections"
        )
    
    @staticmethod
    def get_redis_config() -> ServiceConfig:
        """
        Get a pre-configured Redis service configuration.
        
        Returns:
            A Redis service configuration
        """
        return ServiceConfig(
            name="redis",
            image="redis:latest",
            ports={6379: 6379},
            ready_log_message="Ready to accept connections"
        )