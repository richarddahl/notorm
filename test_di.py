#!/usr/bin/env python3
"""
Test script for UnoServiceProvider.

This script tests the UnoServiceProvider directly, without using the adapter.
"""

import logging
from uno.dependencies.modern_provider import UnoServiceProvider, ServiceLifecycle

# Create a simple service
class MessageService:
    def __init__(self):
        self.message = "Hello from UnoServiceProvider"
    
    def get_message(self):
        return self.message

# Configure a test provider
provider = UnoServiceProvider("test")

# Register the service
provider.register(
    MessageService,
    lambda container: MessageService(),
    lifecycle=ServiceLifecycle.SINGLETON
)

# Initialize basic container
from uno.dependencies.scoped_container import ServiceCollection, initialize_container
services = ServiceCollection()
initialize_container(services, logging.getLogger("test"))

# Configure the container
provider.configure_container(
    from uno.dependencies.scoped_container import get_container
    get_container()
)

# Get the service
from uno.dependencies.scoped_container import get_service
service = get_service(MessageService)

# Use the service
print(f"Message: {service.get_message()}")
print("UnoServiceProvider is working correctly!")

# Also test the adapter
print("\nTesting the adapter...")
from uno.core import (
    DIContainer, ServiceLifetime, 
    initialize_container, get_container, reset_container,
    get_service
)

# Reset and initialize
reset_container()
initialize_container()

# Get container 
container = get_container()

# Register a service through the adapter
class AdapterService:
    def __init__(self):
        self.message = "Hello from the adapter"
    
    def get_message(self):
        return self.message

container.register_singleton(AdapterService)

# Get service
adapter_service = get_service(AdapterService)
print(f"Adapter message: {adapter_service.get_message()}")
print("Adapter is working correctly!")