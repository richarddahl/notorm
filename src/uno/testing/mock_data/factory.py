"""
Factory classes for creating mock data objects, models, and test fixtures.

These factory classes provide a convenient interface for generating
test data based on the generators module.
"""

import inspect
import random
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable, Generic

from uno.testing.mock_data.generators import (
    MockDataGenerator,
    ModelDataGenerator,
    RandomGenerator,
    RealisticGenerator,
    SchemaBasedGenerator,
)

T = TypeVar('T')


class MockFactory:
    """
    Factory for creating mock data objects.
    
    This class provides convenient methods for generating mock data
    based on schemas or specifications.
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        realistic: bool = True,
        locale: str = "en_US",
    ):
        """
        Initialize the mock factory.
        
        Args:
            seed: Optional random seed for reproducible generation
            realistic: Whether to generate realistic data
            locale: Locale for generating localized data
        """
        self.seed = seed
        self.realistic = realistic
        self.locale = locale
        
        # Create generators
        if realistic:
            self.generator = RealisticGenerator(seed=seed, locale=locale)
        else:
            self.generator = RandomGenerator(seed=seed)
        
        self.schema_generator = SchemaBasedGenerator(
            seed=seed, realistic=realistic, locale=locale
        )
    
    def create_from_schema(self, schema: Dict[str, Any], **overrides) -> Dict[str, Any]:
        """
        Create a mock object from a schema.
        
        Args:
            schema: Schema defining the object structure
            **overrides: Field values to override in the generated data
            
        Returns:
            Generated mock object
        """
        data = self.schema_generator.generate(schema)
        
        # Apply overrides
        for field_name, value in overrides.items():
            data[field_name] = value
        
        return data
    
    def create_dict(
        self, 
        fields: List[str], 
        field_types: Optional[Dict[str, str]] = None,
        **field_values
    ) -> Dict[str, Any]:
        """
        Create a mock dictionary with specified fields.
        
        Args:
            fields: List of field names to include
            field_types: Optional mapping of field names to types
            **field_values: Explicit values for specific fields
            
        Returns:
            Generated dictionary
        """
        field_types = field_types or {}
        schema = {}
        
        for field in fields:
            field_type = field_types.get(field, "string")
            field_format = None
            
            # Try to infer format from field name if we're using realistic data
            if self.realistic and field_type == "string":
                field_format = self.generator._infer_format_from_name(field)
            
            schema[field] = {
                "type": field_type,
                "format": field_format,
                "constraints": {}
            }
        
        # Generate the data
        data = self.generator.generate(schema)
        
        # Apply explicit values
        for field, value in field_values.items():
            if field in fields:
                data[field] = value
        
        return data


class ModelFactory(Generic[T]):
    """
    Factory for creating model instances.
    
    This class provides convenient methods for generating instances
    of model classes with mock data.
    """
    
    def __init__(
        self,
        model_class: Type[T],
        seed: Optional[int] = None,
        realistic: bool = True,
        locale: str = "en_US",
    ):
        """
        Initialize the model factory.
        
        Args:
            model_class: The model class to create instances of
            seed: Optional random seed for reproducible generation
            realistic: Whether to generate realistic data
            locale: Locale for generating localized data
        """
        self.model_class = model_class
        self.seed = seed
        self.realistic = realistic
        self.locale = locale
        
        self.generator = ModelDataGenerator(
            seed=seed, realistic=realistic, locale=locale
        )
    
    def create(self, **overrides) -> T:
        """
        Create a model instance with mock data.
        
        Args:
            **overrides: Field values to override in the generated data
            
        Returns:
            Model instance
        """
        return self.generator.instantiate_model(self.model_class, **overrides)
    
    def create_batch(self, size: int, **overrides) -> List[T]:
        """
        Create multiple model instances with mock data.
        
        Args:
            size: Number of instances to create
            **overrides: Field values to override in the generated data
            
        Returns:
            List of model instances
        """
        return [self.create(**overrides) for _ in range(size)]
    
    @classmethod
    def for_model(
        cls,
        model_class: Type[T],
        seed: Optional[int] = None,
        realistic: bool = True,
        locale: str = "en_US",
    ) -> 'ModelFactory[T]':
        """
        Create a factory for a specific model class.
        
        Args:
            model_class: The model class to create instances of
            seed: Optional random seed for reproducible generation
            realistic: Whether to generate realistic data
            locale: Locale for generating localized data
            
        Returns:
            ModelFactory instance
        """
        return cls(
            model_class=model_class,
            seed=seed,
            realistic=realistic,
            locale=locale,
        )


class FixtureFactory:
    """
    Factory for creating test fixtures.
    
    This class provides methods for generating test fixtures
    with relationships between objects.
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        realistic: bool = True,
        locale: str = "en_US",
    ):
        """
        Initialize the fixture factory.
        
        Args:
            seed: Optional random seed for reproducible generation
            realistic: Whether to generate realistic data
            locale: Locale for generating localized data
        """
        self.seed = seed
        self.realistic = realistic
        self.locale = locale
        
        # Store created objects by type
        self.objects: Dict[Type, List[Any]] = {}
        
        # Create base generators
        self.mock_factory = MockFactory(
            seed=seed, realistic=realistic, locale=locale
        )
    
    def create_model(self, model_class: Type[T], **overrides) -> T:
        """
        Create a model instance and register it as a fixture.
        
        Args:
            model_class: The model class to create an instance of
            **overrides: Field values to override in the generated data
            
        Returns:
            Created model instance
        """
        # Create a factory for this model
        factory = ModelFactory(
            model_class=model_class,
            seed=random.randint(0, 10000) if self.seed is None else self.seed,
            realistic=self.realistic,
            locale=self.locale,
        )
        
        # Create the instance
        instance = factory.create(**overrides)
        
        # Store it
        if model_class not in self.objects:
            self.objects[model_class] = []
        self.objects[model_class].append(instance)
        
        return instance
    
    def get_or_create_model(
        self, 
        model_class: Type[T], 
        finder: Optional[Callable[[List[T]], Optional[T]]] = None,
        **overrides
    ) -> T:
        """
        Get an existing model instance or create a new one.
        
        Args:
            model_class: The model class to get or create
            finder: Optional function to find an existing instance
            **overrides: Field values for creating a new instance
            
        Returns:
            Existing or new model instance
        """
        # Check if we have any instances of this type
        instances = self.objects.get(model_class, [])
        
        # If we have a finder, use it to find an instance
        if finder and instances:
            instance = finder(instances)
            if instance:
                return instance
        
        # If we have instances but no finder, return a random one
        if instances and not overrides:
            return random.choice(instances)
        
        # Otherwise create a new instance
        return self.create_model(model_class, **overrides)
    
    def create_related_models(
        self,
        models: Dict[str, Type],
        relationships: Dict[str, List[str]],
        counts: Optional[Dict[str, int]] = None,
    ) -> Dict[str, List[Any]]:
        """
        Create multiple related models.
        
        Args:
            models: Mapping of name to model class
            relationships: Mapping of model name to list of related model names
            counts: Optional mapping of model name to count to create
            
        Returns:
            Mapping of model name to list of created instances
        """
        counts = counts or {name: 1 for name in models}
        results: Dict[str, List[Any]] = {name: [] for name in models}
        
        # First pass: create all models without relationships
        for name, model_class in models.items():
            for _ in range(counts.get(name, 1)):
                instance = self.create_model(model_class)
                results[name].append(instance)
        
        # Second pass: establish relationships
        for name, related_names in relationships.items():
            for instance in results[name]:
                for related_name in related_names:
                    # Get a random related instance
                    related_instance = random.choice(results[related_name])
                    
                    # Set the relationship based on naming convention
                    # This is a simplified approach and might need customization
                    # for specific relationship patterns
                    related_attr = f"{related_name.lower()}_id"
                    if hasattr(instance, related_attr):
                        id_attr = getattr(related_instance, "id", None)
                        if id_attr:
                            setattr(instance, related_attr, id_attr)
                    
                    # Try direct relationship
                    direct_attr = related_name.lower()
                    if hasattr(instance, direct_attr):
                        setattr(instance, direct_attr, related_instance)
        
        return results
    
    def cleanup(self):
        """
        Clean up created fixtures.
        
        This method resets the stored objects, useful for
        cleaning up between tests.
        """
        self.objects.clear()