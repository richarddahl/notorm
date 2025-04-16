"""
Domain entities for the Deployment module.

This module defines the core domain entities for the Deployment module,
providing a rich domain model for deployment management.
"""

from datetime import datetime, timezone, UTC
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union, Callable

from pydantic import BaseModel

from uno.domain.core import Entity, AggregateRoot, ValueObject


@dataclass(frozen=True)
class DeploymentId(ValueObject):
    """Identifier for a deployment."""
    value: str


@dataclass(frozen=True)
class TaskId(ValueObject):
    """Identifier for a deployment task."""
    value: str


@dataclass(frozen=True)
class StageId(ValueObject):
    """Identifier for a deployment stage."""
    value: str


@dataclass(frozen=True)
class PipelineId(ValueObject):
    """Identifier for a deployment pipeline."""
    value: str


@dataclass(frozen=True)
class StrategyId(ValueObject):
    """Identifier for a deployment strategy."""
    value: str


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


class DeploymentStrategy(str, Enum):
    """Deployment strategy types."""

    BLUE_GREEN = "blue-green"
    ROLLING = "rolling"
    CANARY = "canary"
    RECREATE = "recreate"


class TaskStatus(str, Enum):
    """Status of a deployment task."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageStatus(str, Enum):
    """Status of a deployment stage."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class DeploymentStatus(str, Enum):
    """Status of a deployment."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    ROLLING_BACK = "rolling-back"
    ROLLED_BACK = "rolled-back"


@dataclass
class DatabaseConfig(Entity):
    """Database configuration for deployment."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    host: str
    port: int = 5432
    name: str
    user: str
    password_env_var: str = "DB_PASSWORD"
    ssl_mode: Optional[str] = None
    connection_pool_min: int = 5
    connection_pool_max: int = 20
    apply_migrations: bool = True
    backup_before_deploy: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_connection_pool_size(self, min_size: int, max_size: int) -> None:
        """
        Update the connection pool size settings.
        
        Args:
            min_size: Minimum connection pool size
            max_size: Maximum connection pool size
        """
        self.connection_pool_min = min_size
        self.connection_pool_max = max_size
        self.updated_at = datetime.now(UTC)

    def disable_migrations(self) -> None:
        """Disable applying migrations during deployment."""
        self.apply_migrations = False
        self.updated_at = datetime.now(UTC)

    def enable_migrations(self) -> None:
        """Enable applying migrations during deployment."""
        self.apply_migrations = True
        self.updated_at = datetime.now(UTC)

    def disable_backup(self) -> None:
        """Disable database backup before deployment."""
        self.backup_before_deploy = False
        self.updated_at = datetime.now(UTC)

    def enable_backup(self) -> None:
        """Enable database backup before deployment."""
        self.backup_before_deploy = True
        self.updated_at = datetime.now(UTC)


