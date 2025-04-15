# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Deployment configuration.

This module provides classes and utilities for configuring the deployment
pipeline for Uno applications.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from pathlib import Path
import os
import yaml

from pydantic import BaseModel, Field, validator


class DeploymentEnvironment(str, Enum):
    """Deployment environment types."""

    DEV = "dev"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentPlatform(str, Enum):
    """Supported deployment platforms."""

    KUBERNETES = "kubernetes"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    HEROKU = "heroku"
    DIGITALOCEAN = "digitalocean"
    CUSTOM = "custom"


class DatabaseConfig(BaseModel):
    """Database configuration for deployment."""

    host: str = Field(..., description="Database host")
    port: int = Field(5432, description="Database port")
    name: str = Field(..., description="Database name")
    user: str = Field(..., description="Database username")
    password_env_var: str = Field(
        "DB_PASSWORD", description="Environment variable for database password"
    )
    ssl_mode: Optional[str] = Field(
        None, description="SSL mode for database connection"
    )
    connection_pool_min: int = Field(5, description="Minimum connection pool size")
    connection_pool_max: int = Field(20, description="Maximum connection pool size")
    apply_migrations: bool = Field(
        True, description="Apply migrations during deployment"
    )
    backup_before_deploy: bool = Field(
        True, description="Backup database before deployment"
    )


class ResourceRequirements(BaseModel):
    """Resource requirements for deployment."""

    cpu_min: str = Field("100m", description="Minimum CPU requirement")
    cpu_max: str = Field("500m", description="Maximum CPU requirement")
    memory_min: str = Field("256Mi", description="Minimum memory requirement")
    memory_max: str = Field("512Mi", description="Maximum memory requirement")
    replicas_min: int = Field(1, description="Minimum number of replicas")
    replicas_max: int = Field(3, description="Maximum number of replicas")
    auto_scaling: bool = Field(True, description="Enable auto-scaling")
    auto_scaling_cpu_threshold: int = Field(
        80, description="CPU utilization threshold for auto-scaling"
    )


class NetworkConfig(BaseModel):
    """Network configuration for deployment."""

    domain: Optional[str] = Field(None, description="Domain name")
    use_https: bool = Field(True, description="Use HTTPS")
    use_hsts: bool = Field(True, description="Use HTTP Strict Transport Security")
    ingress_annotations: Dict[str, str] = Field(
        default_factory=dict, description="Ingress annotations"
    )
    cors_allowed_origins: List[str] = Field(
        default_factory=list, description="CORS allowed origins"
    )
    rate_limiting: bool = Field(False, description="Enable rate limiting")
    rate_limit_requests: int = Field(100, description="Rate limit requests per minute")


class SecurityConfig(BaseModel):
    """Security configuration for deployment."""

    enable_network_policy: bool = Field(True, description="Enable network policy")
    pod_security_policy: str = Field("restricted", description="Pod security policy")
    scan_images: bool = Field(
        True, description="Scan container images for vulnerabilities"
    )
    scan_dependencies: bool = Field(
        True, description="Scan dependencies for vulnerabilities"
    )
    enable_secrets_encryption: bool = Field(
        True, description="Enable secrets encryption"
    )
    secrets_provider: str = Field("vault", description="Secrets provider")


class MonitoringConfig(BaseModel):
    """Monitoring configuration for deployment."""

    enable_logging: bool = Field(True, description="Enable logging")
    enable_metrics: bool = Field(True, description="Enable metrics collection")
    enable_tracing: bool = Field(True, description="Enable distributed tracing")
    log_level: str = Field("INFO", description="Log level")
    retention_days: int = Field(30, description="Log retention days")
    alerting: bool = Field(True, description="Enable alerting")
    alert_channels: List[str] = Field(
        default_factory=lambda: ["email"], description="Alert channels"
    )


class DeploymentStrategy(str, Enum):
    """Deployment strategy types."""

    BLUE_GREEN = "blue-green"
    ROLLING = "rolling"
    CANARY = "canary"
    RECREATE = "recreate"


class TestingConfig(BaseModel):
    """Testing configuration for deployment pipeline."""

    run_unit_tests: bool = Field(True, description="Run unit tests")
    run_integration_tests: bool = Field(True, description="Run integration tests")
    run_performance_tests: bool = Field(
        False, description="Run performance tests (can be time-consuming)"
    )
    run_security_tests: bool = Field(True, description="Run security tests")
    fail_on_test_failure: bool = Field(
        True, description="Fail deployment on test failure"
    )
    test_coverage_threshold: int = Field(
        80, description="Test coverage threshold percentage"
    )


