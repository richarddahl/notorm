"""
Example demonstrating the use of the EntityRepository with the Specification pattern.

This example shows how to:
1. Create domain entities
2. Define specifications for querying
3. Use the repository to query and modify entities
4. Use specifications with in-memory and SQLAlchemy repositories
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from uno.domain.entity.base import EntityBase
from uno.domain.entity.identity import Identity
from uno.domain.entity.specification.base import Specification, AttributeSpecification
from uno.domain.entity.specification.composite import AndSpecification, OrSpecification, NotSpecification
from uno.domain.entity.repository_memory import InMemoryRepository
from uno.domain.entity.repository_sqlalchemy import SQLAlchemyRepository, EntityMapper


# Define a domain entity
class User(EntityBase[uuid.UUID]):
    """Example user entity."""
    
    name: str
    email: str
    is_active: bool = True
    last_login: Optional[datetime] = None


# Define specifications for querying users
class ActiveUserSpecification(Specification[User]):
    """Specification for active users."""
    
    def is_satisfied_by(self, candidate: User) -> bool:
        """Check if the user is active."""
        return candidate.is_active


class RecentLoginSpecification(Specification[User]):
    """Specification for users who have logged in recently."""
    
    def __init__(self, days: int = 30):
        """
        Initialize the specification.
        
        Args:
            days: Number of days to consider recent
        """
        self.days = days
    
    def is_satisfied_by(self, candidate: User) -> bool:
        """Check if the user has logged in recently."""
        if not candidate.last_login:
            return False
        
        cutoff = datetime.now() - timedelta(days=self.days)
        return candidate.last_login >= cutoff


class EmailDomainSpecification(Specification[User]):
    """Specification for users with email in a specific domain."""
    
    def __init__(self, domain: str):
        """
        Initialize the specification.
        
        Args:
            domain: Email domain to match
        """
        self.domain = domain
    
    def is_satisfied_by(self, candidate: User) -> bool:
        """Check if the user's email matches the domain."""
        return candidate.email.endswith(f"@{self.domain}")


# Define SQLAlchemy model for persistence
SQLBase = declarative_base()