@dataclass
class ResourceRequirements(Entity):
    """Resource requirements for deployment."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cpu_min: str = "100m"
    cpu_max: str = "500m"
    memory_min: str = "256Mi"
    memory_max: str = "512Mi"
    replicas_min: int = 1
    replicas_max: int = 3
    auto_scaling: bool = True
    auto_scaling_cpu_threshold: int = 80
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_cpu_limits(self, min_cpu: str, max_cpu: str) -> None:
        """
        Update CPU limits.
        
        Args:
            min_cpu: Minimum CPU requirement
            max_cpu: Maximum CPU requirement
        """
        self.cpu_min = min_cpu
        self.cpu_max = max_cpu
        self.updated_at = datetime.now(UTC)

    def update_memory_limits(self, min_memory: str, max_memory: str) -> None:
        """
        Update memory limits.
        
        Args:
            min_memory: Minimum memory requirement
            max_memory: Maximum memory requirement
        """
        self.memory_min = min_memory
        self.memory_max = max_memory
        self.updated_at = datetime.now(UTC)

    def update_replica_count(self, min_replicas: int, max_replicas: int) -> None:
        """
        Update replica count.
        
        Args:
            min_replicas: Minimum number of replicas
            max_replicas: Maximum number of replicas
        """
        self.replicas_min = min_replicas
        self.replicas_max = max_replicas
        self.updated_at = datetime.now(UTC)

    def enable_auto_scaling(self, cpu_threshold: int = 80) -> None:
        """
        Enable auto-scaling.
        
        Args:
            cpu_threshold: CPU utilization threshold for auto-scaling
        """
        self.auto_scaling = True
        self.auto_scaling_cpu_threshold = cpu_threshold
        self.updated_at = datetime.now(UTC)

    def disable_auto_scaling(self) -> None:
        """Disable auto-scaling."""
        self.auto_scaling = False
        self.updated_at = datetime.now(UTC)


@dataclass
class NetworkConfig(Entity):
    """Network configuration for deployment."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    domain: Optional[str] = None
    use_https: bool = True
    use_hsts: bool = True
    ingress_annotations: Dict[str, str] = field(default_factory=dict)
    cors_allowed_origins: List[str] = field(default_factory=list)
    rate_limiting: bool = False
    rate_limit_requests: int = 100
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def set_domain(self, domain: str) -> None:
        """
        Set the domain name.
        
        Args:
            domain: Domain name
        """
        self.domain = domain
        self.updated_at = datetime.now(UTC)

    def enable_https(self) -> None:
        """Enable HTTPS."""
        self.use_https = True
        self.updated_at = datetime.now(UTC)

    def disable_https(self) -> None:
        """Disable HTTPS."""
        self.use_https = False
        self.updated_at = datetime.now(UTC)

    def add_cors_origin(self, origin: str) -> None:
        """
        Add a CORS allowed origin.
        
        Args:
            origin: CORS allowed origin
        """
        if origin not in self.cors_allowed_origins:
            self.cors_allowed_origins.append(origin)
            self.updated_at = datetime.now(UTC)

    def remove_cors_origin(self, origin: str) -> None:
        """
        Remove a CORS allowed origin.
        
        Args:
            origin: CORS allowed origin to remove
        """
        if origin in self.cors_allowed_origins:
            self.cors_allowed_origins.remove(origin)
            self.updated_at = datetime.now(UTC)

    def add_ingress_annotation(self, key: str, value: str) -> None:
        """
        Add an ingress annotation.
        
        Args:
            key: Annotation key
            value: Annotation value
        """
        self.ingress_annotations[key] = value
        self.updated_at = datetime.now(UTC)

    def remove_ingress_annotation(self, key: str) -> None:
        """
        Remove an ingress annotation.
        
        Args:
            key: Annotation key to remove
        """
        if key in self.ingress_annotations:
            del self.ingress_annotations[key]
            self.updated_at = datetime.now(UTC)

    def enable_rate_limiting(self, requests_per_minute: int = 100) -> None:
        """
        Enable rate limiting.
        
        Args:
            requests_per_minute: Rate limit requests per minute
        """
        self.rate_limiting = True
        self.rate_limit_requests = requests_per_minute
        self.updated_at = datetime.now(UTC)

    def disable_rate_limiting(self) -> None:
        """Disable rate limiting."""
        self.rate_limiting = False
        self.updated_at = datetime.now(UTC)


