import pytest
from datetime import datetime, UTC
from unittest import mock
import uuid

from uno.core.errors import EntityNotFoundError
from uno.messaging.entities import Message, MessageUser
from uno.messaging.domain_services import MessageDomainService
from uno.enums import MessageImportance


class MockMessageRepository:
    """Mock implementation of MessageRepositoryProtocol for testing."""
    
    def __init__(self):
        self.messages = {}
    
    async def get_by_id(self, message_id):
        return self.messages.get(message_id)
    
    async def get_messages_for_user(self, user_id, only_unread=False, page=1, page_size=20):
        messages = []
        for message in self.messages.values():
            for user in message.users:
                if user.user_id == user_id and not message.is_draft:
                    if only_unread and user.is_read:
                        continue
                    messages.append(message)
                    break
        
        # Sort by sent_at desc
        messages.sort(key=lambda m: m.sent_at if m.sent_at else datetime.min.replace(tzinfo=UTC), reverse=True)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        return messages[start:end]
    
    async def get_message_thread(self, parent_message_id, page=1, page_size=20):
        parent_message = self.messages.get(parent_message_id)
        if not parent_message:
            raise EntityNotFoundError(f"Message with ID {parent_message_id} not found")
        
        thread_messages = [parent_message]
        
        # Find all child messages
        for message in self.messages.values():
            if message.parent_id == parent_message_id:
                thread_messages.append(message)
        
        # Sort by sent_at asc
        thread_messages.sort(key=lambda m: m.sent_at if m.sent_at else datetime.min.replace(tzinfo=UTC))
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        return thread_messages[start:end]
    
    async def create(self, message):
        self.messages[message.id] = message
        return message
    
    async def update(self, message):
        if message.id not in self.messages:
            raise EntityNotFoundError(f"Message with ID {message.id} not found")
        
        self.messages[message.id] = message
        return message
    
    async def delete(self, message_id):
        if message_id not in self.messages:
            raise EntityNotFoundError(f"Message with ID {message_id} not found")
        
        del self.messages[message_id]
    
    async def get_draft_messages_for_user(self, user_id, page=1, page_size=20):
        messages = []
        for message in self.messages.values():
            for user in message.users:
                if user.user_id == user_id and user.is_sender and message.is_draft:
                    messages.append(message)
                    break
        
        # Sort by sent_at desc
        messages.sort(key=lambda m: m.sent_at if m.sent_at else datetime.min.replace(tzinfo=UTC), reverse=True)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        return messages[start:end]
    
    async def get_sent_messages_for_user(self, user_id, page=1, page_size=20):
        messages = []
        for message in self.messages.values():
            for user in message.users:
                if user.user_id == user_id and user.is_sender and not message.is_draft:
                    messages.append(message)
                    break
        
        # Sort by sent_at desc
        messages.sort(key=lambda m: m.sent_at if m.sent_at else datetime.min.replace(tzinfo=UTC), reverse=True)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        return messages[start:end]


