"""
Domain Entity Framework for UNO

This package provides the Domain Entity framework, the foundation of the
Domain-Driven Design (DDD) implementation in UNO. It contains base classes 
and utilities for creating rich domain models with proper encapsulation,
identity management, and business rule enforcement.

Key components:
- EntityBase: Base class for all domain entities
- AggregateRoot: Base class for aggregate roots
- ValueObject: Base class for value objects
- Identity: Utilities for entity identity management
- Specification: Classes for implementing the Specification pattern
- Repository: Implementation of the Repository pattern with specification support
"""

from uno.domain.entity.base import EntityBase
from uno.domain.entity.identity import Identity, IdentityGenerator
from uno.domain.entity.value_object import ValueObject
from uno.domain.entity.aggregate import AggregateRoot
from uno.domain.entity.protocols import EntityProtocol, AggregateRootProtocol, ValueObjectProtocol
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.repository_memory import InMemoryRepository
from uno.domain.entity.repository_sqlalchemy import SQLAlchemyRepository, EntityMapper
from uno.domain.entity.service import (
    DomainService, DomainServiceWithUnitOfWork, 
    ApplicationService, CrudService, ServiceFactory
)

# Import specification subpackage
from uno.domain.entity.specification import (
    Specification,
    PredicateSpecification,
    AttributeSpecification,
    CompositeSpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    AllSpecification,
    AnySpecification,
    SpecificationTranslator,
    SQLSpecificationTranslator,
    PostgreSQLSpecificationTranslator
)

__all__ = [
    # Entity framework
    'EntityBase',
    'Identity',
    'IdentityGenerator',
    'ValueObject',
    'AggregateRoot',
    
    # Protocols
    'EntityProtocol',
    'AggregateRootProtocol',
    'ValueObjectProtocol',
    
    # Repository
    'EntityRepository',
    'InMemoryRepository',
    'SQLAlchemyRepository',
    'EntityMapper',
    
    # Service
    'DomainService',
    'DomainServiceWithUnitOfWork',
    'ApplicationService',
    'CrudService',
    'ServiceFactory',
    
    # Specification pattern
    'Specification',
    'PredicateSpecification',
    'AttributeSpecification',
    'CompositeSpecification',
    'AndSpecification',
    'OrSpecification',
    'NotSpecification',
    'AllSpecification',
    'AnySpecification',
    'SpecificationTranslator',
    'SQLSpecificationTranslator',
    'PostgreSQLSpecificationTranslator'
]