@dataclass
class SecurityConfig(Entity):
    """Security configuration for deployment."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enable_network_policy: bool = True
    pod_security_policy: str = "restricted"
    scan_images: bool = True
    scan_dependencies: bool = True
    enable_secrets_encryption: bool = True
    secrets_provider: str = "vault"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def enable_network_policies(self) -> None:
        """Enable network policies."""
        self.enable_network_policy = True
        self.updated_at = datetime.now(UTC)

    def disable_network_policies(self) -> None:
        """Disable network policies."""
        self.enable_network_policy = False
        self.updated_at = datetime.now(UTC)

    def set_pod_security_policy(self, policy: str) -> None:
        """
        Set the pod security policy.
        
        Args:
            policy: Pod security policy
        """
        self.pod_security_policy = policy
        self.updated_at = datetime.now(UTC)

    def enable_image_scanning(self) -> None:
        """Enable image scanning."""
        self.scan_images = True
        self.updated_at = datetime.now(UTC)

    def disable_image_scanning(self) -> None:
        """Disable image scanning."""
        self.scan_images = False
        self.updated_at = datetime.now(UTC)

    def enable_dependency_scanning(self) -> None:
        """Enable dependency scanning."""
        self.scan_dependencies = True
        self.updated_at = datetime.now(UTC)

    def disable_dependency_scanning(self) -> None:
        """Disable dependency scanning."""
        self.scan_dependencies = False
        self.updated_at = datetime.now(UTC)

    def enable_secrets_encryption(self, provider: str = "vault") -> None:
        """
        Enable secrets encryption.
        
        Args:
            provider: Secrets provider
        """
        self.enable_secrets_encryption = True
        self.secrets_provider = provider
        self.updated_at = datetime.now(UTC)

    def disable_secrets_encryption(self) -> None:
        """Disable secrets encryption."""
        self.enable_secrets_encryption = False
        self.updated_at = datetime.now(UTC)


@dataclass
class MonitoringConfig(Entity):
    """Monitoring configuration for deployment."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enable_logging: bool = True
    enable_metrics: bool = True
    enable_tracing: bool = True
    log_level: str = "INFO"
    retention_days: int = 30
    alerting: bool = True
    alert_channels: List[str] = field(default_factory=lambda: ["email"])
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def enable_logging(self, log_level: str = "INFO") -> None:
        """
        Enable logging.
        
        Args:
            log_level: Log level
        """
        self.enable_logging = True
        self.log_level = log_level
        self.updated_at = datetime.now(UTC)

    def disable_logging(self) -> None:
        """Disable logging."""
        self.enable_logging = False
        self.updated_at = datetime.now(UTC)

    def enable_metrics_collection(self) -> None:
        """Enable metrics collection."""
        self.enable_metrics = True
        self.updated_at = datetime.now(UTC)

    def disable_metrics_collection(self) -> None:
        """Disable metrics collection."""
        self.enable_metrics = False
        self.updated_at = datetime.now(UTC)

    def enable_distributed_tracing(self) -> None:
        """Enable distributed tracing."""
        self.enable_tracing = True
        self.updated_at = datetime.now(UTC)

    def disable_distributed_tracing(self) -> None:
        """Disable distributed tracing."""
        self.enable_tracing = False
        self.updated_at = datetime.now(UTC)

    def set_log_retention(self, days: int) -> None:
        """
        Set log retention days.
        
        Args:
            days: Log retention days
        """
        self.retention_days = days
        self.updated_at = datetime.now(UTC)

    def enable_alerting(self) -> None:
        """Enable alerting."""
        self.alerting = True
        self.updated_at = datetime.now(UTC)

    def disable_alerting(self) -> None:
        """Disable alerting."""
        self.alerting = False
        self.updated_at = datetime.now(UTC)

    def add_alert_channel(self, channel: str) -> None:
        """
        Add an alert channel.
        
        Args:
            channel: Alert channel
        """
        if channel not in self.alert_channels:
            self.alert_channels.append(channel)
            self.updated_at = datetime.now(UTC)

    def remove_alert_channel(self, channel: str) -> None:
        """
        Remove an alert channel.
        
        Args:
            channel: Alert channel to remove
        """
        if channel in self.alert_channels:
            self.alert_channels.remove(channel)
            self.updated_at = datetime.now(UTC)


