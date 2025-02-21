import pytest
from sqlalchemy.exc import IntegrityError
from uno.db.base import SessionLocal
from uno.auth.tables import User, Group, Role

@pytest.fixture(scope="module")
def db_session():
    """Fixture to create a new database session for testing."""
    session = SessionLocal()
    yield session
    session.close()

def test_create_user(db_session):
    """Test creating a new user."""
    new_user = User(email="test@example.com", handle="testuser")
    db_session.add(new_user)
    db_session.commit()

    assert new_user.id is not None
    assert new_user.email == "test@example.com"
    assert new_user.handle == "testuser"

def test_create_group(db_session):
    """Test creating a new group."""
    new_group = Group(name="Test Group")
    db_session.add(new_group)
    db_session.commit()

    assert new_group.id is not None
    assert new_group.name == "Test Group"

def test_create_role(db_session):
    """Test creating a new role."""
    new_role = Role(name="Test Role", description="A role for testing")
    db_session.add(new_role)
    db_session.commit()

    assert new_role.id is not None
    assert new_role.name == "Test Role"
    assert new_role.description == "A role for testing"

def test_user_group_relationship(db_session):
    """Test the relationship between users and groups."""
    user = db_session.query(User).filter_by(email="test@example.com").first()
    group = db_session.query(Group).filter_by(name="Test Group").first()

    user.groups.append(group)
    db_session.commit()

    assert group in user.groups

def test_user_role_relationship(db_session):
    """Test the relationship between users and roles."""
    user = db_session.query(User).filter_by(email="test@example.com").first()
    role = db_session.query(Role).filter_by(name="Test Role").first()

    user.roles.append(role)
    db_session.commit()

    assert role in user.roles

def test_group_role_relationship(db_session):
    """Test the relationship between groups and roles."""
    group = db_session.query(Group).filter_by(name="Test Group").first()
    role = db_session.query(Role).filter_by(name="Test Role").first()

    group.roles.append(role)
    db_session.commit()

    assert role in group.roles

def test_user_unique_email_constraint(db_session):
    """Test the unique constraint on user email."""
    new_user = User(email="test@example.com", handle="anotheruser")
    db_session.add(new_user)

    with pytest.raises(IntegrityError):
        db_session.commit()
        db_session.rollback()
