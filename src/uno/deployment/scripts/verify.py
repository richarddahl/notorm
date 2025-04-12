# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Verification script for Uno deployments.

This script verifies that a deployment was successful by checking that
the application is running and responding to health checks.
"""

import argparse
import logging
import os
import sys
import time
import urllib.request
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from uno.deployment.config import DeploymentEnvironment, DeploymentPlatform


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
    
    return logging.getLogger("uno.deployment.verify")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Verify a Uno deployment",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--app-name",
        type=str,
        required=True,
        help="Application name"
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
        "--url",
        type=str,
        help="URL to check (optional)"
    )
    
    parser.add_argument(
        "--namespace",
        type=str,
        default=os.environ.get("NAMESPACE", "default"),
        help="Kubernetes namespace (only used for Kubernetes platform)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Check interval in seconds"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", "INFO"),
        help="Log level"
    )
    
    return parser.parse_args()


def check_kubernetes_deployment(
    app_name: str,
    namespace: str,
    logger: logging.Logger,
    timeout: int = 300,
    interval: int = 5
) -> bool:
    """
    Check if a Kubernetes deployment is ready.
    
    Args:
        app_name: Application name
        namespace: Kubernetes namespace
        logger: Logger instance
        timeout: Timeout in seconds
        interval: Check interval in seconds
        
    Returns:
        True if the deployment is ready, False otherwise
    """
    logger.info(f"Checking Kubernetes deployment {app_name} in namespace {namespace}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check if the deployment exists
            deployment_status = os.popen(f"kubectl get deployment {app_name} -n {namespace} -o json").read()
            if not deployment_status:
                logger.warning(f"Deployment {app_name} not found in namespace {namespace}")
                time.sleep(interval)
                continue
            
            # Parse deployment status
            deployment_data = json.loads(deployment_status)
            
            # Check if the deployment is ready
            if "status" in deployment_data:
                status = deployment_data["status"]
                if "availableReplicas" in status and "replicas" in status:
                    available = status["availableReplicas"]
                    desired = status["replicas"]
                    
                    logger.info(f"Deployment status: {available}/{desired} replicas available")
                    
                    if available == desired and available > 0:
                        logger.info(f"Deployment {app_name} is ready")
                        return True
            
            logger.info(f"Deployment {app_name} is not ready yet, waiting...")
            time.sleep(interval)
        except Exception as e:
            logger.error(f"Error checking deployment status: {str(e)}")
            time.sleep(interval)
    
    logger.error(f"Deployment {app_name} is not ready after {timeout} seconds")
    return False


def check_health_endpoint(
    url: str,
    logger: logging.Logger,
    timeout: int = 300,
    interval: int = 5
) -> bool:
    """
    Check if a health endpoint is responding.
    
    Args:
        url: URL to check
        logger: Logger instance
        timeout: Timeout in seconds
        interval: Check interval in seconds
        
    Returns:
        True if the endpoint is responding, False otherwise
    """
    logger.info(f"Checking health endpoint {url}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=10)
            if response.getcode() == 200:
                response_data = response.read().decode("utf-8")
                logger.info(f"Health endpoint is responding: {response_data}")
                return True
            else:
                logger.warning(f"Health endpoint returned status code {response.getcode()}")
                time.sleep(interval)
        except Exception as e:
            logger.warning(f"Error checking health endpoint: {str(e)}")
            time.sleep(interval)
    
    logger.error(f"Health endpoint is not responding after {timeout} seconds")
    return False


def get_service_url(
    app_name: str,
    namespace: str,
    environment: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """
    Get the URL for a Kubernetes service.
    
    Args:
        app_name: Application name
        namespace: Kubernetes namespace
        environment: Deployment environment
        logger: Logger instance
        
    Returns:
        Tuple of (success, URL)
    """
    try:
        # Get the service details
        service_status = os.popen(f"kubectl get service {app_name} -n {namespace} -o json").read()
        if not service_status:
            logger.error(f"Service {app_name} not found in namespace {namespace}")
            return False, None
        
        # Parse service status
        service_data = json.loads(service_status)
        
        # Get the service port
        if "spec" in service_data and "ports" in service_data["spec"]:
            ports = service_data["spec"]["ports"]
            if ports:
                port = ports[0].get("port", 80)
                
                # For local development, use port-forwarding
                if environment == "dev":
                    # Start port-forwarding in the background
                    os.system(f"kubectl port-forward service/{app_name} -n {namespace} {port}:{port} &")
                    # Wait for port-forwarding to start
                    time.sleep(2)
                    return True, f"http://localhost:{port}/health"
                
                # For other environments, get the service IP or hostname
                if "status" in service_data and "loadBalancer" in service_data["status"]:
                    ingress = service_data["status"]["loadBalancer"].get("ingress", [])
                    if ingress:
                        ip = ingress[0].get("ip")
                        hostname = ingress[0].get("hostname")
                        
                        if ip:
                            return True, f"http://{ip}:{port}/health"
                        elif hostname:
                            return True, f"http://{hostname}:{port}/health"
        
        logger.error(f"Could not determine URL for service {app_name}")
        return False, None
    except Exception as e:
        logger.error(f"Error getting service URL: {str(e)}")
        return False, None


def verify_deployment(args: argparse.Namespace, logger: logging.Logger) -> bool:
    """
    Verify a deployment.
    
    Args:
        args: Command-line arguments
        logger: Logger instance
        
    Returns:
        True if the deployment is verified, False otherwise
    """
    # Verify based on platform
    if args.platform == DeploymentPlatform.KUBERNETES.value:
        # Check if the deployment is ready
        if not check_kubernetes_deployment(
            args.app_name,
            args.namespace,
            logger,
            args.timeout,
            args.interval
        ):
            return False
        
        # Check the health endpoint
        if args.url:
            # Use the provided URL
            if not check_health_endpoint(
                args.url,
                logger,
                args.timeout,
                args.interval
            ):
                return False
        else:
            # Try to determine the URL
            success, url = get_service_url(
                args.app_name,
                args.namespace,
                args.environment,
                logger
            )
            
            if not success or not url:
                logger.error("Could not determine the service URL")
                return False
            
            if not check_health_endpoint(
                url,
                logger,
                args.timeout,
                args.interval
            ):
                return False
    else:
        # For other platforms, just check the health endpoint if provided
        if args.url:
            if not check_health_endpoint(
                args.url,
                logger,
                args.timeout,
                args.interval
            ):
                return False
        else:
            logger.error("URL not provided for health check")
            return False
    
    logger.info(f"Deployment of {args.app_name} to {args.environment} verified successfully")
    return True


def main() -> int:
    """
    Main entry point for the verification script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_level)
    
    try:
        # Verify the deployment
        if verify_deployment(args, logger):
            logger.info(f"Verification of {args.app_name} in {args.environment} completed successfully")
            return 0
        else:
            logger.error(f"Verification of {args.app_name} in {args.environment} failed")
            return 1
    except Exception as e:
        logger.exception(f"Verification failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())