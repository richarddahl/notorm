"""
Tests for the Deployment module domain entities.

These tests verify the behavior of the domain entities in the Deployment module,
ensuring they meet the business requirements and behave as expected.
"""

import uuid
import pytest
from datetime import datetime, UTC
from typing import Optional, Dict, List, Any

from uno.deployment.entities import (
    DeploymentId, PipelineId, StageId, TaskId, StrategyId,
    DeploymentConfig, Pipeline, Stage, Task,
    DeploymentEnvironment, DeploymentPlatform, DeploymentStrategy,
    DeploymentStatus, StageStatus, TaskStatus,
    DatabaseConfig, ResourceRequirements, NetworkConfig, SecurityConfig,
    MonitoringConfig, TestingConfig,
    DeploymentResult
)


class TestDeploymentEntities:
    """Tests for the deployment domain entities."""

    def test_deployment_id_creation(self):
        """Test creation of a DeploymentId."""
        id_value = str(uuid.uuid4())
        deployment_id = DeploymentId(value=id_value)
        assert deployment_id.value == id_value

    def test_task_id_creation(self):
        """Test creation of a TaskId."""
        id_value = str(uuid.uuid4())
        task_id = TaskId(value=id_value)
        assert task_id.value == id_value

    def test_stage_id_creation(self):
        """Test creation of a StageId."""
        id_value = str(uuid.uuid4())
        stage_id = StageId(value=id_value)
        assert stage_id.value == id_value

    def test_pipeline_id_creation(self):
        """Test creation of a PipelineId."""
        id_value = str(uuid.uuid4())
        pipeline_id = PipelineId(value=id_value)
        assert pipeline_id.value == id_value

    def test_strategy_id_creation(self):
        """Test creation of a StrategyId."""
        id_value = str(uuid.uuid4())
        strategy_id = StrategyId(value=id_value)
        assert strategy_id.value == id_value

    def test_database_config_creation(self):
        """Test creation of a DatabaseConfig entity."""
        db_config = DatabaseConfig(
            host="localhost",
            port=5432,
            name="testdb",
            user="testuser",
            password_env_var="DB_PASSWORD",
            ssl_mode="require",
            connection_pool_min=5,
            connection_pool_max=10,
            apply_migrations=True,
            backup_before_deploy=True
        )

        assert db_config.host == "localhost"
        assert db_config.port == 5432
        assert db_config.name == "testdb"
        assert db_config.user == "testuser"
        assert db_config.password_env_var == "DB_PASSWORD"
        assert db_config.ssl_mode == "require"
        assert db_config.connection_pool_min == 5
        assert db_config.connection_pool_max == 10
        assert db_config.apply_migrations is True
        assert db_config.backup_before_deploy is True
        assert isinstance(db_config.created_at, datetime)
        assert isinstance(db_config.updated_at, datetime)

    def test_database_config_methods(self):
        """Test methods of the DatabaseConfig entity."""
        db_config = DatabaseConfig(
            host="localhost",
            port=5432,
            name="testdb",
            user="testuser"
        )

        # Test update_connection_pool_size
        original_updated_at = db_config.updated_at
        db_config.update_connection_pool_size(10, 20)
        assert db_config.connection_pool_min == 10
        assert db_config.connection_pool_max == 20
        assert db_config.updated_at > original_updated_at

        # Test disable_migrations
        original_updated_at = db_config.updated_at
        db_config.disable_migrations()
        assert db_config.apply_migrations is False
        assert db_config.updated_at > original_updated_at

        # Test enable_migrations
        original_updated_at = db_config.updated_at
        db_config.enable_migrations()
        assert db_config.apply_migrations is True
        assert db_config.updated_at > original_updated_at

        # Test disable_backup
        original_updated_at = db_config.updated_at
        db_config.disable_backup()
        assert db_config.backup_before_deploy is False
        assert db_config.updated_at > original_updated_at

        # Test enable_backup
        original_updated_at = db_config.updated_at
        db_config.enable_backup()
        assert db_config.backup_before_deploy is True
        assert db_config.updated_at > original_updated_at

    def test_resource_requirements_creation(self):
        """Test creation of a ResourceRequirements entity."""
        resources = ResourceRequirements(
            cpu_min="100m",
            cpu_max="500m",
            memory_min="256Mi",
            memory_max="512Mi",
            replicas_min=1,
            replicas_max=3,
            auto_scaling=True,
            auto_scaling_cpu_threshold=80
        )

        assert resources.cpu_min == "100m"
        assert resources.cpu_max == "500m"
        assert resources.memory_min == "256Mi"
        assert resources.memory_max == "512Mi"
        assert resources.replicas_min == 1
        assert resources.replicas_max == 3
        assert resources.auto_scaling is True
        assert resources.auto_scaling_cpu_threshold == 80
        assert isinstance(resources.created_at, datetime)
        assert isinstance(resources.updated_at, datetime)

    def test_resource_requirements_methods(self):
        """Test methods of the ResourceRequirements entity."""
        resources = ResourceRequirements()

        # Test update_cpu_limits
        original_updated_at = resources.updated_at
        resources.update_cpu_limits("200m", "1000m")
        assert resources.cpu_min == "200m"
        assert resources.cpu_max == "1000m"
        assert resources.updated_at > original_updated_at

        # Test update_memory_limits
        original_updated_at = resources.updated_at
        resources.update_memory_limits("512Mi", "1Gi")
        assert resources.memory_min == "512Mi"
        assert resources.memory_max == "1Gi"
        assert resources.updated_at > original_updated_at

        # Test update_replica_count
        original_updated_at = resources.updated_at
        resources.update_replica_count(2, 5)
        assert resources.replicas_min == 2
        assert resources.replicas_max == 5
        assert resources.updated_at > original_updated_at

        # Test enable_auto_scaling
        original_updated_at = resources.updated_at
        resources.enable_auto_scaling(90)
        assert resources.auto_scaling is True
        assert resources.auto_scaling_cpu_threshold == 90
        assert resources.updated_at > original_updated_at

        # Test disable_auto_scaling
        original_updated_at = resources.updated_at
        resources.disable_auto_scaling()
        assert resources.auto_scaling is False
        assert resources.updated_at > original_updated_at

    def test_network_config_creation(self):
        """Test creation of a NetworkConfig entity."""
        network = NetworkConfig(
            domain="example.com",
            use_https=True,
            use_hsts=True,
            ingress_annotations={"nginx.ingress.kubernetes.io/ssl-redirect": "true"},
            cors_allowed_origins=["https://app.example.com"],
            rate_limiting=True,
            rate_limit_requests=100
        )

        assert network.domain == "example.com"
        assert network.use_https is True
        assert network.use_hsts is True
        assert "nginx.ingress.kubernetes.io/ssl-redirect" in network.ingress_annotations
        assert "https://app.example.com" in network.cors_allowed_origins
        assert network.rate_limiting is True
        assert network.rate_limit_requests == 100
        assert isinstance(network.created_at, datetime)
        assert isinstance(network.updated_at, datetime)

    def test_network_config_methods(self):
        """Test methods of the NetworkConfig entity."""
        network = NetworkConfig()

        # Test set_domain
        original_updated_at = network.updated_at
        network.set_domain("test.example.com")
        assert network.domain == "test.example.com"
        assert network.updated_at > original_updated_at

        # Test enable_https
        original_updated_at = network.updated_at
        network.disable_https()  # First disable to test enabling
        network.enable_https()
        assert network.use_https is True
        assert network.updated_at > original_updated_at

        # Test disable_https
        original_updated_at = network.updated_at
        network.disable_https()
        assert network.use_https is False
        assert network.updated_at > original_updated_at

        # Test add_cors_origin
        original_updated_at = network.updated_at
        network.add_cors_origin("https://api.example.com")
        assert "https://api.example.com" in network.cors_allowed_origins
        assert network.updated_at > original_updated_at

        # Test remove_cors_origin
        original_updated_at = network.updated_at
        network.add_cors_origin("https://temp.example.com")
        network.remove_cors_origin("https://temp.example.com")
        assert "https://temp.example.com" not in network.cors_allowed_origins
        assert network.updated_at > original_updated_at

        # Test add_ingress_annotation
        original_updated_at = network.updated_at
        network.add_ingress_annotation("key", "value")
        assert network.ingress_annotations["key"] == "value"
        assert network.updated_at > original_updated_at

        # Test remove_ingress_annotation
        original_updated_at = network.updated_at
        network.remove_ingress_annotation("key")
        assert "key" not in network.ingress_annotations
        assert network.updated_at > original_updated_at

        # Test enable_rate_limiting
        original_updated_at = network.updated_at
        network.enable_rate_limiting(200)
        assert network.rate_limiting is True
        assert network.rate_limit_requests == 200
        assert network.updated_at > original_updated_at

        # Test disable_rate_limiting
        original_updated_at = network.updated_at
        network.disable_rate_limiting()
        assert network.rate_limiting is False
        assert network.updated_at > original_updated_at

    def test_security_config_creation(self):
        """Test creation of a SecurityConfig entity."""
        security = SecurityConfig(
            enable_network_policy=True,
            pod_security_policy="restricted",
            scan_images=True,
            scan_dependencies=True,
            enable_secrets_encryption=True,
            secrets_provider="vault"
        )

        assert security.enable_network_policy is True
        assert security.pod_security_policy == "restricted"
        assert security.scan_images is True
        assert security.scan_dependencies is True
        assert security.enable_secrets_encryption is True
        assert security.secrets_provider == "vault"
        assert isinstance(security.created_at, datetime)
        assert isinstance(security.updated_at, datetime)

    def test_security_config_methods(self):
        """Test methods of the SecurityConfig entity."""
        security = SecurityConfig()

        # Test enable_network_policies
        original_updated_at = security.updated_at
        security.disable_network_policies()  # First disable to test enabling
        security.enable_network_policies()
        assert security.enable_network_policy is True
        assert security.updated_at > original_updated_at

        # Test disable_network_policies
        original_updated_at = security.updated_at
        security.disable_network_policies()
        assert security.enable_network_policy is False
        assert security.updated_at > original_updated_at

        # Test set_pod_security_policy
        original_updated_at = security.updated_at
        security.set_pod_security_policy("privileged")
        assert security.pod_security_policy == "privileged"
        assert security.updated_at > original_updated_at

        # Test enable_image_scanning
        original_updated_at = security.updated_at
        security.disable_image_scanning()  # First disable to test enabling
        security.enable_image_scanning()
        assert security.scan_images is True
        assert security.updated_at > original_updated_at

        # Test disable_image_scanning
        original_updated_at = security.updated_at
        security.disable_image_scanning()
        assert security.scan_images is False
        assert security.updated_at > original_updated_at

        # Test enable_dependency_scanning
        original_updated_at = security.updated_at
        security.disable_dependency_scanning()  # First disable to test enabling
        security.enable_dependency_scanning()
        assert security.scan_dependencies is True
        assert security.updated_at > original_updated_at

        # Test disable_dependency_scanning
        original_updated_at = security.updated_at
        security.disable_dependency_scanning()
        assert security.scan_dependencies is False
        assert security.updated_at > original_updated_at

        # Test enable_secrets_encryption
        original_updated_at = security.updated_at
        security.disable_secrets_encryption()  # First disable to test enabling
        security.enable_secrets_encryption("aws")
        assert security.enable_secrets_encryption is True
        assert security.secrets_provider == "aws"
        assert security.updated_at > original_updated_at

        # Test disable_secrets_encryption
        original_updated_at = security.updated_at
        security.disable_secrets_encryption()
        assert security.enable_secrets_encryption is False
        assert security.updated_at > original_updated_at

    def test_monitoring_config_creation(self):
        """Test creation of a MonitoringConfig entity."""
        monitoring = MonitoringConfig(
            enable_logging=True,
            enable_metrics=True,
            enable_tracing=True,
            log_level="INFO",
            retention_days=30,
            alerting=True,
            alert_channels=["email", "slack"]
        )

        assert monitoring.enable_logging is True
        assert monitoring.enable_metrics is True
        assert monitoring.enable_tracing is True
        assert monitoring.log_level == "INFO"
        assert monitoring.retention_days == 30
        assert monitoring.alerting is True
        assert "email" in monitoring.alert_channels
        assert "slack" in monitoring.alert_channels
        assert isinstance(monitoring.created_at, datetime)
        assert isinstance(monitoring.updated_at, datetime)

    def test_monitoring_config_methods(self):
        """Test methods of the MonitoringConfig entity."""
        monitoring = MonitoringConfig()

        # Test enable_logging
        original_updated_at = monitoring.updated_at
        monitoring.disable_logging()  # First disable to test enabling
        monitoring.enable_logging("DEBUG")
        assert monitoring.enable_logging is True
        assert monitoring.log_level == "DEBUG"
        assert monitoring.updated_at > original_updated_at

        # Test disable_logging
        original_updated_at = monitoring.updated_at
        monitoring.disable_logging()
        assert monitoring.enable_logging is False
        assert monitoring.updated_at > original_updated_at

        # Test enable_metrics_collection
        original_updated_at = monitoring.updated_at
        monitoring.disable_metrics_collection()  # First disable to test enabling
        monitoring.enable_metrics_collection()
        assert monitoring.enable_metrics is True
        assert monitoring.updated_at > original_updated_at

        # Test disable_metrics_collection
        original_updated_at = monitoring.updated_at
        monitoring.disable_metrics_collection()
        assert monitoring.enable_metrics is False
        assert monitoring.updated_at > original_updated_at

        # Test enable_distributed_tracing
        original_updated_at = monitoring.updated_at
        monitoring.disable_distributed_tracing()  # First disable to test enabling
        monitoring.enable_distributed_tracing()
        assert monitoring.enable_tracing is True
        assert monitoring.updated_at > original_updated_at

        # Test disable_distributed_tracing
        original_updated_at = monitoring.updated_at
        monitoring.disable_distributed_tracing()
        assert monitoring.enable_tracing is False
        assert monitoring.updated_at > original_updated_at

        # Test set_log_retention
        original_updated_at = monitoring.updated_at
        monitoring.set_log_retention(60)
        assert monitoring.retention_days == 60
        assert monitoring.updated_at > original_updated_at

        # Test enable_alerting
        original_updated_at = monitoring.updated_at
        monitoring.disable_alerting()  # First disable to test enabling
        monitoring.enable_alerting()
        assert monitoring.alerting is True
        assert monitoring.updated_at > original_updated_at

        # Test disable_alerting
        original_updated_at = monitoring.updated_at
        monitoring.disable_alerting()
        assert monitoring.alerting is False
        assert monitoring.updated_at > original_updated_at

        # Test add_alert_channel
        original_updated_at = monitoring.updated_at
        monitoring.add_alert_channel("pagerduty")
        assert "pagerduty" in monitoring.alert_channels
        assert monitoring.updated_at > original_updated_at

        # Test remove_alert_channel
        original_updated_at = monitoring.updated_at
        monitoring.add_alert_channel("temp")
        monitoring.remove_alert_channel("temp")
        assert "temp" not in monitoring.alert_channels
        assert monitoring.updated_at > original_updated_at

    def test_testing_config_creation(self):
        """Test creation of a TestingConfig entity."""
        testing = TestingConfig(
            run_unit_tests=True,
            run_integration_tests=True,
            run_performance_tests=False,
            run_security_tests=True,
            fail_on_test_failure=True,
            test_coverage_threshold=80
        )

        assert testing.run_unit_tests is True
        assert testing.run_integration_tests is True
        assert testing.run_performance_tests is False
        assert testing.run_security_tests is True
        assert testing.fail_on_test_failure is True
        assert testing.test_coverage_threshold == 80
        assert isinstance(testing.created_at, datetime)
        assert isinstance(testing.updated_at, datetime)

    def test_testing_config_methods(self):
        """Test methods of the TestingConfig entity."""
        testing = TestingConfig()

        # Test enable_unit_tests
        original_updated_at = testing.updated_at
        testing.disable_unit_tests()  # First disable to test enabling
        testing.enable_unit_tests()
        assert testing.run_unit_tests is True
        assert testing.updated_at > original_updated_at

        # Test disable_unit_tests
        original_updated_at = testing.updated_at
        testing.disable_unit_tests()
        assert testing.run_unit_tests is False
        assert testing.updated_at > original_updated_at

        # Test enable_integration_tests
        original_updated_at = testing.updated_at
        testing.disable_integration_tests()  # First disable to test enabling
        testing.enable_integration_tests()
        assert testing.run_integration_tests is True
        assert testing.updated_at > original_updated_at

        # Test disable_integration_tests
        original_updated_at = testing.updated_at
        testing.disable_integration_tests()
        assert testing.run_integration_tests is False
        assert testing.updated_at > original_updated_at

        # Test enable_performance_tests
        original_updated_at = testing.updated_at
        testing.disable_performance_tests()  # First disable to test enabling
        testing.enable_performance_tests()
        assert testing.run_performance_tests is True
        assert testing.updated_at > original_updated_at

        # Test disable_performance_tests
        original_updated_at = testing.updated_at
        testing.disable_performance_tests()
        assert testing.run_performance_tests is False
        assert testing.updated_at > original_updated_at

        # Test enable_security_tests
        original_updated_at = testing.updated_at
        testing.disable_security_tests()  # First disable to test enabling
        testing.enable_security_tests()
        assert testing.run_security_tests is True
        assert testing.updated_at > original_updated_at

        # Test disable_security_tests
        original_updated_at = testing.updated_at
        testing.disable_security_tests()
        assert testing.run_security_tests is False
        assert testing.updated_at > original_updated_at

        # Test set_fail_on_test_failure
        original_updated_at = testing.updated_at
        testing.set_fail_on_test_failure(False)
        assert testing.fail_on_test_failure is False
        assert testing.updated_at > original_updated_at

        # Test set_coverage_threshold
        original_updated_at = testing.updated_at
        testing.set_coverage_threshold(90)
        assert testing.test_coverage_threshold == 90
        assert testing.updated_at > original_updated_at

    def test_task_creation(self):
        """Test creation of a Task entity."""
        task_id = TaskId(value=str(uuid.uuid4()))
        task = Task(
            id=task_id,
            name="test-task",
            description="A test task",
            status=TaskStatus.PENDING,
            dependencies=[],
            skip_on_failure=False,
            timeout=None
        )

        assert task.id == task_id
        assert task.name == "test-task"
        assert task.description == "A test task"
        assert task.status == TaskStatus.PENDING
        assert len(task.dependencies) == 0
        assert task.skip_on_failure is False
        assert task.timeout is None
        assert task.started_at is None
        assert task.completed_at is None
        assert task.result is None
        assert task.error is None
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_methods(self):
        """Test methods of the Task entity."""
        task_id = TaskId(value=str(uuid.uuid4()))
        dependency_id = TaskId(value=str(uuid.uuid4()))
        task = Task(id=task_id, name="test-task", description="A test task")

        # Test start
        original_updated_at = task.updated_at
        task.start()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        assert task.updated_at > original_updated_at

        # Test succeed
        original_updated_at = task.updated_at
        result = {"status": "ok"}
        task.succeed(result)
        assert task.status == TaskStatus.SUCCEEDED
        assert task.completed_at is not None
        assert task.result == result
        assert task.updated_at > original_updated_at

        # Create a new task for testing fail
        task = Task(id=TaskId(value=str(uuid.uuid4())), name="fail-task", description="A task that fails")
        task.start()

        # Test fail
        original_updated_at = task.updated_at
        error_message = "Task failed"
        task.fail(error_message)
        assert task.status == TaskStatus.FAILED
        assert task.completed_at is not None
        assert task.error == error_message
        assert task.updated_at > original_updated_at

        # Create a new task for testing skip
        task = Task(id=TaskId(value=str(uuid.uuid4())), name="skip-task", description="A task to skip")

        # Test skip
        original_updated_at = task.updated_at
        task.skip()
        assert task.status == TaskStatus.SKIPPED
        assert task.updated_at > original_updated_at

        # Create a new task for testing dependencies
        task = Task(id=TaskId(value=str(uuid.uuid4())), name="dep-task", description="A task with dependencies")

        # Test add_dependency
        original_updated_at = task.updated_at
        task.add_dependency(dependency_id)
        assert dependency_id in task.dependencies
        assert task.updated_at > original_updated_at

        # Test remove_dependency
        original_updated_at = task.updated_at
        task.remove_dependency(dependency_id)
        assert dependency_id not in task.dependencies
        assert task.updated_at > original_updated_at

        # Test set_timeout
        original_updated_at = task.updated_at
        task.set_timeout(300)
        assert task.timeout == 300
        assert task.updated_at > original_updated_at

        # Test set_skip_on_failure
        original_updated_at = task.updated_at
        task.set_skip_on_failure(True)
        assert task.skip_on_failure is True
        assert task.updated_at > original_updated_at

        # Test duration (with completed task)
        task = Task(id=TaskId(value=str(uuid.uuid4())), name="duration-task", description="A task for duration test")
        task.start()
        task.succeed()
        assert task.duration is not None
        assert task.duration >= 0

        # Test is_completed
        assert task.is_completed is True

        # Test with a pending task
        task = Task(id=TaskId(value=str(uuid.uuid4())), name="pending-task", description="A pending task")
        assert task.is_completed is False
        assert task.duration is None

    def test_stage_creation(self):
        """Test creation of a Stage entity."""
        stage_id = StageId(value=str(uuid.uuid4()))
        stage = Stage(
            id=stage_id,
            name="test-stage",
            description="A test stage",
            status=StageStatus.PENDING,
            fail_fast=True,
            tasks=[],
            dependencies=[]
        )

        assert stage.id == stage_id
        assert stage.name == "test-stage"
        assert stage.description == "A test stage"
        assert stage.status == StageStatus.PENDING
        assert stage.fail_fast is True
        assert len(stage.tasks) == 0
        assert len(stage.dependencies) == 0
        assert stage.started_at is None
        assert stage.completed_at is None
        assert isinstance(stage.created_at, datetime)
        assert isinstance(stage.updated_at, datetime)

    def test_stage_methods(self):
        """Test methods of the Stage entity."""
        stage_id = StageId(value=str(uuid.uuid4()))
        dependency_id = StageId(value=str(uuid.uuid4()))
        task_id = TaskId(value=str(uuid.uuid4()))
        
        stage = Stage(id=stage_id, name="test-stage", description="A test stage")
        
        # Create a task to add to the stage
        task = Task(id=task_id, name="test-task", description="A task in the stage")

        # Test add_task
        original_updated_at = stage.updated_at
        stage.add_task(task)
        assert len(stage.tasks) == 1
        assert stage.tasks[0].id == task_id
        assert stage.updated_at > original_updated_at

        # Test remove_task
        original_updated_at = stage.updated_at
        stage.remove_task(task_id)
        assert len(stage.tasks) == 0
        assert stage.updated_at > original_updated_at

        # Test start
        original_updated_at = stage.updated_at
        stage.start()
        assert stage.status == StageStatus.RUNNING
        assert stage.started_at is not None
        assert stage.updated_at > original_updated_at

        # Test succeed
        original_updated_at = stage.updated_at
        stage.succeed()
        assert stage.status == StageStatus.SUCCEEDED
        assert stage.completed_at is not None
        assert stage.updated_at > original_updated_at

        # Create a new stage for testing fail
        stage = Stage(id=StageId(value=str(uuid.uuid4())), name="fail-stage", description="A stage that fails")
        stage.start()

        # Test fail
        original_updated_at = stage.updated_at
        stage.fail()
        assert stage.status == StageStatus.FAILED
        assert stage.completed_at is not None
        assert stage.updated_at > original_updated_at

        # Create a new stage for testing skip
        stage = Stage(id=StageId(value=str(uuid.uuid4())), name="skip-stage", description="A stage to skip")

        # Test skip
        original_updated_at = stage.updated_at
        stage.skip()
        assert stage.status == StageStatus.SKIPPED
        assert stage.updated_at > original_updated_at

        # Create a new stage for testing dependencies
        stage = Stage(id=StageId(value=str(uuid.uuid4())), name="dep-stage", description="A stage with dependencies")

        # Test add_dependency
        original_updated_at = stage.updated_at
        stage.add_dependency(dependency_id)
        assert dependency_id in stage.dependencies
        assert stage.updated_at > original_updated_at

        # Test remove_dependency
        original_updated_at = stage.updated_at
        stage.remove_dependency(dependency_id)
        assert dependency_id not in stage.dependencies
        assert stage.updated_at > original_updated_at

        # Test set_fail_fast
        original_updated_at = stage.updated_at
        stage.set_fail_fast(False)
        assert stage.fail_fast is False
        assert stage.updated_at > original_updated_at

        # Test with a successful task and a failed task
        stage = Stage(id=StageId(value=str(uuid.uuid4())), name="multi-task-stage", description="A stage with multiple tasks")
        
        successful_task = Task(id=TaskId(value=str(uuid.uuid4())), name="success-task", description="A successful task")
        successful_task.start()
        successful_task.succeed()
        
        failed_task = Task(id=TaskId(value=str(uuid.uuid4())), name="failed-task", description="A failed task")
        failed_task.start()
        failed_task.fail("Error")
        
        stage.add_task(successful_task)
        stage.add_task(failed_task)
        
        # Test has_failed_tasks
        assert stage.has_failed_tasks is True
        
        # Test success_percentage
        assert stage.success_percentage == 50.0

        # Test with completed stage
        stage.start()
        stage.succeed()
        assert stage.duration is not None
        assert stage.duration >= 0

        # Test is_completed
        assert stage.is_completed is True

        # Test with a pending stage
        stage = Stage(id=StageId(value=str(uuid.uuid4())), name="pending-stage", description="A pending stage")
        assert stage.is_completed is False
        assert stage.duration is None

    def test_pipeline_creation(self):
        """Test creation of a Pipeline entity."""
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING,
            context={}
        )

        assert pipeline.id == pipeline_id
        assert pipeline.name == "test-pipeline"
        assert pipeline.description == "A test pipeline"
        assert len(pipeline.stages) == 0
        assert pipeline.status == DeploymentStatus.PENDING
        assert pipeline.started_at is None
        assert pipeline.completed_at is None
        assert len(pipeline.context) == 0
        assert isinstance(pipeline.created_at, datetime)
        assert isinstance(pipeline.updated_at, datetime)

    def test_pipeline_methods(self):
        """Test methods of the Pipeline entity."""
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        stage_id = StageId(value=str(uuid.uuid4()))
        
        pipeline = Pipeline(id=pipeline_id, name="test-pipeline", description="A test pipeline")
        
        # Create a stage to add to the pipeline
        stage = Stage(id=stage_id, name="test-stage", description="A stage in the pipeline")

        # Test add_stage
        original_updated_at = pipeline.updated_at
        pipeline.add_stage(stage)
        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].id == stage_id
        assert pipeline.updated_at > original_updated_at

        # Test remove_stage
        original_updated_at = pipeline.updated_at
        pipeline.remove_stage(stage_id)
        assert len(pipeline.stages) == 0
        assert pipeline.updated_at > original_updated_at

        # Test start
        original_updated_at = pipeline.updated_at
        pipeline.start()
        assert pipeline.status == DeploymentStatus.RUNNING
        assert pipeline.started_at is not None
        assert pipeline.updated_at > original_updated_at

        # Test succeed
        original_updated_at = pipeline.updated_at
        pipeline.succeed()
        assert pipeline.status == DeploymentStatus.SUCCEEDED
        assert pipeline.completed_at is not None
        assert pipeline.updated_at > original_updated_at

        # Create a new pipeline for testing fail
        pipeline = Pipeline(id=PipelineId(value=str(uuid.uuid4())), name="fail-pipeline", description="A pipeline that fails")
        pipeline.start()

        # Test fail
        original_updated_at = pipeline.updated_at
        pipeline.fail()
        assert pipeline.status == DeploymentStatus.FAILED
        assert pipeline.completed_at is not None
        assert pipeline.updated_at > original_updated_at

        # Create a new pipeline for testing cancel
        pipeline = Pipeline(id=PipelineId(value=str(uuid.uuid4())), name="cancel-pipeline", description="A pipeline to cancel")
        pipeline.start()

        # Test cancel
        original_updated_at = pipeline.updated_at
        pipeline.cancel()
        assert pipeline.status == DeploymentStatus.CANCELED
        assert pipeline.completed_at is not None
        assert pipeline.updated_at > original_updated_at

        # Create a new pipeline for testing rollback
        pipeline = Pipeline(id=PipelineId(value=str(uuid.uuid4())), name="rollback-pipeline", description="A pipeline to roll back")
        pipeline.start()
        pipeline.succeed()

        # Test start_rollback
        original_updated_at = pipeline.updated_at
        pipeline.start_rollback()
        assert pipeline.status == DeploymentStatus.ROLLING_BACK
        assert pipeline.updated_at > original_updated_at

        # Test complete_rollback
        original_updated_at = pipeline.updated_at
        pipeline.complete_rollback()
        assert pipeline.status == DeploymentStatus.ROLLED_BACK
        assert pipeline.completed_at is not None
        assert pipeline.updated_at > original_updated_at

        # Create a new pipeline for testing context operations
        pipeline = Pipeline(id=PipelineId(value=str(uuid.uuid4())), name="context-pipeline", description="A pipeline for context tests")

        # Test add_context
        original_updated_at = pipeline.updated_at
        pipeline.add_context("key", "value")
        assert pipeline.context["key"] == "value"
        assert pipeline.updated_at > original_updated_at

        # Test get_context
        assert pipeline.get_context("key") == "value"
        assert pipeline.get_context("nonexistent", "default") == "default"

        # Test clear_context
        original_updated_at = pipeline.updated_at
        pipeline.clear_context()
        assert len(pipeline.context) == 0
        assert pipeline.updated_at > original_updated_at

        # Test with a running stage
        pipeline = Pipeline(id=PipelineId(value=str(uuid.uuid4())), name="multi-stage-pipeline", description="A pipeline with multiple stages")
        
        successful_stage = Stage(id=StageId(value=str(uuid.uuid4())), name="success-stage", description="A successful stage")
        successful_stage.start()
        successful_stage.succeed()
        
        failed_stage = Stage(id=StageId(value=str(uuid.uuid4())), name="failed-stage", description="A failed stage")
        failed_stage.start()
        failed_stage.fail()
        
        running_stage = Stage(id=StageId(value=str(uuid.uuid4())), name="running-stage", description="A running stage")
        running_stage.start()
        
        pipeline.add_stage(successful_stage)
        pipeline.add_stage(failed_stage)
        pipeline.add_stage(running_stage)
        
        # Test has_failed_stages
        assert pipeline.has_failed_stages is True
        
        # Test success_percentage
        assert pipeline.success_percentage == 50.0
        
        # Test current_stage
        assert pipeline.current_stage == running_stage

        # Test with completed pipeline
        pipeline = Pipeline(id=PipelineId(value=str(uuid.uuid4())), name="complete-pipeline", description="A completed pipeline")
        pipeline.start()
        pipeline.succeed()
        assert pipeline.duration is not None
        assert pipeline.duration >= 0

        # Test is_completed
        assert pipeline.is_completed is True

        # Test with a pending pipeline
        pipeline = Pipeline(id=PipelineId(value=str(uuid.uuid4())), name="pending-pipeline", description="A pending pipeline")
        assert pipeline.is_completed is False
        assert pipeline.duration is None

    def test_deployment_config_creation(self):
        """Test creation of a DeploymentConfig entity."""
        # Create the required component configs
        db_config = DatabaseConfig(
            host="localhost",
            name="testdb",
            user="testuser"
        )
        
        resources = ResourceRequirements()
        network = NetworkConfig()
        security = SecurityConfig()
        monitoring = MonitoringConfig()
        testing = TestingConfig()
        
        # Create the deployment config
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        config = DeploymentConfig(
            id=deployment_id,
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=db_config,
            resources=resources,
            network=network,
            security=security,
            monitoring=monitoring,
            testing=testing,
            custom_settings={"key": "value"},
            environment_variables={"ENV": "dev"},
            secrets=["secret1"],
            config_files=["config.json"]
        )

        assert config.id == deployment_id
        assert config.app_name == "test-app"
        assert config.app_version == "1.0.0"
        assert config.environment == DeploymentEnvironment.DEV
        assert config.platform == DeploymentPlatform.KUBERNETES
        assert config.strategy == DeploymentStrategy.ROLLING
        assert config.database == db_config
        assert config.resources == resources
        assert config.network == network
        assert config.security == security
        assert config.monitoring == monitoring
        assert config.testing == testing
        assert config.custom_settings["key"] == "value"
        assert config.environment_variables["ENV"] == "dev"
        assert "secret1" in config.secrets
        assert "config.json" in config.config_files
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)

    def test_deployment_config_methods(self):
        """Test methods of the DeploymentConfig entity."""
        # Create the required component configs
        db_config = DatabaseConfig(
            host="localhost",
            name="testdb",
            user="testuser"
        )
        
        resources = ResourceRequirements()
        network = NetworkConfig()
        security = SecurityConfig()
        monitoring = MonitoringConfig()
        testing = TestingConfig()
        
        # Create the deployment config
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        config = DeploymentConfig(
            id=deployment_id,
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=db_config,
            resources=resources,
            network=network,
            security=security,
            monitoring=monitoring,
            testing=testing
        )

        # Test set_environment
        original_updated_at = config.updated_at
        config.set_environment(DeploymentEnvironment.TEST)
        assert config.environment == DeploymentEnvironment.TEST
        assert config.updated_at > original_updated_at

        # Test set_platform
        original_updated_at = config.updated_at
        config.set_platform(DeploymentPlatform.AWS)
        assert config.platform == DeploymentPlatform.AWS
        assert config.updated_at > original_updated_at

        # Test set_strategy
        original_updated_at = config.updated_at
        config.set_strategy(DeploymentStrategy.BLUE_GREEN)
        assert config.strategy == DeploymentStrategy.BLUE_GREEN
        assert config.updated_at > original_updated_at

        # Test add_environment_variable
        original_updated_at = config.updated_at
        config.add_environment_variable("KEY", "value")
        assert config.environment_variables["KEY"] == "value"
        assert config.updated_at > original_updated_at

        # Test remove_environment_variable
        original_updated_at = config.updated_at
        config.remove_environment_variable("KEY")
        assert "KEY" not in config.environment_variables
        assert config.updated_at > original_updated_at

        # Test add_secret
        original_updated_at = config.updated_at
        config.add_secret("api-key")
        assert "api-key" in config.secrets
        assert config.updated_at > original_updated_at

        # Test remove_secret
        original_updated_at = config.updated_at
        config.remove_secret("api-key")
        assert "api-key" not in config.secrets
        assert config.updated_at > original_updated_at

        # Test add_config_file
        original_updated_at = config.updated_at
        config.add_config_file("settings.json")
        assert "settings.json" in config.config_files
        assert config.updated_at > original_updated_at

        # Test remove_config_file
        original_updated_at = config.updated_at
        config.remove_config_file("settings.json")
        assert "settings.json" not in config.config_files
        assert config.updated_at > original_updated_at

        # Test add_custom_setting
        original_updated_at = config.updated_at
        config.add_custom_setting("feature-flag", True)
        assert config.custom_settings["feature-flag"] is True
        assert config.updated_at > original_updated_at

        # Test remove_custom_setting
        original_updated_at = config.updated_at
        config.remove_custom_setting("feature-flag")
        assert "feature-flag" not in config.custom_settings
        assert config.updated_at > original_updated_at

        # Test for_environment
        production_config = config.for_environment(DeploymentEnvironment.PRODUCTION)
        assert production_config.environment == DeploymentEnvironment.PRODUCTION
        assert production_config.id != config.id  # Should have a new ID
        assert production_config.app_name == config.app_name
        assert production_config.app_version == config.app_version
        assert production_config.strategy == DeploymentStrategy.BLUE_GREEN  # Should be updated for production
        
        staging_config = config.for_environment(DeploymentEnvironment.STAGING)
        assert staging_config.environment == DeploymentEnvironment.STAGING
        assert staging_config.id != config.id  # Should have a new ID
        
        test_config = config.for_environment(DeploymentEnvironment.TEST)
        assert test_config.environment == DeploymentEnvironment.TEST
        assert test_config.id != config.id  # Should have a new ID
        
        dev_config = config.for_environment(DeploymentEnvironment.DEV)
        assert dev_config.environment == DeploymentEnvironment.DEV
        assert dev_config.id != config.id  # Should have a new ID

    def test_deployment_result_creation(self):
        """Test creation of a DeploymentResult entity."""
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        
        result = DeploymentResult(
            deployment_id=deployment_id,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={"duration": 120, "stages": 5}
        )

        assert result.deployment_id == deployment_id
        assert result.success is True
        assert result.message == "Deployment succeeded"
        assert result.status == DeploymentStatus.SUCCEEDED
        assert result.details["duration"] == 120
        assert result.details["stages"] == 5
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.id, str)

    def test_deployment_result_methods(self):
        """Test methods of the DeploymentResult entity."""
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        
        result = DeploymentResult(
            deployment_id=deployment_id,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={}
        )

        # Test add_detail
        result.add_detail("logs_url", "https://example.com/logs")
        assert result.details["logs_url"] == "https://example.com/logs"