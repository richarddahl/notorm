# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Blue-green deployment script for Uno applications.

This script is a specialized deployment script for blue-green deployments
of Uno applications on Kubernetes.
"""

import argparse
import logging
import os
import sys
import time
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from uno.deployment.config import DeploymentEnvironment
from uno.deployment.strategies import BlueGreenStrategy


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
    
    return logging.getLogger("uno.deployment.blue_green")


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Perform a blue-green deployment of a Uno application on Kubernetes",
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
        "--namespace",
        type=str,
        default=os.environ.get("NAMESPACE", "default"),
        help="Kubernetes namespace"
    )
    
    parser.add_argument(
        "--image-tag",
        type=str,
        default=os.environ.get("IMAGE_TAG", "latest"),
        help="Container image tag"
    )
    
    parser.add_argument(
        "--health-check-url",
        type=str,
        help="URL for health checks"
    )
    
    parser.add_argument(
        "--health-check-timeout",
        type=int,
        default=60,
        help="Timeout for health checks in seconds"
    )
    
    parser.add_argument(
        "--switch-timeout",
        type=int,
        default=300,
        help="Timeout for switching traffic in seconds"
    )
    
    parser.add_argument(
        "--template-file",
        type=str,
        default="src/uno/deployment/templates/kubernetes/deployment.yaml",
        help="Path to deployment template file"
    )
    
    parser.add_argument(
        "--values-file",
        type=str,
        help="Path to values file for template rendering"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", "INFO"),
        help="Log level"
    )
    
    return parser.parse_args()


def get_current_environment(
    app_name: str,
    namespace: str,
    logger: logging.Logger
) -> str:
    """
    Get the current active environment (blue or green).
    
    Args:
        app_name: Application name
        namespace: Kubernetes namespace
        logger: Logger instance
        
    Returns:
        Current environment ('blue' or 'green')
    """
    try:
        # Check if the service exists
        service_status = os.popen(f"kubectl get service {app_name} -n {namespace} -o json").read()
        if not service_status:
            logger.warning(f"Service {app_name} not found in namespace {namespace}")
            return "blue"  # Default to blue if service doesn't exist
        
        # Parse service status
        service_data = json.loads(service_status)
        
        # Check selector to determine current environment
        if "spec" in service_data and "selector" in service_data["spec"]:
            selector = service_data["spec"]["selector"]
            env = selector.get("environment", "")
            
            if env.endswith("-blue"):
                return "blue"
            elif env.endswith("-green"):
                return "green"
        
        logger.warning(f"Could not determine current environment from service {app_name}")
        return "blue"  # Default to blue
    except Exception as e:
        logger.error(f"Error getting current environment: {str(e)}")
        return "blue"  # Default to blue


def render_deployment_template(
    template_file: str,
    output_file: str,
    values: Dict[str, Any],
    logger: logging.Logger
) -> bool:
    """
    Render a deployment template with values.
    
    Args:
        template_file: Path to template file
        output_file: Path to output file
        values: Values for template rendering
        logger: Logger instance
        
    Returns:
        True if the template was rendered successfully, False otherwise
    """
    try:
        # Check if the template file exists
        if not os.path.exists(template_file):
            logger.error(f"Template file {template_file} not found")
            return False
        
        # Read the template
        with open(template_file, "r") as f:
            template = f.read()
        
        # Render the template (simple placeholder replacement)
        # In a real implementation, a proper template engine like Jinja2 would be used
        rendered = template
        for key, value in values.items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
        
        # Write the rendered template to the output file
        with open(output_file, "w") as f:
            f.write(rendered)
        
        logger.info(f"Deployment template rendered to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error rendering deployment template: {str(e)}")
        return False


def deploy_environment(
    env: str,
    app_name: str,
    namespace: str,
    image_tag: str,
    template_file: str,
    values_file: str,
    logger: logging.Logger
) -> bool:
    """
    Deploy to the specified environment (blue or green).
    
    Args:
        env: Environment ('blue' or 'green')
        app_name: Application name
        namespace: Kubernetes namespace
        image_tag: Container image tag
        template_file: Path to deployment template file
        values_file: Path to values file
        logger: Logger instance
        
    Returns:
        True if the deployment was successful, False otherwise
    """
    try:
        # Load values from file if provided
        values = {}
        if values_file and os.path.exists(values_file):
            with open(values_file, "r") as f:
                values = yaml.safe_load(f) or {}
        
        # Add or override values
        values.update({
            "app_name": f"{app_name}-{env}",
            "namespace": namespace,
            "environment": f"{namespace}-{env}",
            "image_tag": image_tag,
        })
        
        # Render the deployment template
        output_file = f"/tmp/{app_name}-{env}-deployment.yaml"
        if not render_deployment_template(template_file, output_file, values, logger):
            return False
        
        # Apply the deployment
        logger.info(f"Applying deployment for {env} environment")
        result = os.system(f"kubectl apply -f {output_file}")
        if result != 0:
            logger.error(f"Failed to apply deployment for {env} environment")
            return False
        
        logger.info(f"Deployment for {env} environment applied successfully")
        return True
    except Exception as e:
        logger.error(f"Error deploying to {env} environment: {str(e)}")
        return False


def run_health_checks(
    env: str,
    app_name: str,
    namespace: str,
    health_check_url: Optional[str],
    health_check_timeout: int,
    logger: logging.Logger
) -> bool:
    """
    Run health checks on the specified environment.
    
    Args:
        env: Environment ('blue' or 'green')
        app_name: Application name
        namespace: Kubernetes namespace
        health_check_url: URL for health checks
        health_check_timeout: Timeout for health checks in seconds
        logger: Logger instance
        
    Returns:
        True if the health checks passed, False otherwise
    """
    try:
        # Wait for the deployment to be ready
        logger.info(f"Waiting for deployment {app_name}-{env} to be ready")
        
        # Check deployment status
        start_time = time.time()
        while time.time() - start_time < health_check_timeout:
            deployment_status = os.popen(
                f"kubectl get deployment {app_name}-{env} -n {namespace} -o json"
            ).read()
            
            if not deployment_status:
                logger.warning(f"Deployment {app_name}-{env} not found in namespace {namespace}")
                time.sleep(5)
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
                        logger.info(f"Deployment {app_name}-{env} is ready")
                        break
            
            logger.info(f"Deployment {app_name}-{env} is not ready yet, waiting...")
            time.sleep(5)
        else:
            logger.error(f"Deployment {app_name}-{env} is not ready after {health_check_timeout} seconds")
            return False
        
        # If a health check URL is provided, check it
        if health_check_url:
            import urllib.request
            
            logger.info(f"Checking health endpoint {health_check_url}")
            
            # Format URL with environment
            url = health_check_url.replace("{env}", env)
            
            start_time = time.time()
            while time.time() - start_time < health_check_timeout:
                try:
                    response = urllib.request.urlopen(url, timeout=10)
                    if response.getcode() == 200:
                        logger.info(f"Health endpoint is responding: {response.read().decode('utf-8')}")
                        return True
                    else:
                        logger.warning(f"Health endpoint returned status code {response.getcode()}")
                        time.sleep(5)
                except Exception as e:
                    logger.warning(f"Error checking health endpoint: {str(e)}")
                    time.sleep(5)
            
            logger.error(f"Health endpoint is not responding after {health_check_timeout} seconds")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error running health checks on {env} environment: {str(e)}")
        return False


def switch_traffic(
    from_env: str,
    to_env: str,
    app_name: str,
    namespace: str,
    switch_timeout: int,
    logger: logging.Logger
) -> bool:
    """
    Switch traffic from one environment to another.
    
    Args:
        from_env: Source environment ('blue' or 'green')
        to_env: Target environment ('blue' or 'green')
        app_name: Application name
        namespace: Kubernetes namespace
        switch_timeout: Timeout for switching traffic in seconds
        logger: Logger instance
        
    Returns:
        True if the traffic was switched successfully, False otherwise
    """
    try:
        # Update the service selector to point to the new environment
        logger.info(f"Switching traffic from {from_env} to {to_env}")
        
        # Get the current service
        service_status = os.popen(f"kubectl get service {app_name} -n {namespace} -o json").read()
        if not service_status:
            logger.error(f"Service {app_name} not found in namespace {namespace}")
            return False
        
        # Parse service data
        service_data = json.loads(service_status)
        
        # Update the selector
        if "spec" in service_data and "selector" in service_data["spec"]:
            selector = service_data["spec"]["selector"]
            
            # Update environment label
            for key in selector:
                if "environment" in key:
                    selector[key] = f"{namespace}-{to_env}"
            
            # Update app label
            for key in selector:
                if "app" in key:
                    selector[key] = f"{app_name}-{to_env}"
            
            # Write the updated service to a temporary file
            service_file = f"/tmp/{app_name}-service.json"
            with open(service_file, "w") as f:
                json.dump(service_data, f)
            
            # Apply the updated service
            result = os.system(f"kubectl apply -f {service_file} -n {namespace}")
            if result != 0:
                logger.error(f"Failed to update service {app_name}")
                return False
            
            logger.info(f"Service {app_name} updated to point to {to_env} environment")
            
            # Wait for the service to update
            time.sleep(5)
            
            return True
        else:
            logger.error(f"Service {app_name} does not have a selector")
            return False
    except Exception as e:
        logger.error(f"Error switching traffic: {str(e)}")
        return False


def main() -> int:
    """
    Main entry point for the blue-green deployment script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_level)
    
    try:
        # Create blue-green strategy
        strategy = BlueGreenStrategy(
            logger=logger,
            health_check_url=args.health_check_url,
            health_check_timeout=args.health_check_timeout,
            switch_timeout=args.switch_timeout
        )
        
        # Create context
        context = {
            "app_name": args.app_name,
            "namespace": args.namespace,
            "image_tag": args.image_tag,
            "template_file": args.template_file,
            "values_file": args.values_file,
            "health_check_url": args.health_check_url,
            "current_env": get_current_environment(args.app_name, args.namespace, logger)
        }
        
        # Deploy using blue-green strategy
        result = strategy.deploy(context)
        
        if result.success:
            logger.info(f"Blue-green deployment of {args.app_name} completed successfully")
            return 0
        else:
            logger.error(f"Blue-green deployment of {args.app_name} failed: {result.message}")
            return 1
    except Exception as e:
        logger.exception(f"Blue-green deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())