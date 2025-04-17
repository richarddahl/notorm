"""
Tests for enhanced specifications.
"""

import re
from datetime import datetime, date, timezone
import pytest

from uno.domain.models import Entity
from uno.domain.specifications import (
    RangeSpecification,
    DateRangeSpecification,
    TextMatchSpecification,
    InListSpecification,
    NotInListSpecification,
    ComparableSpecification,
    NullSpecification,
    NotNullSpecification,
    enhance_specification_factory,
    specification_factory,
)

# Test entity
class TestEntity(Entity):
    """Test entity for specification tests."""
    
    def __init__(
        self,
        id: str = "1",
        name: str = "Test",
        age: int = 30,
        active: bool = True,
        score: float = 85.5,
        created_at: datetime = None,
        tags: list = None,
        optional_field: str = None,
        **kwargs
    ):
        super().__init__(id=id, **kwargs)
        self.name = name
        self.age = age
        self.active = active
        self.score = score
        self.created_at = created_at or datetime.now(timezone.utc)
        self.tags = tags or ["test", "example"]
        self.optional_field = optional_field


# Create enhanced specification factory for testing
TestSpecification = specification_factory(TestEntity)
EnhancedTestSpecification = enhance_specification_factory(TestSpecification)


class TestRangeSpecification:
    """Tests for RangeSpecification."""
    
    def test_range_specification_inclusive(self):
        """Test RangeSpecification with inclusive bounds."""
        entity = TestEntity(age=30)
        spec = RangeSpecification("age", 20, 40, include_min=True, include_max=True)
        
        assert spec.is_satisfied_by(entity) is True
        
        # Test boundary conditions
        entity.age = 20
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 40
        assert spec.is_satisfied_by(entity) is True
        
        # Test outside range
        entity.age = 19
        assert spec.is_satisfied_by(entity) is False
        
        entity.age = 41
        assert spec.is_satisfied_by(entity) is False
    
    def test_range_specification_exclusive(self):
        """Test RangeSpecification with exclusive bounds."""
        entity = TestEntity(age=30)
        spec = RangeSpecification("age", 20, 40, include_min=False, include_max=False)
        
        assert spec.is_satisfied_by(entity) is True
        
        # Test boundary conditions
        entity.age = 20
        assert spec.is_satisfied_by(entity) is False
        
        entity.age = 40
        assert spec.is_satisfied_by(entity) is False
        
        entity.age = 21
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 39
        assert spec.is_satisfied_by(entity) is True
    
    def test_range_specification_missing_attribute(self):
        """Test RangeSpecification with missing attribute."""
        entity = TestEntity()
        spec = RangeSpecification("missing", 20, 40)
        
        assert spec.is_satisfied_by(entity) is False
    
    def test_range_factory_method(self):
        """Test range factory method."""
        entity = TestEntity(score=75.5)
        spec = EnhancedTestSpecification.range("score", 70.0, 80.0)
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.score = 69.9
        assert spec.is_satisfied_by(entity) is False
        
        entity.score = 80.1
        assert spec.is_satisfied_by(entity) is False


class TestDateRangeSpecification:
    """Tests for DateRangeSpecification."""
    
    def test_date_range_specification(self):
        """Test DateRangeSpecification."""
        today = date.today()
        yesterday = date(today.year, today.month, today.day - 1)
        tomorrow = date(today.year, today.month, today.day + 1)
        
        entity = TestEntity(created_at=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc))
        spec = DateRangeSpecification("created_at", 
                                     datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc), 
                                     datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc))
        
        assert spec.is_satisfied_by(entity) is True
        
        # Test boundary conditions
        entity.created_at = datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc)
        assert spec.is_satisfied_by(entity) is True
        
        entity.created_at = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc)
        assert spec.is_satisfied_by(entity) is True
        
        # Test exclusive bounds
        spec = DateRangeSpecification("created_at", 
                                     datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc), 
                                     datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc),
                                     include_start=False,
                                     include_end=False)
        
        entity.created_at = datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc)
        assert spec.is_satisfied_by(entity) is False
        
        entity.created_at = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc)
        assert spec.is_satisfied_by(entity) is False
        
        entity.created_at = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
        assert spec.is_satisfied_by(entity) is True
    
    def test_date_range_factory_method(self):
        """Test date_range factory method."""
        today = date.today()
        yesterday = date(today.year, today.month, today.day - 1)
        tomorrow = date(today.year, today.month, today.day + 1)
        
        entity = TestEntity(created_at=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc))
        spec = EnhancedTestSpecification.date_range(
            "created_at", 
            datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc), 
            datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc)
        )
        
        assert spec.is_satisfied_by(entity) is True


