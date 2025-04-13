# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import Mock, patch, MagicMock
import datetime
import decimal

from uno.core.errors.result import Ok, Err
from uno.database.db_manager import DBManager
from uno.values.repositories import (
    BooleanValueRepository,
    TextValueRepository,
    IntegerValueRepository,
    DecimalValueRepository,
    DateValueRepository,
    DateTimeValueRepository,
    TimeValueRepository,
    AttachmentRepository,
)
from uno.values.services import ValueService, ValueServiceError
from uno.values.objs import (
    BooleanValue,
    TextValue,
    IntegerValue,
    DecimalValue,
    DateValue,
    DateTimeValue,
    TimeValue,
    Attachment,
)


class TestValueService:
    """Tests for the ValueService class."""

    @pytest.fixture
    def mock_value_repositories(self):
        """Create mock value repositories."""
        repositories = {
            "boolean": Mock(spec=BooleanValueRepository),
            "text": Mock(spec=TextValueRepository),
            "integer": Mock(spec=IntegerValueRepository),
            "decimal": Mock(spec=DecimalValueRepository),
            "date": Mock(spec=DateValueRepository),
            "datetime": Mock(spec=DateTimeValueRepository),
            "time": Mock(spec=TimeValueRepository),
            "attachment": Mock(spec=AttachmentRepository),
        }
        
        # Set up common return values
        for repo in repositories.values():
            repo.get_by_id.return_value = Ok(None)
            repo.get_by_value.return_value = Ok(None)
            repo.create.return_value = Ok(None)
        
        # Set up specific return values
        repositories["boolean"].create.return_value = Ok(BooleanValue(id="bool1", value=True, name="True"))
        repositories["text"].create.return_value = Ok(TextValue(id="text1", value="Test", name="Test"))
        repositories["integer"].create.return_value = Ok(IntegerValue(id="int1", value=42, name="42"))
        repositories["decimal"].create.return_value = Ok(DecimalValue(id="dec1", value=decimal.Decimal("3.14"), name="3.14"))
        repositories["date"].create.return_value = Ok(DateValue(id="date1", value=datetime.date.today(), name="Today"))
        repositories["datetime"].create.return_value = Ok(DateTimeValue(id="dt1", value=datetime.datetime.now(), name="Now"))
        repositories["time"].create.return_value = Ok(TimeValue(id="time1", value=datetime.time(12, 0), name="Noon"))
        repositories["attachment"].create.return_value = Ok(Attachment(id="att1", file_path="/file.txt", name="File"))
        
        return repositories

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock DB manager."""
        db_manager = Mock(spec=DBManager)
        
        # Mock session context manager
        session_context = MagicMock()
        session_context.__aenter__.return_value = MagicMock()
        session_context.__aexit__.return_value = None
        
        db_manager.get_enhanced_session.return_value = session_context
        return db_manager

    @pytest.fixture
    def service(self, mock_value_repositories, mock_db_manager):
        """Create a value service instance with mocked dependencies."""
        return ValueService(
            boolean_repository=mock_value_repositories["boolean"],
            text_repository=mock_value_repositories["text"],
            integer_repository=mock_value_repositories["integer"],
            decimal_repository=mock_value_repositories["decimal"],
            date_repository=mock_value_repositories["date"],
            datetime_repository=mock_value_repositories["datetime"],
            time_repository=mock_value_repositories["time"],
            attachment_repository=mock_value_repositories["attachment"],
            db_manager=mock_db_manager
        )

    async def test_create_boolean_value(self, service, mock_value_repositories):
        """Test creating a boolean value."""
        # Execute
        result = await service.create_value(BooleanValue, True, "True Value")
        
        # Assert
        assert result.is_ok()
        mock_value_repositories["boolean"].create.assert_called_once()
        created_value = mock_value_repositories["boolean"].create.call_args[0][0]
        assert created_value.value is True
        assert created_value.name == "True Value"

    async def test_create_text_value(self, service, mock_value_repositories):
        """Test creating a text value."""
        # Execute
        result = await service.create_value(TextValue, "Hello", "Greeting")
        
        # Assert
        assert result.is_ok()
        mock_value_repositories["text"].create.assert_called_once()
        created_value = mock_value_repositories["text"].create.call_args[0][0]
        assert created_value.value == "Hello"
        assert created_value.name == "Greeting"

    async def test_create_integer_value(self, service, mock_value_repositories):
        """Test creating an integer value."""
        # Execute
        result = await service.create_value(IntegerValue, 42, "Answer")
        
        # Assert
        assert result.is_ok()
        mock_value_repositories["integer"].create.assert_called_once()
        created_value = mock_value_repositories["integer"].create.call_args[0][0]
        assert created_value.value == 42
        assert created_value.name == "Answer"

    async def test_create_decimal_value(self, service, mock_value_repositories):
        """Test creating a decimal value."""
        # Execute
        value = decimal.Decimal("3.14159")
        result = await service.create_value(DecimalValue, value, "Pi")
        
        # Assert
        assert result.is_ok()
        mock_value_repositories["decimal"].create.assert_called_once()
        created_value = mock_value_repositories["decimal"].create.call_args[0][0]
        assert created_value.value == value
        assert created_value.name == "Pi"

    async def test_create_date_value(self, service, mock_value_repositories):
        """Test creating a date value."""
        # Execute
        value = datetime.date(2023, 1, 1)
        result = await service.create_value(DateValue, value, "New Year's Day")
        
        # Assert
        assert result.is_ok()
        mock_value_repositories["date"].create.assert_called_once()
        created_value = mock_value_repositories["date"].create.call_args[0][0]
        assert created_value.value == value
        assert created_value.name == "New Year's Day"

    async def test_create_value_invalid_type(self, service):
        """Test creating a value with an invalid type."""
        # Execute
        result = await service.create_value(BooleanValue, "not a boolean", "Invalid")
        
        # Assert
        assert result.is_err()
        assert "Invalid value type" in str(result.unwrap_err())

    async def test_get_or_create_value_existing(self, service, mock_value_repositories):
        """Test getting an existing value."""
        # Setup
        existing_value = TextValue(id="existing", value="Hello", name="Existing")
        mock_value_repositories["text"].get_by_value.return_value = Ok(existing_value)
        
        # Execute
        result = await service.get_or_create_value(TextValue, "Hello", "New Name")
        
        # Assert
        assert result.is_ok()
        assert result.unwrap() == existing_value
        mock_value_repositories["text"].create.assert_not_called()

    async def test_get_or_create_value_new(self, service, mock_value_repositories):
        """Test creating a new value when it doesn't exist."""
        # Setup
        mock_value_repositories["text"].get_by_value.return_value = Ok(None)
        
        # Execute
        result = await service.get_or_create_value(TextValue, "Hello", "Greeting")
        
        # Assert
        assert result.is_ok()
        mock_value_repositories["text"].create.assert_called_once()

    async def test_get_value_by_id(self, service, mock_value_repositories):
        """Test getting a value by ID."""
        # Setup
        value_id = "text123"
        existing_value = TextValue(id=value_id, value="Hello", name="Greeting")
        mock_value_repositories["text"].get_by_id.return_value = Ok(existing_value)
        
        # Execute
        result = await service.get_value_by_id(TextValue, value_id)
        
        # Assert
        assert result.is_ok()
        assert result.unwrap() == existing_value
        mock_value_repositories["text"].get_by_id.assert_called_once_with(value_id)

    async def test_create_attachment(self, service, mock_value_repositories):
        """Test creating an attachment."""
        # Execute
        result = await service.create_attachment("/path/to/file.pdf", "Document")
        
        # Assert
        assert result.is_ok()
        mock_value_repositories["attachment"].create.assert_called_once()
        created_attachment = mock_value_repositories["attachment"].create.call_args[0][0]
        assert created_attachment.file_path == "/path/to/file.pdf"
        assert created_attachment.name == "Document"

    async def test_validate_value_valid(self, service):
        """Test validating a valid value."""
        # Test cases for each value type
        test_cases = [
            (BooleanValue, True),
            (TextValue, "Hello"),
            (IntegerValue, 42),
            (DecimalValue, decimal.Decimal("3.14")),
            (DateValue, datetime.date.today()),
            (DateTimeValue, datetime.datetime.now()),
            (TimeValue, datetime.time(12, 0)),
        ]
        
        # Execute and assert for each test case
        for value_type, value in test_cases:
            result = await service.validate_value(value_type, value)
            assert result.is_ok(), f"Failed for {value_type.__name__}: {result.unwrap_err() if result.is_err() else ''}"
            assert result.unwrap() is True

    async def test_validate_value_invalid(self, service):
        """Test validating an invalid value."""
        # Test cases for each value type with invalid values
        test_cases = [
            (BooleanValue, "not a boolean"),
            (TextValue, 123),  # This will actually pass due to str() conversion
            (IntegerValue, "not an integer"),
            (DecimalValue, "not a decimal"),
            (DateValue, "not a date"),
            (DateTimeValue, "not a datetime"),
            (TimeValue, "not a time"),
        ]
        
        # Execute and assert for each test case
        for value_type, value in test_cases:
            if value_type == TextValue:
                # Skip TextValue since str() makes most things valid
                continue
                
            result = await service.validate_value(value_type, value)
            assert result.is_err(), f"Should have failed for {value_type.__name__} with value {value}"
            assert "Invalid value type" in str(result.unwrap_err())

    async def test_convert_value(self, service):
        """Test converting values between types."""
        # Test cases for conversion
        test_cases = [
            # (source_value, target_type, expected_success, expected_value)
            ("42", IntegerValue, True, 42),
            (42, TextValue, True, "42"),
            ("3.14", DecimalValue, True, decimal.Decimal("3.14")),
            ("true", BooleanValue, True, True),
            ("false", BooleanValue, True, False),
            (1, BooleanValue, True, True),
            (0, BooleanValue, True, False),
            ("2023-01-01", DateValue, True, datetime.date(2023, 1, 1)),
            (datetime.datetime(2023, 1, 1, 12, 0), DateValue, True, datetime.date(2023, 1, 1)),
            (datetime.date(2023, 1, 1), DateTimeValue, True, datetime.datetime(2023, 1, 1, 0, 0)),
            ("12:00:00", TimeValue, True, datetime.time(12, 0, 0)),
            ("not a number", IntegerValue, False, None),
        ]
        
        # Execute and assert for each test case
        for source_value, target_type, should_succeed, expected in test_cases:
            result = await service.convert_value(source_value, target_type)
            
            if should_succeed:
                assert result.is_ok(), f"Conversion failed for {source_value} to {target_type.__name__}: {result.unwrap_err() if result.is_err() else ''}"
                converted = result.unwrap()
                assert converted == expected, f"Expected {expected}, got {converted}"
            else:
                assert result.is_err(), f"Conversion should have failed for {source_value} to {target_type.__name__}"