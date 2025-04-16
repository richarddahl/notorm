import pytest
from datetime import datetime, UTC
from unittest import mock

from uno.messaging.entities import Message, MessageUser
from uno.messaging.domain_repositories import MessageRepository
from uno.enums import MessageImportance
from uno.core.errors import EntityNotFoundError


class MockModel:
    """Base class for mock models."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockMessageModel(MockModel):
    """Mock MessageModel for testing."""
    pass


class MockMessageUserModel(MockModel):
    """Mock MessageUserModel for testing."""
    pass


class MockSession:
    """Mock database session for testing."""
    
    def __init__(self):
        self.data = {
            'messages': {},
            'message_users': {},
            'message__meta_record': {}
        }
        self.query_results = []
        self.added_models = []
        self.flushed = False
        self.deleted_models = []
        self.executed_statements = []
    
    def query(self, model_class):
        """Mock query method."""
        self.current_model = model_class
        self.current_filters = []
        return self
    
    def filter(self, *conditions):
        """Mock filter method."""
        self.current_filters.extend(conditions)
        return self
    
    def join(self, model_class, condition=None):
        """Mock join method."""
        self.joined_model = model_class
        self.join_condition = condition
        return self
    
    def order_by(self, *args):
        """Mock order_by method."""
        return self
    
    def offset(self, offset):
        """Mock offset method."""
        return self
    
    def limit(self, limit):
        """Mock limit method."""
        return self
    
    async def first(self):
        """Mock first method."""
        if not self.query_results:
            return None
        return self.query_results[0]
    
    async def all(self):
        """Mock all method."""
        return self.query_results
    
    async def add(self, model):
        """Mock add method."""
        self.added_models.append(model)
        
        # For MessageModel
        if hasattr(model, 'subject'):
            self.data['messages'][model.id] = model
        
        # For MessageUserModel
        if hasattr(model, 'message_id') and hasattr(model, 'user_id'):
            self.data['message_users'][model.id] = model
        
        return None
    
    async def flush(self):
        """Mock flush method."""
        self.flushed = True
        return None
    
    async def delete(self, model):
        """Mock delete method."""
        self.deleted_models.append(model)
        
        # Remove from in-memory data
        if hasattr(model, 'subject'):
            if model.id in self.data['messages']:
                del self.data['messages'][model.id]
        
        return None
    
    async def execute(self, statement):
        """Mock execute method."""
        self.executed_statements.append(statement)
        return None
    
    def set_query_results(self, results):
        """Set results to be returned by query methods."""
        self.query_results = results


class TestMessageRepository:
    
    @pytest.fixture
    def session(self):
        return MockSession()
    
    @pytest.fixture
    def repository(self, session):
        return MessageRepository(session)
    
    @pytest.mark.asyncio
    async def test_get_by_id_existing(self, repository, session):
        # Create a mock message model
        message_model = MockMessageModel(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body",
            flag=MessageImportance.INFORMATION,
            is_draft=True,
            sent_at=None,
            parent_id=None,
            users=[],
            meta_records=[]
        )
        
        # Set the mock to return this model
        session.set_query_results([message_model])
        
        # Get the message
        message = await repository.get_by_id("test_message_id")
        
        # Verify the message
        assert message is not None
        assert message.id == "test_message_id"
        assert message.subject == "Test Subject"
        assert message.body == "Test Body"
        assert message.flag == MessageImportance.INFORMATION
        assert message.is_draft is True
        assert message.sent_at is None
        assert message.parent_id is None
        assert message.users == []
        assert message.meta_record_ids == []
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, session):
        # Set the mock to return no results
        session.set_query_results([])
        
        # Get a non-existent message
        message = await repository.get_by_id("nonexistent_id")
        
        # Verify message is None
        assert message is None
    
    @pytest.mark.asyncio
    async def test_get_messages_for_user(self, repository, session):
        # Create mock message models
        message_model1 = MockMessageModel(
            id="message1",
            subject="Subject 1",
            body="Body 1",
            flag=MessageImportance.INFORMATION,
            is_draft=False,
            sent_at=datetime(2023, 1, 2, tzinfo=UTC),
            users=[
                MockMessageUserModel(
                    id="mu1",
                    message_id="message1",
                    user_id="user1",
                    is_sender=False,
                    is_addressee=True,
                    is_read=False
                )
            ],
            meta_records=[]
        )
        
        message_model2 = MockMessageModel(
            id="message2",
            subject="Subject 2",
            body="Body 2",
            flag=MessageImportance.INFORMATION,
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC),
            users=[
                MockMessageUserModel(
                    id="mu2",
                    message_id="message2",
                    user_id="user1",
                    is_sender=True,
                    is_addressee=False,
                    is_read=True
                )
            ],
            meta_records=[]
        )
        
        # Set the mock to return these models
        session.set_query_results([message_model1, message_model2])
        
        # Get messages for user
        messages = await repository.get_messages_for_user("user1")
        
        # Verify the messages
        assert len(messages) == 2
        assert messages[0].id == "message1"
        assert messages[1].id == "message2"
        
        # Test with only_unread=True
        session.set_query_results([message_model1])
        unread_messages = await repository.get_messages_for_user("user1", only_unread=True)
        
        assert len(unread_messages) == 1
        assert unread_messages[0].id == "message1"
    
    @pytest.mark.asyncio
    async def test_get_message_thread(self, repository, session):
        # Create a mock parent message model
        parent_message_model = MockMessageModel(
            id="parent_message",
            subject="Parent Subject",
            body="Parent Body",
            flag=MessageImportance.INFORMATION,
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC),
            users=[
                MockMessageUserModel(
                    id="mu1",
                    message_id="parent_message",
                    user_id="user1",
                    is_sender=True,
                    is_addressee=False,
                    is_read=True
                )
            ],
            meta_records=[]
        )
        
        # Create mock child message models
        child_message_model = MockMessageModel(
            id="child_message",
            subject="Re: Parent Subject",
            body="Child Body",
            flag=MessageImportance.INFORMATION,
            is_draft=False,
            sent_at=datetime(2023, 1, 2, tzinfo=UTC),
            parent_id="parent_message",
            users=[
                MockMessageUserModel(
                    id="mu2",
                    message_id="child_message",
                    user_id="user2",
                    is_sender=True,
                    is_addressee=False,
                    is_read=False
                )
            ],
            meta_records=[]
        )
        
        # Set up the mock to return the parent message first, then the child message
        session.set_query_results([parent_message_model])
        
        # Handle second query for child messages
        original_query = session.query
        
        def mock_query(model_class):
            if hasattr(session, 'query_count'):
                session.query_count += 1
            else:
                session.query_count = 1
            
            if session.query_count == 2:
                session.set_query_results([child_message_model])
            
            return original_query(model_class)
        
        session.query = mock_query
        
        # Get the message thread
        thread = await repository.get_message_thread("parent_message")
        
        # Verify the thread
        assert len(thread) == 2
        assert thread[0].id == "parent_message"
        assert thread[1].id == "child_message"
    
    @pytest.mark.asyncio
    async def test_get_message_thread_not_found(self, repository, session):
        # Set the mock to return no results
        session.set_query_results([])
        
        # Try to get a thread for a non-existent parent message
        with pytest.raises(EntityNotFoundError) as exc:
            await repository.get_message_thread("nonexistent_id")
        
        assert "Message with ID nonexistent_id not found" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_create_message(self, repository, session):
        # Create a message to be persisted
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body",
            flag=MessageImportance.HIGH,
            is_draft=True,
            meta_record_ids=["meta1", "meta2"]
        )
        
        # Add users to the message
        message.add_user(user_id="sender", is_sender=True)
        message.add_user(user_id="recipient", is_addressee=True)
        
        # Create the message
        result = await repository.create(message)
        
        # Verify the message was created
        assert result == message
        
        # Verify the session operations
        assert len(session.added_models) == 3  # 1 message + 2 message_users
        assert session.flushed
        
        # Check the message model
        message_model = next((m for m in session.added_models if hasattr(m, 'subject')), None)
        assert message_model is not None
        assert message_model.id == "test_message_id"
        assert message_model.subject == "Test Subject"
        assert message_model.body == "Test Body"
        assert message_model.flag == MessageImportance.HIGH
        assert message_model.is_draft is True
        
        # Check the message user models
        user_models = [m for m in session.added_models if hasattr(m, 'user_id')]
        assert len(user_models) == 2
        
        sender_model = next((m for m in user_models if m.is_sender), None)
        assert sender_model is not None
        assert sender_model.user_id == "sender"
        
        recipient_model = next((m for m in user_models if m.is_addressee), None)
        assert recipient_model is not None
        assert recipient_model.user_id == "recipient"
        
        # Check meta record associations
        assert len(session.executed_statements) == 2
        for statement in session.executed_statements:
            assert "INSERT INTO message__meta_record" in statement
            assert "test_message_id" in statement
            assert any(meta_id in statement for meta_id in ["meta1", "meta2"])
    
    @pytest.mark.asyncio
    async def test_update_message(self, repository, session):
        # Create a mock existing message model
        message_model = MockMessageModel(
            id="test_message_id",
            subject="Original Subject",
            body="Original Body",
            flag=MessageImportance.INFORMATION,
            is_draft=True,
            sent_at=None,
            parent_id=None,
            users=[
                MockMessageUserModel(
                    id="mu1",
                    message_id="test_message_id",
                    user_id="user1",
                    is_sender=True,
                    is_addressee=False,
                    is_read=False
                )
            ],
            meta_records=[]
        )
        
        # Set the mock to return this model
        session.set_query_results([message_model])
        
        # Create an updated message entity
        updated_message = Message(
            id="test_message_id",
            subject="Updated Subject",
            body="Updated Body",
            flag=MessageImportance.HIGH,
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC),
            meta_record_ids=["meta1"]
        )
        
        # Add users to the updated message
        updated_message.add_user(user_id="user1", is_sender=True)  # Keep existing user
        updated_message.add_user(user_id="user2", is_addressee=True)  # Add new user
        
        # Update the message
        result = await repository.update(updated_message)
        
        # Verify the result
        assert result == updated_message
        
        # Verify the session operations
        assert session.flushed
        
        # Check that message fields were updated
        assert message_model.subject == "Updated Subject"
        assert message_model.body == "Updated Body"
        assert message_model.flag == MessageImportance.HIGH
        assert message_model.is_draft is False
        assert message_model.sent_at == datetime(2023, 1, 1, tzinfo=UTC)
        
        # Check that a new message user was added for user2
        added_user_model = next((m for m in session.added_models if hasattr(m, 'user_id') and m.user_id == "user2"), None)
        assert added_user_model is not None
        assert added_user_model.is_addressee is True
        
        # Check meta record update
        assert len(session.executed_statements) == 2
        assert "DELETE FROM message__meta_record" in session.executed_statements[0]
        assert "INSERT INTO message__meta_record" in session.executed_statements[1]
        assert "meta1" in session.executed_statements[1]
    
    @pytest.mark.asyncio
    async def test_update_message_not_found(self, repository, session):
        # Set the mock to return no results
        session.set_query_results([])
        
        # Create a message entity
        message = Message(
            id="nonexistent_id",
            subject="Subject",
            body="Body"
        )
        
        # Try to update a non-existent message
        with pytest.raises(EntityNotFoundError) as exc:
            await repository.update(message)
        
        assert "Message with ID nonexistent_id not found" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_delete_message(self, repository, session):
        # Create a mock existing message model
        message_model = MockMessageModel(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Set the mock to return this model
        session.set_query_results([message_model])
        
        # Delete the message
        await repository.delete("test_message_id")
        
        # Verify the session operations
        assert len(session.deleted_models) == 1
        assert session.deleted_models[0].id == "test_message_id"
    
    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, repository, session):
        # Set the mock to return no results
        session.set_query_results([])
        
        # Try to delete a non-existent message
        with pytest.raises(EntityNotFoundError) as exc:
            await repository.delete("nonexistent_id")
        
        assert "Message with ID nonexistent_id not found" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_get_draft_messages_for_user(self, repository, session):
        # Create mock message models
        draft_message_model = MockMessageModel(
            id="draft_message",
            subject="Draft Subject",
            body="Draft Body",
            flag=MessageImportance.INFORMATION,
            is_draft=True,
            sent_at=None,
            users=[
                MockMessageUserModel(
                    id="mu1",
                    message_id="draft_message",
                    user_id="user1",
                    is_sender=True,
                    is_addressee=False,
                    is_read=False
                )
            ],
            meta_records=[]
        )
        
        # Set the mock to return these models
        session.set_query_results([draft_message_model])
        
        # Get draft messages for user
        drafts = await repository.get_draft_messages_for_user("user1")
        
        # Verify the messages
        assert len(drafts) == 1
        assert drafts[0].id == "draft_message"
        assert drafts[0].is_draft is True
    
    @pytest.mark.asyncio
    async def test_get_sent_messages_for_user(self, repository, session):
        # Create mock message models
        sent_message_model = MockMessageModel(
            id="sent_message",
            subject="Sent Subject",
            body="Sent Body",
            flag=MessageImportance.INFORMATION,
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC),
            users=[
                MockMessageUserModel(
                    id="mu1",
                    message_id="sent_message",
                    user_id="user1",
                    is_sender=True,
                    is_addressee=False,
                    is_read=True
                )
            ],
            meta_records=[]
        )
        
        # Set the mock to return these models
        session.set_query_results([sent_message_model])
        
        # Get sent messages for user
        sent = await repository.get_sent_messages_for_user("user1")
        
        # Verify the messages
        assert len(sent) == 1
        assert sent[0].id == "sent_message"
        assert sent[0].is_draft is False
        assert sent[0].sent_at == datetime(2023, 1, 1, tzinfo=UTC)
    
    def test_model_to_entity_conversion(self, repository):
        # Create a mock message model
        message_model = MockMessageModel(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body",
            flag=MessageImportance.HIGH,
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC),
            parent_id="parent_id",
            group_id="group_id",
            users=[
                MockMessageUserModel(
                    id="mu1",
                    message_id="test_message_id",
                    user_id="user1",
                    is_sender=True,
                    is_addressee=False,
                    is_copied_on=False,
                    is_blind_copied_on=False,
                    is_read=True,
                    read_at=datetime(2023, 1, 2, tzinfo=UTC)
                ),
                MockMessageUserModel(
                    id="mu2",
                    message_id="test_message_id",
                    user_id="user2",
                    is_sender=False,
                    is_addressee=True,
                    is_copied_on=False,
                    is_blind_copied_on=False,
                    is_read=False,
                    read_at=None
                )
            ],
            meta_records=[
                MockModel(id="meta1"),
                MockModel(id="meta2")
            ]
        )
        
        # Convert the model to an entity
        entity = repository._model_to_entity(message_model)
        
        # Verify the entity
        assert entity.id == "test_message_id"
        assert entity.subject == "Test Subject"
        assert entity.body == "Test Body"
        assert entity.flag == MessageImportance.HIGH
        assert entity.is_draft is False
        assert entity.sent_at == datetime(2023, 1, 1, tzinfo=UTC)
        assert entity.parent_id == "parent_id"
        assert entity.group_id == "group_id"
        
        # Verify users
        assert len(entity.users) == 2
        
        sender = next((u for u in entity.users if u.is_sender), None)
        assert sender is not None
        assert sender.user_id == "user1"
        assert sender.is_read is True
        assert sender.read_at == datetime(2023, 1, 2, tzinfo=UTC)
        
        recipient = next((u for u in entity.users if u.is_addressee), None)
        assert recipient is not None
        assert recipient.user_id == "user2"
        assert recipient.is_read is False
        assert recipient.read_at is None
        
        # Verify meta records
        assert len(entity.meta_record_ids) == 2
        assert "meta1" in entity.meta_record_ids
        assert "meta2" in entity.meta_record_ids