class TestTextMatchSpecification:
    """Tests for TextMatchSpecification."""
    
    def test_contains_match(self):
        """Test text match with contains."""
        entity = TestEntity(name="John Doe")
        spec = TextMatchSpecification("name", "John", "contains")
        
        assert spec.is_satisfied_by(entity) is True
        
        spec = TextMatchSpecification("name", "Jane", "contains")
        assert spec.is_satisfied_by(entity) is False
    
    def test_starts_with_match(self):
        """Test text match with starts_with."""
        entity = TestEntity(name="John Doe")
        spec = TextMatchSpecification("name", "John", "starts_with")
        
        assert spec.is_satisfied_by(entity) is True
        
        spec = TextMatchSpecification("name", "Doe", "starts_with")
        assert spec.is_satisfied_by(entity) is False
    
    def test_ends_with_match(self):
        """Test text match with ends_with."""
        entity = TestEntity(name="John Doe")
        spec = TextMatchSpecification("name", "Doe", "ends_with")
        
        assert spec.is_satisfied_by(entity) is True
        
        spec = TextMatchSpecification("name", "John", "ends_with")
        assert spec.is_satisfied_by(entity) is False
    
    def test_exact_match(self):
        """Test text match with exact."""
        entity = TestEntity(name="John Doe")
        spec = TextMatchSpecification("name", "John Doe", "exact")
        
        assert spec.is_satisfied_by(entity) is True
        
        spec = TextMatchSpecification("name", "John", "exact")
        assert spec.is_satisfied_by(entity) is False
    
    def test_regex_match(self):
        """Test text match with regex."""
        entity = TestEntity(name="John Doe")
        spec = TextMatchSpecification("name", r"John\s+\w+", "regex")
        
        assert spec.is_satisfied_by(entity) is True
        
        spec = TextMatchSpecification("name", r"Jane\s+\w+", "regex")
        assert spec.is_satisfied_by(entity) is False
    
    def test_case_sensitivity(self):
        """Test text match with case sensitivity."""
        entity = TestEntity(name="John Doe")
        
        # Case-insensitive (default)
        spec = TextMatchSpecification("name", "john", "contains")
        assert spec.is_satisfied_by(entity) is True
        
        # Case-sensitive
        spec = TextMatchSpecification("name", "john", "contains", case_sensitive=True)
        assert spec.is_satisfied_by(entity) is False
    
    def test_text_match_factory_methods(self):
        """Test text match factory methods."""
        entity = TestEntity(name="John Doe")
        
        assert EnhancedTestSpecification.contains("name", "john").is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.starts_with("name", "john").is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.ends_with("name", "doe").is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.exact_match("name", "John Doe").is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.regex_match("name", r"j.*\s+d.*", case_sensitive=False).is_satisfied_by(entity) is True


class TestListSpecifications:
    """Tests for InListSpecification and NotInListSpecification."""
    
    def test_in_list_specification(self):
        """Test InListSpecification."""
        entity = TestEntity(name="John")
        spec = InListSpecification("name", ["John", "Jane", "Bob"])
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.name = "Alice"
        assert spec.is_satisfied_by(entity) is False
    
    def test_not_in_list_specification(self):
        """Test NotInListSpecification."""
        entity = TestEntity(name="John")
        spec = NotInListSpecification("name", ["Jane", "Bob", "Alice"])
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.name = "Jane"
        assert spec.is_satisfied_by(entity) is False
    
    def test_list_factory_methods(self):
        """Test list factory methods."""
        entity = TestEntity(name="John")
        
        assert EnhancedTestSpecification.in_list("name", ["John", "Jane"]).is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.not_in_list("name", ["Jane", "Bob"]).is_satisfied_by(entity) is True