@dataclass
class TestingConfig(Entity):
    """Testing configuration for deployment."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_unit_tests: bool = True
    run_integration_tests: bool = True
    run_performance_tests: bool = False
    run_security_tests: bool = True
    fail_on_test_failure: bool = True
    test_coverage_threshold: int = 80
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def enable_unit_tests(self) -> None:
        """Enable unit tests."""
        self.run_unit_tests = True
        self.updated_at = datetime.now(UTC)

    def disable_unit_tests(self) -> None:
        """Disable unit tests."""
        self.run_unit_tests = False
        self.updated_at = datetime.now(UTC)

    def enable_integration_tests(self) -> None:
        """Enable integration tests."""
        self.run_integration_tests = True
        self.updated_at = datetime.now(UTC)

    def disable_integration_tests(self) -> None:
        """Disable integration tests."""
        self.run_integration_tests = False
        self.updated_at = datetime.now(UTC)

    def enable_performance_tests(self) -> None:
        """Enable performance tests."""
        self.run_performance_tests = True
        self.updated_at = datetime.now(UTC)

    def disable_performance_tests(self) -> None:
        """Disable performance tests."""
        self.run_performance_tests = False
        self.updated_at = datetime.now(UTC)

    def enable_security_tests(self) -> None:
        """Enable security tests."""
        self.run_security_tests = True
        self.updated_at = datetime.now(UTC)

    def disable_security_tests(self) -> None:
        """Disable security tests."""
        self.run_security_tests = False
        self.updated_at = datetime.now(UTC)

    def set_fail_on_test_failure(self, fail: bool) -> None:
        """
        Set whether to fail deployment on test failure.
        
        Args:
            fail: Whether to fail on test failure
        """
        self.fail_on_test_failure = fail
        self.updated_at = datetime.now(UTC)

    def set_coverage_threshold(self, threshold: int) -> None:
        """
        Set test coverage threshold.
        
        Args:
            threshold: Test coverage threshold percentage
        """
        self.test_coverage_threshold = threshold
        self.updated_at = datetime.now(UTC)


@dataclass
class Task(Entity):
    """
    A task in a deployment pipeline.
    
    Each task represents a single unit of work in the deployment process.
    """

    id: TaskId
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[TaskId] = field(default_factory=list)
    skip_on_failure: bool = False
    timeout: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def start(self) -> None:
        """Start the task."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def succeed(self, result: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark the task as succeeded.
        
        Args:
            result: Task result data
        """
        self.status = TaskStatus.SUCCEEDED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.result = result

    def fail(self, error: str) -> None:
        """
        Mark the task as failed.
        
        Args:
            error: Error message
        """
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.error = error

    def skip(self) -> None:
        """Skip the task."""
        self.status = TaskStatus.SKIPPED
        self.updated_at = datetime.now(UTC)

    def add_dependency(self, task_id: TaskId) -> None:
        """
        Add a dependency task.
        
        Args:
            task_id: Task ID to depend on
        """
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.updated_at = datetime.now(UTC)

    def remove_dependency(self, task_id: TaskId) -> None:
        """
        Remove a dependency task.
        
        Args:
            task_id: Task ID to remove
        """
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.updated_at = datetime.now(UTC)

    def set_timeout(self, timeout: Optional[int]) -> None:
        """
        Set the task timeout.
        
        Args:
            timeout: Timeout in seconds, or None for no timeout
        """
        self.timeout = timeout
        self.updated_at = datetime.now(UTC)

    def set_skip_on_failure(self, skip: bool) -> None:
        """
        Set whether to skip dependent tasks on failure.
        
        Args:
            skip: Whether to skip dependent tasks on failure
        """
        self.skip_on_failure = skip
        self.updated_at = datetime.now(UTC)

    @property
    def duration(self) -> Optional[float]:
        """
        Get the task duration in seconds.
        
        Returns:
            Task duration in seconds, or None if task has not completed
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """
        Check if the task is completed.
        
        Returns:
            True if task is completed, False otherwise
        """
        return self.status in [TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.SKIPPED]


