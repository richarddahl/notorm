# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Deployment script for Uno applications.

This script is the main entry point for deploying Uno applications using
the deployment pipeline.
"""

import argparse
import logging
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

from uno.deployment.config import DeploymentConfig, DeploymentEnvironment, DeploymentPlatform
from uno.deployment.manager import DeploymentManager


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logger instance
    """
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    return logging.getLogger("uno.deployment")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Deploy a Uno application",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--app-name",
        type=str,
        required=True,
        help="Application name"
    )
    
    parser.add_argument(
        "--app-version",
        type=str,
        default=os.environ.get("APP_VERSION", "latest"),
        help="Application version"
    )
    
    parser.add_argument(
        "--environment",
        type=str,
        choices=[e.value for e in DeploymentEnvironment],
        default=os.environ.get("ENV", "dev"),
        help="Deployment environment"
    )
    
    parser.add_argument(
        "--platform",
        type=str,
        choices=[p.value for p in DeploymentPlatform],
        default=os.environ.get("PLATFORM", "kubernetes"),
        help="Deployment platform"
    )
    
    parser.add_argument(
        "--config-file",
        type=str,
        help="Path to deployment configuration file"
    )
    
    parser.add_argument(
        "--image-tag",
        type=str,
        default=os.environ.get("IMAGE_TAG", "latest"),
        help="Container image tag"
    )
    
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        default=False,
        help="Skip tests before deployment"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Perform a dry run without actually deploying"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", "INFO"),
        help="Log level"
    )
    
    return parser.parse_args()


def create_config(args: argparse.Namespace) -> DeploymentConfig:
    """
    Create a deployment configuration.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Deployment configuration
    """
    if args.config_file and os.path.exists(args.config_file):
        # Load configuration from file
        config = DeploymentConfig.from_yaml(args.config_file)
        
        # Override with command-line arguments
        config.app_name = args.app_name
        config.app_version = args.app_version
        config.environment = DeploymentEnvironment(args.environment)
        config.platform = DeploymentPlatform(args.platform)
        
        # Update testing configuration
        if args.skip_tests:
            config.testing.run_unit_tests = False
            config.testing.run_integration_tests = False
            config.testing.run_performance_tests = False
            config.testing.run_security_tests = False
        
        return config
    else:
        # Create a default configuration
        config = DeploymentConfig(
            app_name=args.app_name,
            app_version=args.app_version,
            environment=DeploymentEnvironment(args.environment),
            platform=DeploymentPlatform(args.platform)
        )
        
        # Update testing configuration
        if args.skip_tests:
            config.testing.run_unit_tests = False
            config.testing.run_integration_tests = False
            config.testing.run_performance_tests = False
            config.testing.run_security_tests = False
        
        return config


def main() -> int:
    """
    Main entry point for the deployment script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_level)
    
    try:
        # Create deployment configuration
        config = create_config(args)
        
        # Add image tag to custom settings
        config.custom_settings["image_tag"] = args.image_tag
        
        # Log configuration
        logger.info(f"Deploying {config.app_name} version {config.app_version} to {config.environment.value}")
        logger.info(f"Platform: {config.platform.value}")
        logger.info(f"Dry run: {args.dry_run}")
        
        if args.dry_run:
            # Print the configuration in YAML format
            yaml_config = yaml.dump(config.dict(), sort_keys=False, indent=2)
            logger.info(f"Configuration:\n{yaml_config}")
            return 0
        
        # Create deployment manager
        manager = DeploymentManager(config, logger)
        
        # Deploy the application
        success = manager.deploy()
        
        if success:
            logger.info(f"Deployment of {config.app_name} to {config.environment.value} completed successfully")
            return 0
        else:
            logger.error(f"Deployment of {config.app_name} to {config.environment.value} failed")
            return 1
    except Exception as e:
        logger.exception(f"Deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())