class TestMessageDomainService:
    
    @pytest.fixture
    def message_repository(self):
        return MockMessageRepository()
    
    @pytest.fixture
    def message_service(self, message_repository):
        return MessageDomainService(message_repository)
    
    @pytest.mark.asyncio
    async def test_get_message(self, message_service, message_repository):
        # Create a test message
        test_message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        message_repository.messages["test_message_id"] = test_message
        
        # Get the message
        message = await message_service.get_message("test_message_id")
        
        assert message is test_message
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_message(self, message_service):
        # Try to get a message that doesn't exist
        with pytest.raises(EntityNotFoundError) as exc:
            await message_service.get_message("nonexistent_id")
        
        assert "Message with ID nonexistent_id not found" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_get_messages_for_user(self, message_service, message_repository):
        # Create test messages
        message1 = Message(
            id="message1",
            subject="Subject 1",
            body="Body 1",
            is_draft=False,
            sent_at=datetime(2023, 1, 3, tzinfo=UTC)
        )
        message1.add_user(user_id="user1", is_addressee=True)
        
        message2 = Message(
            id="message2",
            subject="Subject 2",
            body="Body 2",
            is_draft=False,
            sent_at=datetime(2023, 1, 2, tzinfo=UTC)
        )
        message2.add_user(user_id="user1", is_addressee=True)
        message2.mark_as_read_by_user("user1")
        
        message3 = Message(
            id="message3",
            subject="Subject 3",
            body="Body 3",
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC)
        )
        message3.add_user(user_id="user2", is_addressee=True)
        
        message4 = Message(
            id="message4",
            subject="Subject 4",
            body="Body 4",
            is_draft=True
        )
        message4.add_user(user_id="user1", is_sender=True)
        
        message_repository.messages["message1"] = message1
        message_repository.messages["message2"] = message2
        message_repository.messages["message3"] = message3
        message_repository.messages["message4"] = message4
        
        # Get all messages for user1
        messages = await message_service.get_messages_for_user("user1")
        
        assert len(messages) == 2
        # Messages should be ordered by sent_at desc
        assert messages[0].id == "message1"
        assert messages[1].id == "message2"
        
        # Get only unread messages for user1
        unread_messages = await message_service.get_messages_for_user("user1", only_unread=True)
        
        assert len(unread_messages) == 1
        assert unread_messages[0].id == "message1"
        
        # Get messages for user2
        user2_messages = await message_service.get_messages_for_user("user2")
        
        assert len(user2_messages) == 1
        assert user2_messages[0].id == "message3"
        
        # Get messages with pagination
        paginated_messages = await message_service.get_messages_for_user("user1", page=1, page_size=1)
        
        assert len(paginated_messages) == 1
        assert paginated_messages[0].id == "message1"
    
    @pytest.mark.asyncio
    async def test_get_draft_messages(self, message_service, message_repository):
        # Create test messages
        draft_message = Message(
            id="draft_message",
            subject="Draft Subject",
            body="Draft Body",
            is_draft=True
        )
        draft_message.add_user(user_id="user1", is_sender=True)
        
        sent_message = Message(
            id="sent_message",
            subject="Sent Subject",
            body="Sent Body",
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC)
        )
        sent_message.add_user(user_id="user1", is_sender=True)
        
        other_draft = Message(
            id="other_draft",
            subject="Other Draft",
            body="Other Body",
            is_draft=True
        )
        other_draft.add_user(user_id="user2", is_sender=True)
        
        message_repository.messages["draft_message"] = draft_message
        message_repository.messages["sent_message"] = sent_message
        message_repository.messages["other_draft"] = other_draft
        
        # Get draft messages for user1
        drafts = await message_service.get_draft_messages("user1")
        
        assert len(drafts) == 1
        assert drafts[0].id == "draft_message"
    
    @pytest.mark.asyncio
    async def test_get_sent_messages(self, message_service, message_repository):
        # Create test messages
        draft_message = Message(
            id="draft_message",
            subject="Draft Subject",
            body="Draft Body",
            is_draft=True
        )
        draft_message.add_user(user_id="user1", is_sender=True)
        
        sent_message1 = Message(
            id="sent_message1",
            subject="Sent Subject 1",
            body="Sent Body 1",
            is_draft=False,
            sent_at=datetime(2023, 1, 2, tzinfo=UTC)
        )
        sent_message1.add_user(user_id="user1", is_sender=True)
        
        sent_message2 = Message(
            id="sent_message2",
            subject="Sent Subject 2",
            body="Sent Body 2",
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC)
        )
        sent_message2.add_user(user_id="user1", is_sender=True)
        
        other_sent = Message(
            id="other_sent",
            subject="Other Sent",
            body="Other Body",
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC)
        )
        other_sent.add_user(user_id="user2", is_sender=True)
        
        message_repository.messages["draft_message"] = draft_message
        message_repository.messages["sent_message1"] = sent_message1
        message_repository.messages["sent_message2"] = sent_message2
        message_repository.messages["other_sent"] = other_sent
        
        # Get sent messages for user1
        sent = await message_service.get_sent_messages("user1")
        
        assert len(sent) == 2
        # Should be sorted by sent_at desc
        assert sent[0].id == "sent_message1"
        assert sent[1].id == "sent_message2"
    
    @pytest.mark.asyncio
    async def test_get_message_thread(self, message_service, message_repository):
        # Create a parent message
        parent_message = Message(
            id="parent_message",
            subject="Parent Subject",
            body="Parent Body",
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC)
        )
        parent_message.add_user(user_id="user1", is_sender=True)
        parent_message.add_user(user_id="user2", is_addressee=True)
        
        # Create reply messages
        reply1 = Message(
            id="reply1",
            subject="Re: Parent Subject",
            body="Reply 1",
            is_draft=False,
            sent_at=datetime(2023, 1, 2, tzinfo=UTC),
            parent_id="parent_message"
        )
        reply1.add_user(user_id="user2", is_sender=True)
        reply1.add_user(user_id="user1", is_addressee=True)
        
        reply2 = Message(
            id="reply2",
            subject="Re: Parent Subject",
            body="Reply 2",
            is_draft=False,
            sent_at=datetime(2023, 1, 3, tzinfo=UTC),
            parent_id="parent_message"
        )
        reply2.add_user(user_id="user1", is_sender=True)
        reply2.add_user(user_id="user2", is_addressee=True)
        
        message_repository.messages["parent_message"] = parent_message
        message_repository.messages["reply1"] = reply1
        message_repository.messages["reply2"] = reply2
        
        # Get message thread
        thread = await message_service.get_message_thread("parent_message")
        
        assert len(thread) == 3
        # Should be sorted by sent_at asc (parent first, then children)
        assert thread[0].id == "parent_message"
        assert thread[1].id == "reply1"
        assert thread[2].id == "reply2"
    
    @pytest.mark.asyncio
    async def test_create_message(self, message_service):
        # Mock uuid generation to get a predictable ID
        with mock.patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            # Create a message
            message = await message_service.create_message(
                subject="Test Subject",
                body="Test Body",
                sender_id="sender1",
                recipient_ids=["recipient1", "recipient2"],
                cc_ids=["cc1"],
                bcc_ids=["bcc1"],
                flag=MessageImportance.HIGH,
                is_draft=True,
                meta_record_ids=["meta1", "meta2"],
                group_id="group1"
            )
            
            # Verify the message
            assert message.id == "12345678-1234-5678-1234-567812345678"
            assert message.subject == "Test Subject"
            assert message.body == "Test Body"
            assert message.flag == MessageImportance.HIGH
            assert message.is_draft is True
            assert message.sent_at is None
            assert message.meta_record_ids == ["meta1", "meta2"]
            assert message.group_id == "group1"
            
            # Verify the users
            assert len(message.users) == 5
            
            # Check sender
            sender = next((u for u in message.users if u.is_sender), None)
            assert sender is not None
            assert sender.user_id == "sender1"
            
            # Check recipients
            recipients = [u for u in message.users if u.is_addressee]
            assert len(recipients) == 2
            assert {u.user_id for u in recipients} == {"recipient1", "recipient2"}
            
            # Check CC
            cc = [u for u in message.users if u.is_copied_on]
            assert len(cc) == 1
            assert cc[0].user_id == "cc1"
            
            # Check BCC
            bcc = [u for u in message.users if u.is_blind_copied_on]
            assert len(bcc) == 1
            assert bcc[0].user_id == "bcc1"
    
    @pytest.mark.asyncio
    async def test_create_message_minimal(self, message_service):
        # Create a message with minimal parameters
        message = await message_service.create_message(
            subject="Simple Subject",
            body="Simple Body",
            sender_id="sender1",
            recipient_ids=["recipient1"]
        )
        
        # Verify the message
        assert message.subject == "Simple Subject"
        assert message.body == "Simple Body"
        assert message.flag == MessageImportance.INFORMATION  # Default value
        assert message.is_draft is True  # Default value
        assert message.meta_record_ids == []  # Default value
        assert message.parent_id is None  # Default value
        assert message.group_id is None  # Default value
        
        # Verify the users
        assert len(message.users) == 2
        
        # Check sender
        sender = next((u for u in message.users if u.is_sender), None)
        assert sender is not None
        assert sender.user_id == "sender1"
        
        # Check recipient
        recipient = next((u for u in message.users if u.is_addressee), None)
        assert recipient is not None
        assert recipient.user_id == "recipient1"
    
    @pytest.mark.asyncio
    async def test_update_message(self, message_service, message_repository):
        # Create a test message
        draft_message = Message(
            id="draft_message",
            subject="Draft Subject",
            body="Draft Body",
            flag=MessageImportance.INFORMATION,
            is_draft=True
        )
        draft_message.add_user(user_id="sender1", is_sender=True)
        draft_message.add_user(user_id="recipient1", is_addressee=True)
        message_repository.messages["draft_message"] = draft_message
        
        # Update the message
        updated_message = await message_service.update_message(
            message_id="draft_message",
            subject="Updated Subject",
            body="Updated Body",
            recipient_ids=["recipient2"],
            cc_ids=["cc1"],
            bcc_ids=["bcc1"],
            flag=MessageImportance.HIGH,
            meta_record_ids=["meta1"]
        )
        
        # Verify the message was updated
        assert updated_message.subject == "Updated Subject"
        assert updated_message.body == "Updated Body"
        assert updated_message.flag == MessageImportance.HIGH
        assert updated_message.meta_record_ids == ["meta1"]
        
        # Verify the users
        assert len(updated_message.users) == 4
        
        # Sender should be preserved
        sender = next((u for u in updated_message.users if u.is_sender), None)
        assert sender is not None
        assert sender.user_id == "sender1"
        
        # Recipients should be updated
        recipients = [u for u in updated_message.users if u.is_addressee]
        assert len(recipients) == 1
        assert recipients[0].user_id == "recipient2"
        
        # Check CC
        cc = [u for u in updated_message.users if u.is_copied_on]
        assert len(cc) == 1
        assert cc[0].user_id == "cc1"
        
        # Check BCC
        bcc = [u for u in updated_message.users if u.is_blind_copied_on]
        assert len(bcc) == 1
        assert bcc[0].user_id == "bcc1"
    
    @pytest.mark.asyncio
    async def test_update_message_partial(self, message_service, message_repository):
        # Create a test message
        draft_message = Message(
            id="draft_message",
            subject="Draft Subject",
            body="Draft Body",
            flag=MessageImportance.INFORMATION,
            is_draft=True
        )
        draft_message.add_user(user_id="sender1", is_sender=True)
        draft_message.add_user(user_id="recipient1", is_addressee=True)
        message_repository.messages["draft_message"] = draft_message
        
        # Update only some fields
        updated_message = await message_service.update_message(
            message_id="draft_message",
            subject="Updated Subject"
        )
        
        # Verify that only the subject was updated
        assert updated_message.subject == "Updated Subject"
        assert updated_message.body == "Draft Body"  # Unchanged
        assert updated_message.flag == MessageImportance.INFORMATION  # Unchanged
        
        # Verify users were not changed
        assert len(updated_message.users) == 2
        assert any(u.user_id == "recipient1" and u.is_addressee for u in updated_message.users)
    
    @pytest.mark.asyncio
    async def test_update_non_draft_message(self, message_service, message_repository):
        # Create a test message that has already been sent
        sent_message = Message(
            id="sent_message",
            subject="Sent Subject",
            body="Sent Body",
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC)
        )
        sent_message.add_user(user_id="sender1", is_sender=True)
        message_repository.messages["sent_message"] = sent_message
        
        # Try to update a message that's already been sent
        with pytest.raises(ValueError) as exc:
            await message_service.update_message(
                message_id="sent_message",
                subject="Updated Subject"
            )
        
        assert "Cannot update a message that has already been sent" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_send_message(self, message_service, message_repository):
        # Create a draft message
        draft_message = Message(
            id="draft_message",
            subject="Draft Subject",
            body="Draft Body",
            is_draft=True
        )
        draft_message.add_user(user_id="sender1", is_sender=True)
        draft_message.add_user(user_id="recipient1", is_addressee=True)
        message_repository.messages["draft_message"] = draft_message
        
        # Mock datetime.now to return a fixed time
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            # Send the message
            sent_message = await message_service.send_message("draft_message")
            
            # Verify the message was sent
            assert sent_message.is_draft is False
            assert sent_message.sent_at == fixed_time
    
    @pytest.mark.asyncio
    async def test_send_already_sent_message(self, message_service, message_repository):
        # Create a message that has already been sent
        sent_message = Message(
            id="sent_message",
            subject="Sent Subject",
            body="Sent Body",
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC)
        )
        sent_message.add_user(user_id="sender1", is_sender=True)
        sent_message.add_user(user_id="recipient1", is_addressee=True)
        message_repository.messages["sent_message"] = sent_message
        
        # Try to send an already sent message
        with pytest.raises(ValueError) as exc:
            await message_service.send_message("sent_message")
        
        assert "Message is already sent" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_send_message_without_recipients(self, message_service, message_repository):
        # Create a draft message without recipients
        draft_message = Message(
            id="draft_message",
            subject="Draft Subject",
            body="Draft Body",
            is_draft=True
        )
        draft_message.add_user(user_id="sender1", is_sender=True)
        message_repository.messages["draft_message"] = draft_message
        
        # Try to send a message without recipients
        with pytest.raises(ValueError) as exc:
            await message_service.send_message("draft_message")
        
        assert "Cannot send a message without recipients" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_delete_message(self, message_service, message_repository):
        # Create a test message
        message = Message(
            id="test_message",
            subject="Test Subject",
            body="Test Body"
        )
        message_repository.messages["test_message"] = message
        
        # Delete the message
        await message_service.delete_message("test_message")
        
        # Verify the message was deleted
        assert "test_message" not in message_repository.messages
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_message(self, message_service):
        # Try to delete a message that doesn't exist
        with pytest.raises(EntityNotFoundError) as exc:
            await message_service.delete_message("nonexistent_id")
        
        assert "Message with ID nonexistent_id not found" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_mark_as_read(self, message_service, message_repository):
        # Create a test message
        message = Message(
            id="test_message",
            subject="Test Subject",
            body="Test Body",
            is_draft=False,
            sent_at=datetime(2023, 1, 1, tzinfo=UTC)
        )
        message.add_user(user_id="sender1", is_sender=True)
        message.add_user(user_id="recipient1", is_addressee=True)
        message_repository.messages["test_message"] = message
        
        # Mark as read
        updated_message = await message_service.mark_as_read("test_message", "recipient1")
        
        # Verify the message was marked as read
        recipient = next((u for u in updated_message.users if u.user_id == "recipient1"), None)
        assert recipient is not None
        assert recipient.is_read is True
        assert recipient.read_at is not None
        
        # Verify other users are not affected
        sender = next((u for u in updated_message.users if u.user_id == "sender1"), None)
        assert sender is not None
        assert sender.is_read is False
        assert sender.read_at is None
    
    @pytest.mark.asyncio
    async def test_mark_nonexistent_user_as_read(self, message_service, message_repository):
        # Create a test message
        message = Message(
            id="test_message",
            subject="Test Subject",
            body="Test Body"
        )
        message.add_user(user_id="sender1", is_sender=True)
        message_repository.messages["test_message"] = message
        
        # Try to mark as read for a user not associated with the message
        # This should be a no-op and not raise an exception
        updated_message = await message_service.mark_as_read("test_message", "nonexistent_user")
        
        # Verify the message was not changed
        assert len(updated_message.users) == 1
        assert all(not u.is_read for u in updated_message.users)