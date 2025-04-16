import pytest
from datetime import datetime, UTC
from unittest import mock

from uno.messaging.entities import Message, MessageUser
from uno.enums import MessageImportance


class TestMessageUser:
    
    def test_create_message_user(self):
        message_user = MessageUser(
            id="test_message_user_id",
            message_id="test_message_id",
            user_id="test_user_id",
            is_sender=True,
            is_addressee=False,
            is_copied_on=False,
            is_blind_copied_on=False
        )
        
        assert message_user.id == "test_message_user_id"
        assert message_user.message_id == "test_message_id"
        assert message_user.user_id == "test_user_id"
        assert message_user.is_sender is True
        assert message_user.is_addressee is False
        assert message_user.is_copied_on is False
        assert message_user.is_blind_copied_on is False
        assert message_user.is_read is False
        assert message_user.read_at is None
    
    def test_mark_as_read(self):
        message_user = MessageUser(
            id="test_message_user_id",
            message_id="test_message_id",
            user_id="test_user_id"
        )
        
        assert message_user.is_read is False
        assert message_user.read_at is None
        
        # Mock datetime.now to return a fixed time
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            message_user.mark_as_read()
            
            assert message_user.is_read is True
            assert message_user.read_at == fixed_time
    
    def test_mark_as_read_idempotent(self):
        message_user = MessageUser(
            id="test_message_user_id",
            message_id="test_message_id",
            user_id="test_user_id"
        )
        
        # First mark as read
        message_user.mark_as_read()
        first_read_at = message_user.read_at
        
        # Wait a moment to ensure different timestamp
        import time
        time.sleep(0.001)
        
        # Mark as read again
        message_user.mark_as_read()
        
        # Should not update read_at time
        assert message_user.read_at == first_read_at


class TestMessage:
    
    def test_create_message(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body",
            flag=MessageImportance.HIGH,
            is_draft=True,
            parent_id="parent_message_id",
            group_id="test_group_id"
        )
        
        assert message.id == "test_message_id"
        assert message.subject == "Test Subject"
        assert message.body == "Test Body"
        assert message.flag == MessageImportance.HIGH
        assert message.is_draft is True
        assert message.sent_at is None
        assert message.parent_id == "parent_message_id"
        assert message.users == []
        assert message.meta_record_ids == []
        assert message.group_id == "test_group_id"
    
    def test_send_message(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body",
            is_draft=True
        )
        
        assert message.is_draft is True
        assert message.sent_at is None
        
        # Mock datetime.now to return a fixed time
        fixed_time = datetime(2023, 1, 1, tzinfo=UTC)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.UTC = UTC
            
            message.send()
            
            assert message.is_draft is False
            assert message.sent_at == fixed_time
    
    def test_send_message_idempotent(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body",
            is_draft=True
        )
        
        # Send the message
        message.send()
        first_sent_at = message.sent_at
        
        # Wait a moment to ensure different timestamp
        import time
        time.sleep(0.001)
        
        # Try to send again (should be idempotent)
        message.send()
        
        # Should not update sent_at time
        assert message.sent_at == first_sent_at
    
    def test_add_user(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Add a sender
        sender = message.add_user(
            user_id="sender_id",
            is_sender=True
        )
        
        assert isinstance(sender, MessageUser)
        assert sender.user_id == "sender_id"
        assert sender.is_sender is True
        assert sender.message_id == message.id
        assert len(message.users) == 1
        
        # Add a recipient
        recipient = message.add_user(
            user_id="recipient_id",
            is_addressee=True
        )
        
        assert isinstance(recipient, MessageUser)
        assert recipient.user_id == "recipient_id"
        assert recipient.is_addressee is True
        assert len(message.users) == 2
        
        # Add cc recipient
        cc = message.add_user(
            user_id="cc_id",
            is_copied_on=True
        )
        
        assert isinstance(cc, MessageUser)
        assert cc.user_id == "cc_id"
        assert cc.is_copied_on is True
        assert len(message.users) == 3
        
        # Add bcc recipient
        bcc = message.add_user(
            user_id="bcc_id",
            is_blind_copied_on=True
        )
        
        assert isinstance(bcc, MessageUser)
        assert bcc.user_id == "bcc_id"
        assert bcc.is_blind_copied_on is True
        assert len(message.users) == 4
    
    def test_add_duplicate_user(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Add a user
        message.add_user(user_id="user_id")
        
        # Try to add the same user again
        with pytest.raises(ValueError) as exc:
            message.add_user(user_id="user_id")
        
        assert "User user_id is already associated with this message" in str(exc.value)
    
    def test_meta_record_management(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert message.meta_record_ids == []
        
        # Add a meta record
        message.add_meta_record("meta_record_1")
        assert message.meta_record_ids == ["meta_record_1"]
        
        # Add another meta record
        message.add_meta_record("meta_record_2")
        assert message.meta_record_ids == ["meta_record_1", "meta_record_2"]
        
        # Try to add a duplicate meta record (should be idempotent)
        message.add_meta_record("meta_record_1")
        assert message.meta_record_ids == ["meta_record_1", "meta_record_2"]
        
        # Remove a meta record
        message.remove_meta_record("meta_record_1")
        assert message.meta_record_ids == ["meta_record_2"]
        
        # Try to remove a non-existent meta record (should be idempotent)
        message.remove_meta_record("non_existent")
        assert message.meta_record_ids == ["meta_record_2"]
    
    def test_mark_as_read_by_user(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Add users
        sender = message.add_user(user_id="sender_id", is_sender=True)
        recipient = message.add_user(user_id="recipient_id", is_addressee=True)
        
        # Mark as read by recipient
        message.mark_as_read_by_user("recipient_id")
        
        # Check that only the recipient's message is marked as read
        assert recipient.is_read is True
        assert recipient.read_at is not None
        assert sender.is_read is False
        assert sender.read_at is None
    
    def test_mark_as_read_by_nonexistent_user(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Try to mark as read by a user not associated with the message
        # This should be a no-op and not raise an exception
        message.mark_as_read_by_user("nonexistent_user")
    
    def test_is_read_by_user(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Add users
        message.add_user(user_id="sender_id", is_sender=True)
        message.add_user(user_id="recipient_id", is_addressee=True)
        
        # Initially, no users have read the message
        assert message.is_read_by_user("sender_id") is False
        assert message.is_read_by_user("recipient_id") is False
        
        # Mark as read by recipient
        message.mark_as_read_by_user("recipient_id")
        
        # Now the recipient has read the message
        assert message.is_read_by_user("sender_id") is False
        assert message.is_read_by_user("recipient_id") is True
        
        # Non-existent user
        assert message.is_read_by_user("nonexistent_user") is False
    
    def test_find_user(self):
        message = Message(
            id="test_message_id",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Add users
        sender = message.add_user(user_id="sender_id", is_sender=True)
        recipient = message.add_user(user_id="recipient_id", is_addressee=True)
        
        # Find users
        found_sender = message._find_user("sender_id")
        found_recipient = message._find_user("recipient_id")
        nonexistent = message._find_user("nonexistent_user")
        
        assert found_sender is sender
        assert found_recipient is recipient
        assert nonexistent is None