class UserModel(SQLBase):
    """SQLAlchemy model for User entity."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


# Define mapper functions
def model_to_entity(model: UserModel) -> User:
    """Convert UserModel to User entity."""
    return User(
        id=uuid.UUID(model.id),
        name=model.name,
        email=model.email,
        is_active=model.is_active,
        last_login=model.last_login,
        created_at=model.created_at,
        updated_at=model.updated_at
    )


def entity_to_model(entity: User) -> UserModel:
    """Convert User entity to UserModel."""
    return UserModel(
        id=str(entity.id),
        name=entity.name,
        email=entity.email,
        is_active=entity.is_active,
        last_login=entity.last_login,
        created_at=entity.created_at,
        updated_at=entity.updated_at
    )


async def in_memory_repository_example():
    """Example of using the InMemoryRepository with specifications."""
    print("\n--- In-Memory Repository Example ---")
    
    # Create repository
    repository = InMemoryRepository[User, uuid.UUID](User)
    
    # Create test users
    users = [
        User(
            id=uuid.uuid4(),
            name="Alice Smith",
            email="alice@example.com",
            is_active=True,
            last_login=datetime.now() - timedelta(days=5)
        ),
        User(
            id=uuid.uuid4(),
            name="Bob Johnson",
            email="bob@example.com",
            is_active=True,
            last_login=datetime.now() - timedelta(days=45)
        ),
        User(
            id=uuid.uuid4(),
            name="Charlie Brown",
            email="charlie@acme.com",
            is_active=False,
            last_login=datetime.now() - timedelta(days=3)
        ),
        User(
            id=uuid.uuid4(),
            name="Dave Miller",
            email="dave@acme.com",
            is_active=True,
            last_login=None
        )
    ]
    
    # Add users to repository
    await repository.add_many(users)
    print(f"Added {len(users)} users to repository")
    
    # Define specifications
    active_spec = ActiveUserSpecification()
    recent_login_spec = RecentLoginSpecification(days=10)
    acme_email_spec = EmailDomainSpecification("acme.com")
    example_email_spec = EmailDomainSpecification("example.com")
    
    # Test composite specifications
    active_recent_spec = active_spec.and_(recent_login_spec)
    active_acme_spec = active_spec.and_(acme_email_spec)
    any_email_spec = acme_email_spec.or_(example_email_spec)
    
    # Query with specifications
    active_users = await repository.find(active_spec)
    print(f"\nActive users: {len(active_users)}")
    for user in active_users:
        print(f"  - {user.name} ({user.email})")
    
    recent_active_users = await repository.find(active_recent_spec)
    print(f"\nActive users with recent login: {len(recent_active_users)}")
    for user in recent_active_users:
        print(f"  - {user.name} ({user.email}) - Last login: {user.last_login}")
    
    active_acme_users = await repository.find(active_acme_spec)
    print(f"\nActive users with acme.com email: {len(active_acme_users)}")
    for user in active_acme_users:
        print(f"  - {user.name} ({user.email})")
    
    users_any_email = await repository.find(any_email_spec)
    print(f"\nUsers with acme.com or example.com email: {len(users_any_email)}")
    for user in users_any_email:
        print(f"  - {user.name} ({user.email}) - Active: {user.is_active}")
    
    # Use NOT specification
    not_active_spec = active_spec.not_()
    inactive_users = await repository.find(not_active_spec)
    print(f"\nInactive users: {len(inactive_users)}")
    for user in inactive_users:
        print(f"  - {user.name} ({user.email})")
    
    # Use find_one
    active_acme_user = await repository.find_one(active_acme_spec)
    if active_acme_user:
        print(f"\nFound active acme.com user: {active_acme_user.name} ({active_acme_user.email})")
    
    # Count with specification
    count = await repository.count(acme_email_spec)
    print(f"\nNumber of users with acme.com email: {count}")


async def sqlalchemy_repository_example():
    """Example of using the SQLAlchemyRepository with specifications."""
    print("\n--- SQLAlchemy Repository Example ---")
    
    # Setup SQLAlchemy
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLBase.metadata.create_all)
    
    # Create session and repository
    async with async_session() as session:
        mapper = EntityMapper(User, UserModel, model_to_entity, entity_to_model)
        repository = SQLAlchemyRepository[User, uuid.UUID, UserModel](session, mapper)
        
        # Create test users (same as in-memory example)
        users = [
            User(
                id=uuid.uuid4(),
                name="Alice Smith",
                email="alice@example.com",
                is_active=True,
                last_login=datetime.now() - timedelta(days=5)
            ),
            User(
                id=uuid.uuid4(),
                name="Bob Johnson",
                email="bob@example.com",
                is_active=True,
                last_login=datetime.now() - timedelta(days=45)
            ),
            User(
                id=uuid.uuid4(),
                name="Charlie Brown",
                email="charlie@acme.com",
                is_active=False,
                last_login=datetime.now() - timedelta(days=3)
            ),
            User(
                id=uuid.uuid4(),
                name="Dave Miller",
                email="dave@acme.com",
                is_active=True,
                last_login=None
            )
        ]
        
        # Add users to repository
        await repository.add_many(users)
        await session.commit()
        print(f"Added {len(users)} users to repository")
        
        # Define specifications (same as in-memory example)
        active_spec = ActiveUserSpecification()
        recent_login_spec = RecentLoginSpecification(days=10)
        acme_email_spec = EmailDomainSpecification("acme.com")
        
        # Define SQL-friendly specifications using AttributeSpecification
        sql_active_spec = AttributeSpecification("is_active", True)
        sql_acme_email_spec = AttributeSpecification(
            "email", 
            "acme.com",
            lambda email, domain: email.endswith(f"@{domain}")
        )
        
        # Test composite specifications that mix SQL-friendly and complex specs
        mixed_spec = sql_active_spec.and_(recent_login_spec)
        
        # Query with specifications
        active_users = await repository.find(sql_active_spec)
        print(f"\nActive users (SQL): {len(active_users)}")
        for user in active_users:
            print(f"  - {user.name} ({user.email})")
        
        # Query with complex specification (will use in-memory filtering)
        recent_active_users = await repository.find(mixed_spec)
        print(f"\nActive users with recent login (mixed SQL/in-memory): {len(recent_active_users)}")
        for user in recent_active_users:
            print(f"  - {user.name} ({user.email}) - Last login: {user.last_login}")
        
        # Stream results with specification
        print("\nStreaming active users:")
        async for user in repository.stream(sql_active_spec):
            print(f"  - {user.name} ({user.email})")
        
        # Modify entity and update
        alice = await repository.find_one(AttributeSpecification("name", "Alice Smith"))
        if alice:
            alice.last_login = datetime.now()
            await repository.update(alice)
            await session.commit()
            print(f"\nUpdated {alice.name}'s last login to {alice.last_login}")
        
        # Delete entity
        bob = await repository.find_one(AttributeSpecification("name", "Bob Johnson"))
        if bob:
            await repository.delete(bob)
            await session.commit()
            print(f"\nDeleted user: {bob.name}")
        
        # Verify deletion
        count = await repository.count(AttributeSpecification("name", "Bob Johnson"))
        print(f"Users named Bob Johnson left: {count}")


async def main():
    """Run the repository examples."""
    await in_memory_repository_example()
    await sqlalchemy_repository_example()


if __name__ == "__main__":
    asyncio.run(main())