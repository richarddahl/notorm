"""
Examples of using the UnoServiceProvider system for dependency injection.

This module contains examples of using the UnoServiceProvider system
for domain-oriented dependency injection.
"""

# ----------------------------------------------------------------------
# Example 1: Using UnoServiceProvider directly
# ----------------------------------------------------------------------

def example_uno_service_provider():
    """Example of using UnoServiceProvider directly."""
    
    from uno.dependencies.modern_provider import UnoServiceProvider, ServiceLifecycle
    import logging
    
    # Create a provider
    provider = UnoServiceProvider('example')
    
    # Define a service
    class MessageService:
        def __init__(self):
            self.message = 'Hello from UnoServiceProvider'
        
        def get_message(self):
            return self.message
    
    # Register the service with the provider
    provider.register_instance(MessageService, MessageService())
    
    # Get the service
    service = provider.get_service(MessageService)
    
    # Use the service
    print(f'Message: {service.get_message()}')

# ----------------------------------------------------------------------
# Example 2: Domain Provider Pattern
# ----------------------------------------------------------------------

def example_domain_provider():
    """Example of using the domain provider pattern."""
    
    from uno.dependencies.modern_provider import UnoServiceProvider, ServiceLifecycle
    import logging
    from functools import lru_cache
    
    # Define a service
    class ProductService:
        def __init__(self, logger=None):
            self.logger = logger or logging.getLogger('product')
        
        def get_product(self, id):
            self.logger.info(f'Getting product {id}')
            return {'id': id, 'name': f'Product {id}', 'price': 10.99}
    
    # Define a domain provider
    @lru_cache(maxsize=1)
    def get_product_provider():
        """Get the product domain provider."""
        provider = UnoServiceProvider('product')
        logger = logging.getLogger('product')
        
        # Register services
        provider.register(
            ProductService,
            lambda container: ProductService(logger=logger),
            lifecycle=ServiceLifecycle.SCOPED,
        )
        
        return provider
    
    # Get provider and create a scope
    provider = get_product_provider()
    
    # Use a scope for scoped services
    with provider.create_scope() as scope:
        # Get service from the scope
        service = scope.resolve(ProductService)
        
        # Use service
        product = service.get_product('123')
        print(f'Product: {product}')

# ----------------------------------------------------------------------
# Example 3: Advanced Provider Configuration
# ----------------------------------------------------------------------

def example_advanced_configuration():
    """Example of advanced provider configuration."""
    
    from uno.dependencies.modern_provider import (
        UnoServiceProvider, 
        ServiceLifecycle,
        Initializable,
        Disposable
    )
    import logging
    
    # Define a service with lifecycle hooks
    class DataService(Initializable, Disposable):
        def __init__(self, logger=None):
            self.logger = logger or logging.getLogger('data')
            self.data = {}
            
        def initialize(self):
            self.logger.info("Initializing DataService")
            self.data = {"initialized": True}
            
        def dispose(self):
            self.logger.info("Disposing DataService")
            self.data.clear()
            
        def get_data(self, key):
            return self.data.get(key)
            
        def set_data(self, key, value):
            self.data[key] = value
    
    # Create provider
    provider = UnoServiceProvider('data')
    logger = logging.getLogger('data')
    
    # Register service
    provider.register(
        DataService,
        lambda container: DataService(logger=logger),
        lifecycle=ServiceLifecycle.SINGLETON,
    )
    
    # Get service
    service = provider.get_service(DataService)
    
    # Use service
    service.set_data('example', 'value')
    result = service.get_data('example')
    print(f'Data: {result}')
    
    # Provider will automatically call initialize and dispose

# Run the examples
if __name__ == '__main__':
    print('Example 1: Using UnoServiceProvider directly')
    print('-------------------------------------------')
    example_uno_service_provider()
    
    print('\nExample 2: Domain Provider Pattern')
    print('--------------------------------')
    example_domain_provider()
    
    print('\nExample 3: Advanced Provider Configuration')
    print('--------------------------------')
    example_advanced_configuration()