class TestComparableSpecification:
    """Tests for ComparableSpecification."""
    
    def test_equal_comparison(self):
        """Test equal comparison."""
        entity = TestEntity(age=30)
        spec = ComparableSpecification("age", 30, "eq")
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 31
        assert spec.is_satisfied_by(entity) is False
    
    def test_not_equal_comparison(self):
        """Test not equal comparison."""
        entity = TestEntity(age=30)
        spec = ComparableSpecification("age", 31, "neq")
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 31
        assert spec.is_satisfied_by(entity) is False
    
    def test_greater_than_comparison(self):
        """Test greater than comparison."""
        entity = TestEntity(age=30)
        spec = ComparableSpecification("age", 25, "gt")
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 25
        assert spec.is_satisfied_by(entity) is False
        
        entity.age = 24
        assert spec.is_satisfied_by(entity) is False
    
    def test_greater_than_or_equal_comparison(self):
        """Test greater than or equal comparison."""
        entity = TestEntity(age=30)
        spec = ComparableSpecification("age", 25, "gte")
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 25
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 24
        assert spec.is_satisfied_by(entity) is False
    
    def test_less_than_comparison(self):
        """Test less than comparison."""
        entity = TestEntity(age=30)
        spec = ComparableSpecification("age", 35, "lt")
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 35
        assert spec.is_satisfied_by(entity) is False
        
        entity.age = 36
        assert spec.is_satisfied_by(entity) is False
    
    def test_less_than_or_equal_comparison(self):
        """Test less than or equal comparison."""
        entity = TestEntity(age=30)
        spec = ComparableSpecification("age", 35, "lte")
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 35
        assert spec.is_satisfied_by(entity) is True
        
        entity.age = 36
        assert spec.is_satisfied_by(entity) is False
    
    def test_comparison_factory_methods(self):
        """Test comparison factory methods."""
        entity = TestEntity(age=30)
        
        assert EnhancedTestSpecification.eq("age", 30).is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.neq("age", 31).is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.gt("age", 25).is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.gte("age", 30).is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.lt("age", 35).is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.lte("age", 30).is_satisfied_by(entity) is True


class TestNullSpecifications:
    """Tests for NullSpecification and NotNullSpecification."""
    
    def test_null_specification(self):
        """Test NullSpecification."""
        entity = TestEntity(optional_field=None)
        spec = NullSpecification("optional_field")
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.optional_field = "value"
        assert spec.is_satisfied_by(entity) is False
    
    def test_not_null_specification(self):
        """Test NotNullSpecification."""
        entity = TestEntity(optional_field="value")
        spec = NotNullSpecification("optional_field")
        
        assert spec.is_satisfied_by(entity) is True
        
        entity.optional_field = None
        assert spec.is_satisfied_by(entity) is False
    
    def test_null_factory_methods(self):
        """Test null factory methods."""
        entity = TestEntity(optional_field=None)
        
        assert EnhancedTestSpecification.is_null("optional_field").is_satisfied_by(entity) is True
        assert EnhancedTestSpecification.is_not_null("name").is_satisfied_by(entity) is True


class TestCompositeSpecifications:
    """Tests for composite specifications using the enhanced factory."""
    
    def test_composite_specifications(self):
        """Test composite specifications."""
        entity = TestEntity(name="John Doe", age=30, active=True)
        
        # Active user named John who is 30 or older
        spec = (EnhancedTestSpecification.contains("name", "john")
                .and_(EnhancedTestSpecification.gte("age", 30))
                .and_(EnhancedTestSpecification.eq("active", True)))
        
        assert spec.is_satisfied_by(entity) is True
        
        # Change age to make spec fail
        entity.age = 29
        assert spec.is_satisfied_by(entity) is False
        
        # User is either named John or is older than 40
        spec = (EnhancedTestSpecification.contains("name", "john")
                .or_(EnhancedTestSpecification.gt("age", 40)))
        
        assert spec.is_satisfied_by(entity) is True
        
        # User is not named Jane and is younger than 50
        spec = (EnhancedTestSpecification.contains("name", "jane").not_()
                .and_(EnhancedTestSpecification.lt("age", 50)))
        
        assert spec.is_satisfied_by(entity) is True