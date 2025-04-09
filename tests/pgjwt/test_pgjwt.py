# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import datetime
import pytest  # type: ignore
import jwt

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import ProgrammingError

# from uno.auth.tables import User
from uno.settings import uno_settings

# from tests.conftest import mock_rls_vars


# Not marked as a fixture as need to call it with different parameters for testing
def encode_test_token(
    email: str = uno_settings.SUPERUSER_EMAIL,  # Email for sub
    has_sub: bool = True,  # Has subject
    has_exp: bool = True,  # Has expiration
    is_expired: bool = False,  # Expired token
    invalid_secret: bool = False,  # Invalid secret
) -> str:
    """Returns a JWT token for use in tests."""
    token_payload: dict[str, Any] = {}
    if has_exp and not is_expired:
        token_payload["exp"] = datetime.datetime.now(
            datetime.timezone.utc
        ) + datetime.timedelta(minutes=uno_settings.TOKEN_EXPIRE_MINUTES)
    elif has_exp and is_expired:
        token_payload["exp"] = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(minutes=uno_settings.TOKEN_EXPIRE_MINUTES)

    if has_sub:
        token_payload["sub"] = email

    if invalid_secret:
        return jwt.encode(token_payload, "FAKE SECRET", uno_settings.TOKEN_ALGORITHM)
    return jwt.encode(
        token_payload, uno_settings.TOKEN_SECRET, uno_settings.TOKEN_ALGORITHM
    )


'''
class TestJWT:
    def test_valid_jwt(self, session, create_test_functions):
        """Tests that a valid JWT token can be verified and the session variables set."""
        token = encode_test_token()
        with session.begin():
            result = session.execute(func.uno.authorize_user(token))
            assert result.scalars().first() is True

            result = session.execute(func.uno.testlist_rls_vars())
            session_variables = result.scalars().first()
            assert session_variables.get("email") == uno_settings.SUPERUSER_EMAIL
            assert session_variables.get("id") != ""
            assert session_variables.get("is_superuser") == "true"
            assert session_variables.get("is_tenant_admin") == "false"
            assert session_variables.get("tenant_id") == ""

    def test_expired_jwt(self, session):
        """Tests that an expired JWT token cannot be authorized."""
        token = encode_test_token(is_expired=True)
        with session.begin():
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(func.uno.authorize_user(token))
            assert "invalid token" in str(excinfo.value)

    def test_invalid_secret_jwt(self, session):
        """Tests that a JWT token with an invalid secret cannot be authorized."""
        token = encode_test_token(invalid_secret=True)
        with session.begin():
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(func.uno.authorize_user(token))
            assert "invalid token" in str(excinfo.value)

    def test_invalid_sub_jwt(self, session):
        """Tests that a JWT token with an invalid sub cannot be authorized."""
        token = encode_test_token(email="anonymous@nowheres.none")
        with session.begin():
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(func.uno.authorize_user(token))
            assert "user not found" in str(excinfo.value)

    def test_no_sub_jwt(self, session):
        """Tests that a JWT token without a sub cannot be authorized."""
        token = encode_test_token(has_sub=False)
        with session.begin():
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(func.uno.authorize_user(token))
            assert "no sub in token" in str(excinfo.value)

    def test_no_exp_jwt(self, session):
        """Tests that a JWT token without an expiration cannot be authorized."""
        token = encode_test_token(has_exp=False)
        with session.begin():
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(func.uno.authorize_user(token))
            assert "no exp in token" in str(excinfo.value)

    def test_inactive_user_jwt(self, session, superuser_id, user_dict):
        """Tests that an inactive user cannot be authorized."""
        token = encode_test_token(email="user1@acme.com")
        with session.begin():
            session.execute(func.uno.mock_authorize_user(*mock_rls_vars(superuser_id)))
            session.execute(func.uno.mock_role("writer"))
            user = session.scalar(select(User).where(User.email == "user1@acme.com"))
            user.is_active = False
            session.commit()
        with session.begin():
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(func.uno.authorize_user(token))
            assert "user is not active" in str(excinfo.value)

    def test_deleted_user_jwt(self, session, superuser_id, user_dict):
        """Tests that a deleted user cannot be authorized."""
        token = encode_test_token(email="user2@acme.com")
        with session.begin():
            session.execute(func.uno.mock_authorize_user(*mock_rls_vars(superuser_id)))
            session.execute(func.uno.mock_role("writer"))
            user = session.scalar(select(User).where(User.email == "user2@acme.com"))
            user.is_deleted = True
            session.commit()
        with session.begin():
            with pytest.raises(ProgrammingError) as excinfo:
                session.execute(func.uno.authorize_user(token))
            assert "user was deleted" in str(excinfo.value)
'''
