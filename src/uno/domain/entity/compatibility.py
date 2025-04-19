"""
Compatibility layer for legacy implementations.

This module provides compatibility classes and functions that redirect to the
new domain entity framework implementations. It is intended to help with migrating
existing code to the new framework.

IMPORTANT: This module is deprecated and will be removed in a future release.
All new code should directly use the classes and functions in the domain entity
framework.
"""

import warnings
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast, Union

from uno.domain.entity.base import EntityBase
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.repository_memory import InMemoryRepository
from uno.domain.entity.repository_sqlalchemy import SQLAlchemyRepository, EntityMapper
from uno.domain.entity.specification.base import Specification
from uno.domain.entity.specification.composite import (
    AndSpecification, OrSpecification, NotSpecification,
    AllSpecification, AnySpecification
)
from uno.domain.entity.service import (
    DomainService, DomainServiceWithUnitOfWork, 
    ApplicationService, CrudService, ServiceFactory
)

# Type variables from legacy implementations
T = TypeVar("T", bound=EntityBase)  # Entity type
ID = TypeVar("ID")  # ID type
InputT = TypeVar("InputT")  # Input type
OutputT = TypeVar("OutputT")  # Output type

# Repository Compatibility Classes

class LegacyRepositoryBase(EntityRepository[T, ID], Generic[T, ID]):
    """
    Compatibility class for legacy repository base.
    
    This class implements the legacy repository interface but delegates to
    the new EntityRepository implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacyRepositoryBase is deprecated. "
            "Use uno.domain.entity.repository.EntityRepository instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class LegacyInMemoryRepository(InMemoryRepository[T, ID], Generic[T, ID]):
    """
    Compatibility class for legacy in-memory repository.
    
    This class implements the legacy in-memory repository interface but delegates
    to the new InMemoryRepository implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacyInMemoryRepository is deprecated. "
            "Use uno.domain.entity.repository_memory.InMemoryRepository instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class LegacySQLAlchemyRepository(SQLAlchemyRepository[T, ID, Any], Generic[T, ID]):
    """
    Compatibility class for legacy SQLAlchemy repository.
    
    This class implements the legacy SQLAlchemy repository interface but delegates
    to the new SQLAlchemyRepository implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacySQLAlchemyRepository is deprecated. "
            "Use uno.domain.entity.repository_sqlalchemy.SQLAlchemyRepository instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


# Specification Compatibility Classes

class LegacySpecification(Specification[T], Generic[T]):
    """
    Compatibility class for legacy specification.
    
    This class implements the legacy specification interface but delegates to
    the new Specification implementation.
    """
    
    def __init__(self):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacySpecification is deprecated. "
            "Use uno.domain.entity.specification.base.Specification instead.",
            DeprecationWarning,
            stacklevel=2
        )


class LegacyAndSpecification(AndSpecification[T], Generic[T]):
    """
    Compatibility class for legacy AND specification.
    
    This class implements the legacy AND specification interface but delegates to
    the new AndSpecification implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacyAndSpecification is deprecated. "
            "Use uno.domain.entity.specification.composite.AndSpecification instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class LegacyOrSpecification(OrSpecification[T], Generic[T]):
    """
    Compatibility class for legacy OR specification.
    
    This class implements the legacy OR specification interface but delegates to
    the new OrSpecification implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacyOrSpecification is deprecated. "
            "Use uno.domain.entity.specification.composite.OrSpecification instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class LegacyNotSpecification(NotSpecification[T], Generic[T]):
    """
    Compatibility class for legacy NOT specification.
    
    This class implements the legacy NOT specification interface but delegates to
    the new NotSpecification implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacyNotSpecification is deprecated. "
            "Use uno.domain.entity.specification.composite.NotSpecification instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


# Service Compatibility Classes

class LegacyDomainService(DomainService[T, ID], Generic[T, ID]):
    """
    Compatibility class for legacy domain service.
    
    This class implements the legacy domain service interface but delegates to
    the new DomainService implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacyDomainService is deprecated. "
            "Use uno.domain.entity.service.DomainService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class LegacyApplicationService(ApplicationService[InputT, OutputT], Generic[InputT, OutputT]):
    """
    Compatibility class for legacy application service.
    
    This class implements the legacy application service interface but delegates to
    the new ApplicationService implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacyApplicationService is deprecated. "
            "Use uno.domain.entity.service.ApplicationService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


class LegacyCrudService(CrudService[T, ID], Generic[T, ID]):
    """
    Compatibility class for legacy CRUD service.
    
    This class implements the legacy CRUD service interface but delegates to
    the new CrudService implementation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "LegacyCrudService is deprecated. "
            "Use uno.domain.entity.service.CrudService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


# Legacy Factory Functions

def legacy_create_service(*args, **kwargs) -> Any:
    """
    Compatibility function for legacy service creation.
    
    This function redirects to the new ServiceFactory implementation.
    """
    warnings.warn(
        "legacy_create_service is deprecated. "
        "Use uno.domain.entity.service.ServiceFactory instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Create a service factory and return a domain service
    factory = ServiceFactory(args[0])
    return factory.create_domain_service()


def legacy_create_crud_service(*args, **kwargs) -> Any:
    """
    Compatibility function for legacy CRUD service creation.
    
    This function redirects to the new ServiceFactory implementation.
    """
    warnings.warn(
        "legacy_create_crud_service is deprecated. "
        "Use uno.domain.entity.service.ServiceFactory instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Create a service factory and return a CRUD service
    factory = ServiceFactory(args[0])
    return factory.create_crud_service()