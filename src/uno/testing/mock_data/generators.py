"""
Mock data generators for Uno applications.

This module provides base classes and implementations for generating
mock data for testing, with support for various data types and constraints.
"""

import random
import string
import datetime
import uuid
import decimal
import inspect
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, TypeVar, Generic, Callable

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

from dataclasses import is_dataclass, fields as dataclass_fields


T = TypeVar('T')


class MockDataGeneratorError(Exception):
    """Exception raised when mock data generation fails."""
    pass


class MockDataGenerator:
    """Base class for mock data generators."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the mock data generator.
        
        Args:
            seed: Optional random seed for reproducible generation
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def generate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate mock data based on a schema.
        
        Args:
            schema: Schema defining the data structure and constraints
            
        Returns:
            Generated data
        """
        raise NotImplementedError("Subclasses must implement generate")


class RandomGenerator(MockDataGenerator):
    """
    Generator that produces random data based on type hints.
    
    This generator uses Python's built-in random module to generate
    values for basic types like integers, floats, strings, etc.
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        max_length: int = 100,
        min_int: int = -1000,
        max_int: int = 1000,
    ):
        """
        Initialize the random generator.
        
        Args:
            seed: Optional random seed for reproducible generation
            max_length: Maximum length for generated strings and lists
            min_int: Minimum value for generated integers
            max_int: Maximum value for generated integers
        """
        super().__init__(seed)
        self.max_length = max_length
        self.min_int = min_int
        self.max_int = max_int
    
    def generate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate random data based on the schema.
        
        Args:
            schema: Schema defining the data structure and constraints
            
        Returns:
            Generated data
        """
        result = {}
        
        for field_name, field_schema in schema.items():
            field_type = field_schema.get("type", "string")
            field_format = field_schema.get("format")
            field_constraints = field_schema.get("constraints", {})
            
            result[field_name] = self._generate_value(field_type, field_format, field_constraints)
        
        return result
    
    def _generate_value(
        self,
        field_type: str,
        field_format: Optional[str] = None,
        field_constraints: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Generate a value for a field.
        
        Args:
            field_type: Type of the field
            field_format: Optional format specifier
            field_constraints: Optional constraints
            
        Returns:
            Generated value
        """
        field_constraints = field_constraints or {}
        
        # Handle different types
        if field_type == "integer":
            return self._generate_integer(field_constraints)
        elif field_type == "number":
            return self._generate_number(field_constraints)
        elif field_type == "string":
            return self._generate_string(field_format, field_constraints)
        elif field_type == "boolean":
            return random.choice([True, False])
        elif field_type == "array":
            return self._generate_array(field_constraints)
        elif field_type == "object":
            return self._generate_object(field_constraints)
        elif field_type == "null":
            return None
        else:
            # Default to string for unknown types
            return self._generate_string(None, field_constraints)
    
    def _generate_integer(self, constraints: Dict[str, Any]) -> int:
        """Generate an integer value."""
        min_value = constraints.get("minimum", self.min_int)
        max_value = constraints.get("maximum", self.max_int)
        return random.randint(min_value, max_value)
    
    def _generate_number(self, constraints: Dict[str, Any]) -> float:
        """Generate a number value."""
        min_value = constraints.get("minimum", float(self.min_int))
        max_value = constraints.get("maximum", float(self.max_int))
        return random.uniform(min_value, max_value)
    
    def _generate_string(
        self,
        format_spec: Optional[str],
        constraints: Dict[str, Any]
    ) -> str:
        """Generate a string value."""
        min_length = constraints.get("minLength", 1)
        max_length = constraints.get("maxLength", self.max_length)
        length = random.randint(min_length, max_length)
        
        # Handle special formats
        if format_spec == "date":
            return self._generate_date()
        elif format_spec == "date-time":
            return self._generate_datetime()
        elif format_spec == "email":
            return self._generate_email()
        elif format_spec == "uuid":
            return str(uuid.uuid4())
        elif format_spec == "uri":
            return self._generate_uri()
        elif format_spec == "password":
            return self._generate_password(length)
        elif format_spec == "binary":
            return self._generate_binary(length)
        elif format_spec == "byte":
            return self._generate_bytes(length)
        
        # Check for pattern constraint
        pattern = constraints.get("pattern")
        if pattern:
            # Simple pattern-based generation (limited support)
            if pattern == "^[A-Za-z]+$":
                return ''.join(random.choices(string.ascii_letters, k=length))
            elif pattern == "^[0-9]+$":
                return ''.join(random.choices(string.digits, k=length))
            elif pattern == "^[A-Za-z0-9]+$":
                return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        
        # Default string generation
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _generate_date(self) -> str:
        """Generate a date string."""
        year = random.randint(1970, 2030)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Avoiding edge cases with month lengths
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    def _generate_datetime(self) -> str:
        """Generate a datetime string."""
        date = self._generate_date()
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        return f"{date}T{hour:02d}:{minute:02d}:{second:02d}Z"
    
    def _generate_email(self) -> str:
        """Generate an email address."""
        username_length = random.randint(5, 10)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
        
        domains = ["example.com", "test.org", "mock.net", "sample.io"]
        domain = random.choice(domains)
        
        return f"{username}@{domain}"
    
    def _generate_uri(self) -> str:
        """Generate a URI."""
        protocols = ["http", "https"]
        protocol = random.choice(protocols)
        
        domains = ["example.com", "test.org", "mock.net", "sample.io"]
        domain = random.choice(domains)
        
        path_length = random.randint(0, 3)
        path = ""
        if path_length > 0:
            path_parts = []
            for _ in range(path_length):
                part_length = random.randint(3, 8)
                part = ''.join(random.choices(string.ascii_lowercase, k=part_length))
                path_parts.append(part)
            path = "/" + "/".join(path_parts)
        
        return f"{protocol}://{domain}{path}"
    
    def _generate_password(self, length: int) -> str:
        """Generate a password."""
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choices(chars, k=length))
    
    def _generate_binary(self, length: int) -> str:
        """Generate a binary string."""
        return ''.join(random.choices("01", k=length))
    
    def _generate_bytes(self, length: int) -> str:
        """Generate a byte string."""
        return ''.join(random.choices(string.hexdigits, k=length * 2))
    
    def _generate_array(self, constraints: Dict[str, Any]) -> List[Any]:
        """Generate an array value."""
        min_items = constraints.get("minItems", 0)
        max_items = constraints.get("maxItems", 10)
        length = random.randint(min_items, max_items)
        
        items_schema = constraints.get("items", {"type": "string"})
        item_type = items_schema.get("type", "string")
        item_format = items_schema.get("format")
        item_constraints = items_schema.get("constraints", {})
        
        return [
            self._generate_value(item_type, item_format, item_constraints)
            for _ in range(length)
        ]
    
    def _generate_object(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an object value."""
        properties = constraints.get("properties", {})
        result = {}
        
        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            prop_format = prop_schema.get("format")
            prop_constraints = prop_schema.get("constraints", {})
            
            result[prop_name] = self._generate_value(prop_type, prop_format, prop_constraints)
        
        return result


class RealisticGenerator(MockDataGenerator):
    """
    Generator that produces realistic mock data.
    
    This generator uses the Faker library to generate realistic
    data for various types of fields.
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        max_length: int = 100,
    ):
        """
        Initialize the realistic generator.
        
        Args:
            seed: Optional random seed for reproducible generation
            locale: Locale for generating localized data
            max_length: Maximum length for generated collections
        """
        super().__init__(seed)
        self.max_length = max_length
        
        if not FAKER_AVAILABLE:
            raise ImportError(
                "Faker is required for realistic data generation. "
                "Please install it with: pip install faker"
            )
        
        self.faker = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
    
    def generate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate realistic data based on the schema.
        
        Args:
            schema: Schema defining the data structure and constraints
            
        Returns:
            Generated data
        """
        result = {}
        
        for field_name, field_schema in schema.items():
            field_type = field_schema.get("type", "string")
            field_format = field_schema.get("format")
            field_constraints = field_schema.get("constraints", {})
            
            result[field_name] = self._generate_value(field_name, field_type, field_format, field_constraints)
        
        return result
    
    def _generate_value(
        self,
        field_name: str,
        field_type: str,
        field_format: Optional[str] = None,
        field_constraints: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Generate a realistic value for a field.
        
        Args:
            field_name: Name of the field (used for hints)
            field_type: Type of the field
            field_format: Optional format specifier
            field_constraints: Optional constraints
            
        Returns:
            Generated value
        """
        field_constraints = field_constraints or {}
        
        # Try to infer the type of data from the field name
        inferred_format = self._infer_format_from_name(field_name)
        if inferred_format and not field_format:
            field_format = inferred_format
        
        # Handle different types
        if field_type == "integer":
            return self._generate_integer(field_format, field_constraints)
        elif field_type == "number":
            return self._generate_number(field_format, field_constraints)
        elif field_type == "string":
            return self._generate_string(field_format, field_constraints)
        elif field_type == "boolean":
            return self.faker.boolean()
        elif field_type == "array":
            return self._generate_array(field_constraints)
        elif field_type == "object":
            return self._generate_object(field_constraints)
        elif field_type == "null":
            return None
        else:
            # Default to string for unknown types
            return self._generate_string(field_format, field_constraints)
    
    def _infer_format_from_name(self, field_name: str) -> Optional[str]:
        """
        Infer the format from the field name.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Inferred format or None
        """
        name_lower = field_name.lower()
        
        if "email" in name_lower:
            return "email"
        elif "password" in name_lower:
            return "password"
        elif "date" in name_lower and "time" in name_lower:
            return "date-time"
        elif "date" in name_lower:
            return "date"
        elif "time" in name_lower:
            return "time"
        elif "url" in name_lower or "uri" in name_lower:
            return "uri"
        elif "phone" in name_lower:
            return "phone"
        elif "address" in name_lower:
            return "address"
        elif "name" == name_lower:
            return "name"
        elif "first" in name_lower and "name" in name_lower:
            return "first_name"
        elif "last" in name_lower and "name" in name_lower:
            return "last_name"
        elif "city" in name_lower:
            return "city"
        elif "state" in name_lower:
            return "state"
        elif "country" in name_lower:
            return "country"
        elif "zip" in name_lower or "postal" in name_lower:
            return "zipcode"
        elif "company" in name_lower:
            return "company"
        elif "job" in name_lower:
            return "job"
        elif "description" in name_lower:
            return "text"
        elif "uuid" in name_lower or "guid" in name_lower:
            return "uuid"
        elif "image" in name_lower or "photo" in name_lower:
            return "image_url"
        
        return None
    
    def _generate_integer(
        self,
        format_spec: Optional[str],
        constraints: Dict[str, Any]
    ) -> int:
        """Generate a realistic integer value."""
        min_value = constraints.get("minimum", -1000)
        max_value = constraints.get("maximum", 1000)
        
        if format_spec == "unix-timestamp":
            # Unix timestamp (seconds since epoch)
            return int(self.faker.date_time().timestamp())
        
        return self.faker.pyint(min_value=min_value, max_value=max_value)
    
    def _generate_number(
        self,
        format_spec: Optional[str],
        constraints: Dict[str, Any]
    ) -> float:
        """Generate a realistic number value."""
        min_value = constraints.get("minimum", -1000.0)
        max_value = constraints.get("maximum", 1000.0)
        
        if format_spec == "percentage":
            return self.faker.pyfloat(min_value=0.0, max_value=100.0)
        elif format_spec == "latitude":
            return self.faker.latitude()
        elif format_spec == "longitude":
            return self.faker.longitude()
        
        return self.faker.pyfloat(min_value=min_value, max_value=max_value)
    
    def _generate_string(
        self,
        format_spec: Optional[str],
        constraints: Dict[str, Any]
    ) -> str:
        """Generate a realistic string value."""
        min_length = constraints.get("minLength", 1)
        max_length = constraints.get("maxLength", self.max_length)
        
        # Handle special formats
        if format_spec == "date":
            return self.faker.date()
        elif format_spec == "date-time":
            return self.faker.iso8601()
        elif format_spec == "time":
            return self.faker.time()
        elif format_spec == "email":
            return self.faker.email()
        elif format_spec == "uuid":
            return str(self.faker.uuid4())
        elif format_spec == "uri" or format_spec == "url":
            return self.faker.url()
        elif format_spec == "hostname":
            return self.faker.domain_name()
        elif format_spec == "ipv4":
            return self.faker.ipv4()
        elif format_spec == "ipv6":
            return self.faker.ipv6()
        elif format_spec == "password":
            return self.faker.password(length=random.randint(min_length, max_length))
        elif format_spec == "name":
            return self.faker.name()
        elif format_spec == "first_name":
            return self.faker.first_name()
        elif format_spec == "last_name":
            return self.faker.last_name()
        elif format_spec == "phone":
            return self.faker.phone_number()
        elif format_spec == "address":
            return self.faker.address()
        elif format_spec == "city":
            return self.faker.city()
        elif format_spec == "state":
            return self.faker.state()
        elif format_spec == "country":
            return self.faker.country()
        elif format_spec == "zipcode":
            return self.faker.zipcode()
        elif format_spec == "company":
            return self.faker.company()
        elif format_spec == "job":
            return self.faker.job()
        elif format_spec == "text":
            # Generate text with reasonable length
            length = random.randint(min_length, min(max_length, 500))
            return self.faker.text(length)
        elif format_spec == "image_url":
            return self.faker.image_url()
        
        # Check for pattern constraint
        pattern = constraints.get("pattern")
        if pattern:
            # Use basic regex generation (limited support)
            try:
                # Try to generate from regex pattern
                from faker.providers import BaseProvider
                return BaseProvider(self.faker).lexify(pattern)
            except Exception:
                # Fall back to regular generation
                pass
        
        # Default to a random word or sentence
        if max_length < 10:
            return self.faker.word()[:max_length]
        elif max_length < 100:
            return self.faker.sentence()[:max_length]
        else:
            return self.faker.paragraph()[:max_length]
    
    def _generate_array(self, constraints: Dict[str, Any]) -> List[Any]:
        """Generate a realistic array value."""
        min_items = constraints.get("minItems", 0)
        max_items = constraints.get("maxItems", 10)
        length = random.randint(min_items, max_items)
        
        items_schema = constraints.get("items", {"type": "string"})
        item_type = items_schema.get("type", "string")
        item_format = items_schema.get("format")
        item_constraints = items_schema.get("constraints", {})
        
        return [
            self._generate_value("item", item_type, item_format, item_constraints)
            for _ in range(length)
        ]
    
    def _generate_object(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a realistic object value."""
        properties = constraints.get("properties", {})
        result = {}
        
        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            prop_format = prop_schema.get("format")
            prop_constraints = prop_schema.get("constraints", {})
            
            result[prop_name] = self._generate_value(
                prop_name, prop_type, prop_format, prop_constraints
            )
        
        return result


class SchemaBasedGenerator(MockDataGenerator):
    """
    Generator that produces data based on JSON Schema.
    
    This generator takes a JSON Schema document and produces
    data that conforms to the schema.
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        realistic: bool = True,
        locale: str = "en_US",
    ):
        """
        Initialize the schema-based generator.
        
        Args:
            seed: Optional random seed for reproducible generation
            realistic: Whether to generate realistic data
            locale: Locale for generating localized data
        """
        super().__init__(seed)
        self.realistic = realistic
        
        if realistic:
            if not FAKER_AVAILABLE:
                raise ImportError(
                    "Faker is required for realistic data generation. "
                    "Please install it with: pip install faker"
                )
            self.realistic_generator = RealisticGenerator(seed=seed, locale=locale)
        
        self.random_generator = RandomGenerator(seed=seed)
    
    def generate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data based on the JSON Schema.
        
        Args:
            schema: JSON Schema defining the data structure
            
        Returns:
            Generated data
        """
        # Use the appropriate generator based on configuration
        if self.realistic:
            generator = self.realistic_generator
        else:
            generator = self.random_generator
        
        # Extract properties from the schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Create a schema format for the generator
        generator_schema = {}
        
        for prop_name, prop_schema in properties.items():
            # Skip if not required and randomly decide to include
            if prop_name not in required and random.random() < 0.3:
                continue
            
            # Build field schema for the generator
            field_schema = {
                "type": prop_schema.get("type", "string"),
                "format": prop_schema.get("format"),
                "constraints": {
                    "minimum": prop_schema.get("minimum"),
                    "maximum": prop_schema.get("maximum"),
                    "minLength": prop_schema.get("minLength"),
                    "maxLength": prop_schema.get("maxLength"),
                    "pattern": prop_schema.get("pattern"),
                    "minItems": prop_schema.get("minItems"),
                    "maxItems": prop_schema.get("maxItems"),
                    "items": {
                        "type": prop_schema.get("items", {}).get("type", "string"),
                        "format": prop_schema.get("items", {}).get("format"),
                    }
                }
            }
            
            # Handle nested objects
            if prop_schema.get("type") == "object" and "properties" in prop_schema:
                field_schema["constraints"]["properties"] = {}
                for nested_name, nested_schema in prop_schema["properties"].items():
                    field_schema["constraints"]["properties"][nested_name] = {
                        "type": nested_schema.get("type", "string"),
                        "format": nested_schema.get("format"),
                        "constraints": {
                            "minimum": nested_schema.get("minimum"),
                            "maximum": nested_schema.get("maximum"),
                            "minLength": nested_schema.get("minLength"),
                            "maxLength": nested_schema.get("maxLength"),
                            "pattern": nested_schema.get("pattern"),
                        }
                    }
            
            generator_schema[prop_name] = field_schema
        
        # Generate the data
        return generator.generate(generator_schema)


class ModelDataGenerator(MockDataGenerator):
    """
    Generator that produces data for Uno models.
    
    This generator analyzes model classes and generates
    data that conforms to their field specifications.
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        realistic: bool = True,
        locale: str = "en_US",
    ):
        """
        Initialize the model data generator.
        
        Args:
            seed: Optional random seed for reproducible generation
            realistic: Whether to generate realistic data
            locale: Locale for generating localized data
        """
        super().__init__(seed)
        self.realistic = realistic
        
        if realistic:
            if not FAKER_AVAILABLE:
                raise ImportError(
                    "Faker is required for realistic data generation. "
                    "Please install it with: pip install faker"
                )
            self.realistic_generator = RealisticGenerator(seed=seed, locale=locale)
        
        self.random_generator = RandomGenerator(seed=seed)
    
    def generate_for_model(self, model_class: Type[T], **overrides) -> Dict[str, Any]:
        """
        Generate data for a model class.
        
        Args:
            model_class: Model class to generate data for
            **overrides: Field values to override in the generated data
            
        Returns:
            Dictionary of field values for the model
        """
        schema = self._model_to_schema(model_class)
        
        # Use the appropriate generator based on configuration
        if self.realistic:
            generator = self.realistic_generator
        else:
            generator = self.random_generator
        
        # Generate data from schema
        data = generator.generate(schema)
        
        # Apply overrides
        for field_name, value in overrides.items():
            data[field_name] = value
        
        return data
    
    def instantiate_model(self, model_class: Type[T], **overrides) -> T:
        """
        Generate and instantiate a model.
        
        Args:
            model_class: Model class to instantiate
            **overrides: Field values to override in the generated data
            
        Returns:
            Instance of the model class
        """
        data = self.generate_for_model(model_class, **overrides)
        
        try:
            # Try to instantiate the model with the generated data
            return model_class(**data)
        except Exception as e:
            raise MockDataGeneratorError(
                f"Failed to instantiate model {model_class.__name__}: {str(e)}"
            ) from e
    
    def generate(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data based on a schema.
        
        Args:
            schema: Schema defining the data structure
            
        Returns:
            Generated data
        """
        if self.realistic:
            return self.realistic_generator.generate(schema)
        else:
            return self.random_generator.generate(schema)
    
    def _model_to_schema(self, model_class: Type[Any]) -> Dict[str, Any]:
        """
        Convert a model class to a schema for data generation.
        
        Args:
            model_class: Model class to convert
            
        Returns:
            Schema for data generation
        """
        schema = {}
        
        # Handle dataclasses
        if is_dataclass(model_class):
            for field in dataclass_fields(model_class):
                field_schema = self._field_to_schema(field.name, field.type)
                schema[field.name] = field_schema
            return schema
        
        # Handle SQLAlchemy models
        if hasattr(model_class, "__table__") and hasattr(model_class.__table__, "columns"):
            for column in model_class.__table__.columns:
                field_schema = self._sqla_column_to_schema(column)
                schema[column.name] = field_schema
            return schema
        
        # Handle Pydantic models
        if hasattr(model_class, "__fields__"):
            for field_name, field in model_class.__fields__.items():
                field_schema = self._pydantic_field_to_schema(field)
                schema[field_name] = field_schema
            return schema
        
        # Handle classes with type annotations
        annotations = getattr(model_class, "__annotations__", {})
        for field_name, field_type in annotations.items():
            field_schema = self._field_to_schema(field_name, field_type)
            schema[field_name] = field_schema
        
        # Handle UnoModel classes
        if hasattr(model_class, "schema") and callable(model_class.schema):
            try:
                model_schema = model_class.schema()
                for field_name, field_schema in model_schema.get("properties", {}).items():
                    schema_entry = {
                        "type": field_schema.get("type", "string"),
                        "format": field_schema.get("format"),
                        "constraints": {
                            "minimum": field_schema.get("minimum"),
                            "maximum": field_schema.get("maximum"),
                            "minLength": field_schema.get("minLength"),
                            "maxLength": field_schema.get("maxLength"),
                            "pattern": field_schema.get("pattern"),
                        }
                    }
                    schema[field_name] = schema_entry
                return schema
            except Exception:
                pass
        
        # For other classes, try to inspect attributes
        for attr_name, attr_value in inspect.getmembers(model_class):
            if not attr_name.startswith("_") and not inspect.ismethod(attr_value) and not inspect.isfunction(attr_value):
                field_schema = self._field_to_schema(attr_name, type(attr_value))
                schema[attr_name] = field_schema
        
        return schema
    
    def _field_to_schema(self, field_name: str, field_type: Any) -> Dict[str, Any]:
        """
        Convert a field type to a schema for data generation.
        
        Args:
            field_name: Name of the field
            field_type: Type of the field
            
        Returns:
            Schema for data generation
        """
        schema = {
            "type": "string",  # Default type
            "format": None,
            "constraints": {}
        }
        
        # Handle basic types
        if field_type == int or field_type == float:
            schema["type"] = "integer" if field_type == int else "number"
        elif field_type == bool:
            schema["type"] = "boolean"
        elif field_type == str:
            schema["type"] = "string"
            # Try to infer format from field name
            if self.realistic:
                inferred_format = self.realistic_generator._infer_format_from_name(field_name)
                if inferred_format:
                    schema["format"] = inferred_format
        elif field_type == list or getattr(field_type, "__origin__", None) == list:
            schema["type"] = "array"
            if hasattr(field_type, "__args__") and field_type.__args__:
                item_type = field_type.__args__[0]
                item_schema = self._field_to_schema("item", item_type)
                schema["constraints"]["items"] = item_schema
        elif field_type == dict or getattr(field_type, "__origin__", None) == dict:
            schema["type"] = "object"
        elif field_type == datetime.date:
            schema["type"] = "string"
            schema["format"] = "date"
        elif field_type == datetime.datetime:
            schema["type"] = "string"
            schema["format"] = "date-time"
        elif field_type == uuid.UUID:
            schema["type"] = "string"
            schema["format"] = "uuid"
        elif field_type == decimal.Decimal:
            schema["type"] = "number"
        
        return schema
    
    def _sqla_column_to_schema(self, column: Any) -> Dict[str, Any]:
        """
        Convert an SQLAlchemy column to a schema for data generation.
        
        Args:
            column: SQLAlchemy column
            
        Returns:
            Schema for data generation
        """
        import sqlalchemy as sa
        
        schema = {
            "type": "string",  # Default type
            "format": None,
            "constraints": {}
        }
        
        # Get column type
        column_type = column.type
        
        # Handle common SQLAlchemy types
        if isinstance(column_type, sa.Integer):
            schema["type"] = "integer"
        elif isinstance(column_type, sa.Float):
            schema["type"] = "number"
        elif isinstance(column_type, sa.String):
            schema["type"] = "string"
            if column_type.length:
                schema["constraints"]["maxLength"] = column_type.length
        elif isinstance(column_type, sa.Boolean):
            schema["type"] = "boolean"
        elif isinstance(column_type, sa.Date):
            schema["type"] = "string"
            schema["format"] = "date"
        elif isinstance(column_type, sa.DateTime):
            schema["type"] = "string"
            schema["format"] = "date-time"
        elif isinstance(column_type, sa.Enum):
            schema["type"] = "string"
            if column_type.enums:
                schema["constraints"]["enum"] = list(column_type.enums)
        
        # Add constraints based on column properties
        if column.primary_key:
            # Primary keys are special - might want to handle differently
            pass
        
        if not column.nullable:
            schema["constraints"]["required"] = True
        
        return schema
    
    def _pydantic_field_to_schema(self, field: Any) -> Dict[str, Any]:
        """
        Convert a Pydantic field to a schema for data generation.
        
        Args:
            field: Pydantic field
            
        Returns:
            Schema for data generation
        """
        schema = {
            "type": "string",  # Default type
            "format": None,
            "constraints": {}
        }
        
        # Get field type
        field_type = field.type_
        
        # Convert field type to schema
        schema = self._field_to_schema(field.name, field_type)
        
        # Add constraints from field
        if field.required:
            schema["constraints"]["required"] = True
        
        if field.default is not None and field.default != Ellipsis:
            schema["constraints"]["default"] = field.default
        
        # Add validator-derived constraints
        if hasattr(field, "validators") and field.validators:
            for validator in field.validators:
                if "regex" in validator.__name__:
                    # Extract regex pattern if possible
                    schema["constraints"]["pattern"] = str(validator.regex)
                elif "min_length" in validator.__name__:
                    schema["constraints"]["minLength"] = validator.min_length
                elif "max_length" in validator.__name__:
                    schema["constraints"]["maxLength"] = validator.max_length
        
        return schema