@dataclass
class Stage(Entity):
    """
    A stage in a deployment pipeline.
    
    Each stage represents a phase in the deployment process, such as
    preparation, building, deployment, or verification.
    """

    id: StageId
    name: str
    description: str
    status: StageStatus = StageStatus.PENDING
    fail_fast: bool = True
    tasks: List[Task] = field(default_factory=list)
    dependencies: List[StageId] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def add_task(self, task: Task) -> None:
        """
        Add a task to the stage.
        
        Args:
            task: The task to add
        """
        self.tasks.append(task)
        self.updated_at = datetime.now(UTC)

    def remove_task(self, task_id: TaskId) -> None:
        """
        Remove a task from the stage.
        
        Args:
            task_id: ID of the task to remove
        """
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self.updated_at = datetime.now(UTC)

    def start(self) -> None:
        """Start the stage."""
        self.status = StageStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def succeed(self) -> None:
        """Mark the stage as succeeded."""
        self.status = StageStatus.SUCCEEDED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def fail(self) -> None:
        """Mark the stage as failed."""
        self.status = StageStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def skip(self) -> None:
        """Skip the stage."""
        self.status = StageStatus.SKIPPED
        self.updated_at = datetime.now(UTC)

    def add_dependency(self, stage_id: StageId) -> None:
        """
        Add a dependency stage.
        
        Args:
            stage_id: Stage ID to depend on
        """
        if stage_id not in self.dependencies:
            self.dependencies.append(stage_id)
            self.updated_at = datetime.now(UTC)

    def remove_dependency(self, stage_id: StageId) -> None:
        """
        Remove a dependency stage.
        
        Args:
            stage_id: Stage ID to remove
        """
        if stage_id in self.dependencies:
            self.dependencies.remove(stage_id)
            self.updated_at = datetime.now(UTC)

    def set_fail_fast(self, fail_fast: bool) -> None:
        """
        Set whether to fail fast on task failure.
        
        Args:
            fail_fast: Whether to fail fast
        """
        self.fail_fast = fail_fast
        self.updated_at = datetime.now(UTC)

    @property
    def duration(self) -> Optional[float]:
        """
        Get the stage duration in seconds.
        
        Returns:
            Stage duration in seconds, or None if stage has not completed
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """
        Check if the stage is completed.
        
        Returns:
            True if stage is completed, False otherwise
        """
        return self.status in [StageStatus.SUCCEEDED, StageStatus.FAILED, StageStatus.SKIPPED]

    @property
    def has_failed_tasks(self) -> bool:
        """
        Check if the stage has any failed tasks.
        
        Returns:
            True if stage has any failed tasks, False otherwise
        """
        return any(task.status == TaskStatus.FAILED for task in self.tasks)

    @property
    def success_percentage(self) -> float:
        """
        Calculate the success percentage of completed tasks.
        
        Returns:
            Percentage of completed tasks that succeeded
        """
        completed_tasks = [task for task in self.tasks if task.is_completed]
        if not completed_tasks:
            return 0.0
        
        succeeded_tasks = [
            task for task in completed_tasks 
            if task.status == TaskStatus.SUCCEEDED
        ]
        return (len(succeeded_tasks) / len(completed_tasks)) * 100.0


@dataclass
class Pipeline(AggregateRoot):
    """
    A deployment pipeline.
    
    The pipeline is responsible for orchestrating a series of stages and tasks
    to deploy an application.
    """

    id: PipelineId
    name: str
    description: str
    stages: List[Stage] = field(default_factory=list)
    status: DeploymentStatus = DeploymentStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def add_stage(self, stage: Stage) -> None:
        """
        Add a stage to the pipeline.
        
        Args:
            stage: The stage to add
        """
        self.stages.append(stage)
        self.updated_at = datetime.now(UTC)

    def remove_stage(self, stage_id: StageId) -> None:
        """
        Remove a stage from the pipeline.
        
        Args:
            stage_id: ID of the stage to remove
        """
        self.stages = [stage for stage in self.stages if stage.id != stage_id]
        self.updated_at = datetime.now(UTC)

    def start(self) -> None:
        """Start the pipeline."""
        self.status = DeploymentStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def succeed(self) -> None:
        """Mark the pipeline as succeeded."""
        self.status = DeploymentStatus.SUCCEEDED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def fail(self) -> None:
        """Mark the pipeline as failed."""
        self.status = DeploymentStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def cancel(self) -> None:
        """Cancel the pipeline."""
        self.status = DeploymentStatus.CANCELED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def start_rollback(self) -> None:
        """Start rolling back the pipeline."""
        self.status = DeploymentStatus.ROLLING_BACK
        self.updated_at = datetime.now(UTC)

    def complete_rollback(self) -> None:
        """Complete rolling back the pipeline."""
        self.status = DeploymentStatus.ROLLED_BACK
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def add_context(self, key: str, value: Any) -> None:
        """
        Add a value to the pipeline context.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
        self.updated_at = datetime.now(UTC)

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the pipeline context.
        
        Args:
            key: Context key
            default: Default value if key not found
            
        Returns:
            Context value or default
        """
        return self.context.get(key, default)

    def clear_context(self) -> None:
        """Clear the pipeline context."""
        self.context.clear()
        self.updated_at = datetime.now(UTC)

    @property
    def duration(self) -> Optional[float]:
        """
        Get the pipeline duration in seconds.
        
        Returns:
            Pipeline duration in seconds, or None if pipeline has not completed
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """
        Check if the pipeline is completed.
        
        Returns:
            True if pipeline is completed, False otherwise
        """
        return self.status in [
            DeploymentStatus.SUCCEEDED, 
            DeploymentStatus.FAILED,
            DeploymentStatus.CANCELED,
            DeploymentStatus.ROLLED_BACK
        ]

    @property
    def has_failed_stages(self) -> bool:
        """
        Check if the pipeline has any failed stages.
        
        Returns:
            True if pipeline has any failed stages, False otherwise
        """
        return any(stage.status == StageStatus.FAILED for stage in self.stages)

    @property
    def success_percentage(self) -> float:
        """
        Calculate the success percentage of completed stages.
        
        Returns:
            Percentage of completed stages that succeeded
        """
        completed_stages = [
            stage for stage in self.stages 
            if stage.is_completed
        ]
        if not completed_stages:
            return 0.0
        
        succeeded_stages = [
            stage for stage in completed_stages 
            if stage.status == StageStatus.SUCCEEDED
        ]
        return (len(succeeded_stages) / len(completed_stages)) * 100.0

    @property
    def current_stage(self) -> Optional[Stage]:
        """
        Get the current running stage, if any.
        
        Returns:
            The current running stage, or None if no stage is running
        """
        running_stages = [
            stage for stage in self.stages 
            if stage.status == StageStatus.RUNNING
        ]
        return running_stages[0] if running_stages else None


