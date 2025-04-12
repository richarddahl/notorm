"""
Uno Deployment Framework.

This module provides a comprehensive deployment pipeline for Uno applications,
including CI/CD integration, blue-green deployment support, and deployment
templates for various platforms.
"""

from uno.deployment.manager import DeploymentManager
from uno.deployment.config import DeploymentConfig
from uno.deployment.pipeline import Pipeline, Stage, Task
from uno.deployment.strategies import BlueGreenStrategy, RollingStrategy, CanaryStrategy

__version__ = "0.1.0"

__all__ = [
    "DeploymentManager",
    "DeploymentConfig",
    "Pipeline",
    "Stage",
    "Task",
    "BlueGreenStrategy",
    "RollingStrategy",
    "CanaryStrategy",
]