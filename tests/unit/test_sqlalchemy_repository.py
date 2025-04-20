import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from uno.domain.entity.repository_sqlalchemy import SQLAlchemyRepository, EntityMapper
from uno.domain.entity.base import EntityBase
from uno.core.errors.framework import Result, Success, Failure, ErrorDetail

# Example entity and model for testing
class DummyEntity(EntityBase):
    def __init__(self, id, name):
        self.id = id
        self.name = name

class DummyModel:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class DummyMapper(EntityMapper):
    entity_type = DummyEntity
    model_type = DummyModel
    def to_entity(self, model):
        return DummyEntity(model.id, model.name)
    def to_model(self, entity):
        return DummyModel(entity.id, entity.name)

@pytest.fixture
def dummy_session():
    session = AsyncMock(spec=AsyncSession)
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    return session

@pytest.fixture
def dummy_mapper():
    return DummyMapper()

@pytest.fixture
def repository(dummy_session, dummy_mapper):
    return SQLAlchemyRepository(session=dummy_session, mapper=dummy_mapper)

@pytest.mark.asyncio
async def test_add_success(repository, dummy_session):
    entity = DummyEntity(id=None, name="Alice")
    dummy_session.flush.return_value = None
    dummy_session.refresh.return_value = None
    result = await repository.add(entity)
    assert isinstance(result, Success)
    assert isinstance(result.value(), DummyEntity)

@pytest.mark.asyncio
async def test_add_failure_exists(repository, dummy_session):
    entity = DummyEntity(id="1", name="Bob")
    # Patch exists to return True
    repository.exists = AsyncMock(return_value=Success(True, convert=True))
    result = await repository.add(entity)
    assert isinstance(result, Failure)
    assert "already exists" in result.error()

@pytest.mark.asyncio
async def test_add_db_error(repository, dummy_session):
    entity = DummyEntity(id=None, name="Charlie")
    dummy_session.flush.side_effect = SQLAlchemyError("db error")
    result = await repository.add(entity)
    assert isinstance(result, Failure)
    assert "Database error" in result.error()

@pytest.mark.asyncio
async def test_get_success(repository, dummy_session):
    entity = DummyEntity(id="2", name="Dana")
    model = DummyModel(id="2", name="Dana")
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = model
    dummy_session.execute.return_value = dummy_result
    repository.mapper.to_entity = MagicMock(return_value=entity)
    result = await repository.get("2")
    assert isinstance(result, Success)
    assert isinstance(result.value(), DummyEntity)

@pytest.mark.asyncio
async def test_get_not_found(repository, dummy_session):
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = None
    dummy_session.execute.return_value = dummy_result
    result = await repository.get("999")
    assert isinstance(result, Success)
    assert result.value() is None

@pytest.mark.asyncio
async def test_get_db_error(repository, dummy_session):
    dummy_session.execute.side_effect = SQLAlchemyError("db error")
    result = await repository.get("err")
    assert isinstance(result, Failure)
    assert "Database error" in result.error()

@pytest.mark.asyncio
async def test_update_success(repository, dummy_session):
    entity = DummyEntity(id="3", name="Eve")
    repository.exists = AsyncMock(return_value=Success(True, convert=True))
    dummy_session.flush.return_value = None
    repository.mapper.to_entity = MagicMock(return_value=entity)
    result = await repository.update(entity)
    assert isinstance(result, Success)
    assert isinstance(result.value(), DummyEntity)

@pytest.mark.asyncio
async def test_update_not_found(repository, dummy_session):
    entity = DummyEntity(id="4", name="Frank")
    repository.exists = AsyncMock(return_value=Success(False, convert=True))
    result = await repository.update(entity)
    assert isinstance(result, Failure)
    assert "does not exist" in result.error()

@pytest.mark.asyncio
async def test_delete_success(repository, dummy_session):
    entity = DummyEntity(id="5", name="Grace")
    result = await repository.delete(entity)
    assert isinstance(result, Success)
    assert result.value() is True

@pytest.mark.asyncio
async def test_delete_db_error(repository, dummy_session):
    entity = DummyEntity(id="6", name="Heidi")
    dummy_session.delete.side_effect = SQLAlchemyError("db error")
    result = await repository.delete(entity)
    assert isinstance(result, Failure)
    assert "Database error" in result.error()

@pytest.mark.asyncio
async def test_list_success(repository, dummy_session):
    model1 = DummyModel(id="7", name="Ivan")
    model2 = DummyModel(id="8", name="Judy")
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [model1, model2]
    dummy_session.execute.return_value = dummy_result
    repository.mapper.to_entity = MagicMock(side_effect=[DummyEntity("7", "Ivan"), DummyEntity("8", "Judy")])
    result = await repository.list()
    assert isinstance(result, Success)
    assert isinstance(result.value(), list)
    assert len(result.value()) == 2

@pytest.mark.asyncio
async def test_list_db_error(repository, dummy_session):
    dummy_session.execute.side_effect = SQLAlchemyError("db error")
    result = await repository.list()
    assert isinstance(result, Failure)
    assert "Database error" in result.error()