@dataclass
class DeploymentConfig(AggregateRoot):
    """
    Deployment configuration.
    
    This entity represents the configuration for deploying an application.
    """

    id: DeploymentId
    app_name: str
    app_version: str
    environment: DeploymentEnvironment = DeploymentEnvironment.DEV
    platform: DeploymentPlatform = DeploymentPlatform.KUBERNETES
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    database: DatabaseConfig
    resources: ResourceRequirements
    network: NetworkConfig
    security: SecurityConfig
    monitoring: MonitoringConfig
    testing: TestingConfig
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def set_environment(self, environment: DeploymentEnvironment) -> None:
        """
        Set the deployment environment.
        
        Args:
            environment: Deployment environment
        """
        self.environment = environment
        self.updated_at = datetime.now(UTC)

    def set_platform(self, platform: DeploymentPlatform) -> None:
        """
        Set the deployment platform.
        
        Args:
            platform: Deployment platform
        """
        self.platform = platform
        self.updated_at = datetime.now(UTC)

    def set_strategy(self, strategy: DeploymentStrategy) -> None:
        """
        Set the deployment strategy.
        
        Args:
            strategy: Deployment strategy
        """
        self.strategy = strategy
        self.updated_at = datetime.now(UTC)

    def add_environment_variable(self, key: str, value: str) -> None:
        """
        Add an environment variable.
        
        Args:
            key: Variable key
            value: Variable value
        """
        self.environment_variables[key] = value
        self.updated_at = datetime.now(UTC)

    def remove_environment_variable(self, key: str) -> None:
        """
        Remove an environment variable.
        
        Args:
            key: Variable key to remove
        """
        if key in self.environment_variables:
            del self.environment_variables[key]
            self.updated_at = datetime.now(UTC)

    def add_secret(self, secret: str) -> None:
        """
        Add a secret key.
        
        Args:
            secret: Secret key
        """
        if secret not in self.secrets:
            self.secrets.append(secret)
            self.updated_at = datetime.now(UTC)

    def remove_secret(self, secret: str) -> None:
        """
        Remove a secret key.
        
        Args:
            secret: Secret key to remove
        """
        if secret in self.secrets:
            self.secrets.remove(secret)
            self.updated_at = datetime.now(UTC)

    def add_config_file(self, file_path: str) -> None:
        """
        Add a configuration file.
        
        Args:
            file_path: Path to the configuration file
        """
        if file_path not in self.config_files:
            self.config_files.append(file_path)
            self.updated_at = datetime.now(UTC)

    def remove_config_file(self, file_path: str) -> None:
        """
        Remove a configuration file.
        
        Args:
            file_path: Path to the configuration file to remove
        """
        if file_path in self.config_files:
            self.config_files.remove(file_path)
            self.updated_at = datetime.now(UTC)

    def add_custom_setting(self, key: str, value: Any) -> None:
        """
        Add a custom setting.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.custom_settings[key] = value
        self.updated_at = datetime.now(UTC)

    def remove_custom_setting(self, key: str) -> None:
        """
        Remove a custom setting.
        
        Args:
            key: Setting key to remove
        """
        if key in self.custom_settings:
            del self.custom_settings[key]
            self.updated_at = datetime.now(UTC)

    def for_environment(self, environment: DeploymentEnvironment) -> 'DeploymentConfig':
        """
        Create a copy of this configuration for a specific environment.
        
        Args:
            environment: Target environment
            
        Returns:
            A new DeploymentConfig instance for the specified environment
        """
        # Create a copy of this configuration
        new_config = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name=self.app_name,
            app_version=self.app_version,
            environment=environment,
            platform=self.platform,
            strategy=self.strategy,
            database=self.database,
            resources=self.resources,
            network=self.network,
            security=self.security,
            monitoring=self.monitoring,
            testing=self.testing,
            custom_settings=self.custom_settings.copy(),
            environment_variables=self.environment_variables.copy(),
            secrets=self.secrets.copy(),
            config_files=self.config_files.copy()
        )
        
        # Adjust settings based on environment
        if environment == DeploymentEnvironment.PRODUCTION:
            # Production environments should use blue-green or canary
            new_config.strategy = DeploymentStrategy.BLUE_GREEN
            
            # Update resource requirements for production
            new_config.resources.update_replica_count(2, 5)
            new_config.resources.update_cpu_limits("250m", "1000m")
            new_config.resources.update_memory_limits("512Mi", "1Gi")
            
            # Update security settings for production
            new_config.security.enable_network_policies()
            new_config.security.enable_image_scanning()
            new_config.security.enable_dependency_scanning()
            new_config.security.enable_secrets_encryption()
            
            # Update testing settings for production
            new_config.testing.enable_unit_tests()
            new_config.testing.enable_integration_tests()
            new_config.testing.enable_performance_tests()
            new_config.testing.enable_security_tests()
            new_config.testing.set_fail_on_test_failure(True)
            
        elif environment == DeploymentEnvironment.STAGING:
            # Staging should mimic production but with fewer resources
            new_config.strategy = DeploymentStrategy.BLUE_GREEN
            new_config.resources.update_replica_count(1, 3)
            
            # Update security settings for staging
            new_config.security.enable_network_policies()
            new_config.security.enable_image_scanning()
            
            # Update testing settings for staging
            new_config.testing.enable_unit_tests()
            new_config.testing.enable_integration_tests()
            new_config.testing.disable_performance_tests()
            new_config.testing.enable_security_tests()
            
        elif environment == DeploymentEnvironment.TEST:
            # Test environment can use simpler deployment
            new_config.strategy = DeploymentStrategy.ROLLING
            new_config.resources.update_replica_count(1, 1)
            
            # Update security settings for test
            new_config.security.disable_network_policies()
            
            # Update testing settings for test
            new_config.testing.enable_unit_tests()
            new_config.testing.enable_integration_tests()
            new_config.testing.disable_performance_tests()
            new_config.testing.disable_security_tests()
            
        elif environment == DeploymentEnvironment.DEV:
            # Dev environment should be simple
            new_config.strategy = DeploymentStrategy.RECREATE
            new_config.resources.update_replica_count(1, 1)
            new_config.resources.disable_auto_scaling()
            
            # Update security settings for dev
            new_config.security.disable_network_policies()
            new_config.security.disable_image_scanning()
            
            # Update testing settings for dev
            new_config.testing.enable_unit_tests()
            new_config.testing.disable_integration_tests()
            new_config.testing.disable_performance_tests()
            new_config.testing.disable_security_tests()
        
        return new_config


@dataclass
class DeploymentResult(Entity):
    """
    Result of a deployment operation.
    
    This entity represents the result of a deployment operation.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deployment_id: DeploymentId
    success: bool
    message: str
    status: DeploymentStatus
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def add_detail(self, key: str, value: Any) -> None:
        """
        Add a detail to the result.
        
        Args:
            key: Detail key
            value: Detail value
        """
        self.details[key] = value