class DeploymentConfig(BaseModel):
    """
    Main deployment configuration.

    This class represents the main configuration for deploying Uno applications
    using the deployment pipeline.
    """

    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application version")
    environment: DeploymentEnvironment = Field(
        DeploymentEnvironment.DEV, description="Deployment environment"
    )
    platform: DeploymentPlatform = Field(
        DeploymentPlatform.KUBERNETES, description="Deployment platform"
    )

    # Component configurations
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig, description="Database configuration"
    )
    resources: ResourceRequirements = Field(
        default_factory=ResourceRequirements, description="Resource requirements"
    )
    network: NetworkConfig = Field(
        default_factory=NetworkConfig, description="Network configuration"
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig, description="Security configuration"
    )
    monitoring: MonitoringConfig = Field(
        default_factory=MonitoringConfig, description="Monitoring configuration"
    )

    # Deployment strategy
    strategy: DeploymentStrategy = Field(
        DeploymentStrategy.ROLLING, description="Deployment strategy"
    )

    # Testing configuration
    testing: TestingConfig = Field(
        default_factory=TestingConfig, description="Testing configuration"
    )

    # Additional custom settings
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Custom settings"
    )

    # Environment variables to inject
    environment_variables: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )

    # Secrets (keys only, values should be provided securely)
    secrets: List[str] = Field(
        default_factory=list, description="Secret keys (values provided separately)"
    )

    # Path to additional configuration files
    config_files: List[str] = Field(
        default_factory=list, description="Additional configuration files"
    )

    @field_validator("environment_variables")
    def validate_environment_variables(
        cls, v: Dict[str, str], values: Dict[str, Any]
    ) -> Dict[str, str]:
        """Validate environment variables."""
        env = values.get("environment", DeploymentEnvironment.DEV)

        # Add default environment variable for environment
        v["UNO_ENV"] = env.value

        # Add database password environment variable
        if "database" in values:
            db_config = values["database"]
            if (
                hasattr(db_config, "password_env_var")
                and db_config.password_env_var not in v
            ):
                # Add as empty placeholder for documentation purposes
                v[db_config.password_env_var] = ""

        return v

    @field_validator("strategy")
    def validate_strategy(
        cls, v: DeploymentStrategy, values: Dict[str, Any]
    ) -> DeploymentStrategy:
        """Validate deployment strategy based on environment."""
        env = values.get("environment", DeploymentEnvironment.DEV)

        # Enforce blue-green or canary for production
        if env == DeploymentEnvironment.PRODUCTION and v not in [
            DeploymentStrategy.BLUE_GREEN,
            DeploymentStrategy.CANARY,
        ]:
            return DeploymentStrategy.BLUE_GREEN

        return v

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "DeploymentConfig":
        """
        Create a deployment configuration from a YAML file.

        Args:
            path: Path to the YAML file

        Returns:
            A DeploymentConfig instance
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def to_yaml(self, path: Union[str, Path]) -> None:
        """
        Save the deployment configuration to a YAML file.

        Args:
            path: Path to save the YAML file
        """
        with open(path, "w") as f:
            yaml.dump(self.dict(), f, sort_keys=False, indent=2)

    def for_environment(self, environment: DeploymentEnvironment) -> "DeploymentConfig":
        """
        Create a configuration for a specific environment.

        Args:
            environment: Target environment

        Returns:
            A new DeploymentConfig instance for the specified environment
        """
        config_dict = self.dict()
        config_dict["environment"] = environment

        # Adjust settings based on environment
        if environment == DeploymentEnvironment.PRODUCTION:
            # Production environments should use blue-green or canary
            config_dict["strategy"] = DeploymentStrategy.BLUE_GREEN

            # Increase resource requirements for production
            config_dict["resources"]["replicas_min"] = 2
            config_dict["resources"]["replicas_max"] = 5
            config_dict["resources"]["cpu_min"] = "250m"
            config_dict["resources"]["cpu_max"] = "1000m"
            config_dict["resources"]["memory_min"] = "512Mi"
            config_dict["resources"]["memory_max"] = "1Gi"

            # Enable security features for production
            config_dict["security"]["enable_network_policy"] = True
            config_dict["security"]["scan_images"] = True
            config_dict["security"]["scan_dependencies"] = True
            config_dict["security"]["enable_secrets_encryption"] = True

            # Enable all testing for production
            config_dict["testing"]["run_unit_tests"] = True
            config_dict["testing"]["run_integration_tests"] = True
            config_dict["testing"]["run_performance_tests"] = True
            config_dict["testing"]["run_security_tests"] = True
            config_dict["testing"]["fail_on_test_failure"] = True

        elif environment == DeploymentEnvironment.STAGING:
            # Staging should mimic production but with fewer resources
            config_dict["strategy"] = DeploymentStrategy.BLUE_GREEN
            config_dict["resources"]["replicas_min"] = 1
            config_dict["resources"]["replicas_max"] = 3

            # Enable most security features for staging
            config_dict["security"]["enable_network_policy"] = True
            config_dict["security"]["scan_images"] = True

            # Enable most testing for staging
            config_dict["testing"]["run_unit_tests"] = True
            config_dict["testing"]["run_integration_tests"] = True

        elif environment == DeploymentEnvironment.TEST:
            # Test environment can use simpler deployment
            config_dict["strategy"] = DeploymentStrategy.ROLLING
            config_dict["resources"]["replicas_min"] = 1
            config_dict["resources"]["replicas_max"] = 1

            # Basic security for test
            config_dict["security"]["enable_network_policy"] = False

            # Only basic testing for test environment
            config_dict["testing"]["run_unit_tests"] = True
            config_dict["testing"]["run_integration_tests"] = False

        elif environment == DeploymentEnvironment.DEV:
            # Dev environment should be simple
            config_dict["strategy"] = DeploymentStrategy.RECREATE
            config_dict["resources"]["replicas_min"] = 1
            config_dict["resources"]["replicas_max"] = 1
            config_dict["resources"]["auto_scaling"] = False

            # Minimal security for dev
            config_dict["security"]["enable_network_policy"] = False
            config_dict["security"]["scan_images"] = False

            # Only unit tests for dev
            config_dict["testing"]["run_unit_tests"] = True
            config_dict["testing"]["run_integration_tests"] = False
            config_dict["testing"]["run_performance_tests"] = False

        return DeploymentConfig(**config_dict)
