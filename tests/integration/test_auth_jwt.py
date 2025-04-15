"""
Integration tests for JWT authentication.

This module tests JWT authentication functionality with actual token generation,
validation, refresh, and revocation against a real database.
"""

import time
import pytest
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta

import jwt
from fastapi import FastAPI, Depends, APIRouter, HTTPException
from fastapi.testclient import TestClient
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from uno.security.config import SecurityConfig, AuthenticationConfig
from uno.security.auth.jwt import (
    JWTAuth, JWTConfig, TokenType, TokenData, 
    JWTBearer, JWTAuthMiddleware
)
from uno.security.auth.token_cache import (
    TokenCache, TokenCacheConfig, 
    MemoryTokenCache, RedisTokenCache
)
from uno.domain.rbac import RbacService, User


# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration]


@pytest.fixture
def jwt_config():
    """Create a JWT configuration for testing."""
    return JWTConfig(
        secret_key="test-secret-key-for-integration-testing",
        algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
        issuer="test-issuer",
        audience="test-audience"
    )


@pytest.fixture
def token_cache_config():
    """Create a token cache configuration for testing."""
    return TokenCacheConfig(
        enabled=True,
        cache_type="memory",
        ttl=300,  # 5 minutes
        max_size=1000,
        blacklist_enabled=True,
        blacklist_ttl=3600  # 1 hour
    )


@pytest.fixture
def memory_token_cache(token_cache_config):
    """Create a memory token cache for testing."""
    return MemoryTokenCache(token_cache_config)


@pytest.fixture
def jwt_auth(jwt_config, memory_token_cache):
    """Create a JWT authentication manager for testing."""
    return JWTAuth(
        config=jwt_config,
        logger=logging.getLogger("test_jwt_auth"),
        token_cache=memory_token_cache
    )


@pytest.fixture
def test_user():
    """Create a test user for authentication tests."""
    return {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["user", "editor"],
        "tenant_id": "tenant-abc"
    }


@pytest.fixture
def test_app(jwt_auth, test_user):
    """Create a FastAPI test application with JWT authentication."""
    app = FastAPI()
    
    # Configure JWT auth with the app
    jwt_bearer = JWTBearer(jwt_auth)
    
    # Add middleware for JWT auth
    app.add_middleware(
        JWTAuthMiddleware,
        jwt_auth=jwt_auth,
        exclude_paths=["/auth/login", "/docs", "/openapi.json"]
    )
    
    # Add routes for testing
    router = APIRouter()
    
    @router.post("/auth/login")
    async def login():
        """Simple login endpoint that always returns tokens for the test user."""
        # Create tokens for the test user
        access_token = jwt_auth.create_access_token(
            subject=test_user["id"],
            additional_claims={
                "roles": test_user["roles"],
                "email": test_user["email"],
                "name": test_user["name"],
                "tenant_id": test_user["tenant_id"]
            }
        )
        
        refresh_token = jwt_auth.create_refresh_token(
            subject=test_user["id"],
            additional_claims={
                "roles": test_user["roles"],
                "email": test_user["email"],
                "name": test_user["name"],
                "tenant_id": test_user["tenant_id"]
            }
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": jwt_auth.config.access_token_expire_minutes * 60
        }
    
    @router.post("/auth/refresh")
    async def refresh(refresh_token: str):
        """Refresh an access token using a refresh token."""
        try:
            new_access_token = jwt_auth.refresh_access_token(refresh_token)
            return {
                "access_token": new_access_token,
                "expires_in": jwt_auth.config.access_token_expire_minutes * 60
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")
    
    @router.post("/auth/revoke")
    async def revoke(token: str):
        """Revoke a token."""
        success = jwt_auth.revoke_token(token)
        return {"success": success}
    
    @router.get("/protected")
    async def protected_route(token_data: TokenData = Depends(jwt_bearer)):
        """A protected route that requires authentication."""
        return {
            "message": "You have access to the protected resource",
            "user_id": token_data.sub,
            "roles": token_data.roles,
            "tenant_id": token_data.tenant_id
        }
    
    @router.get("/admin")
    async def admin_route(token_data: TokenData = Depends(jwt_bearer)):
        """A protected route that requires the admin role."""
        if "admin" not in token_data.roles:
            raise HTTPException(status_code=403, detail="Admin role required")
        return {"message": "You have access to the admin resource"}
    
    app.include_router(router)
    
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI application."""
    return TestClient(test_app)


class TestJWTAuthentication:
    """Tests for JWT authentication functionality."""
    
    def test_token_generation(self, jwt_auth, test_user):
        """Test token generation with claims."""
        # Create access token
        access_token = jwt_auth.create_access_token(
            subject=test_user["id"],
            additional_claims={
                "roles": test_user["roles"],
                "email": test_user["email"],
                "tenant_id": test_user["tenant_id"]
            }
        )
        
        # Validate token format
        assert isinstance(access_token, str)
        assert len(access_token.split(".")) == 3  # Header, payload, signature
        
        # Decode token
        token_data = jwt_auth.decode_token(access_token)
        
        # Validate token data
        assert token_data.sub == test_user["id"]
        assert token_data.token_type == TokenType.ACCESS
        assert token_data.roles == test_user["roles"]
        assert token_data.email == test_user["email"]
        assert token_data.tenant_id == test_user["tenant_id"]
        assert token_data.exp > int(time.time())
        assert "jti" in token_data.dict()
        
        # Create refresh token
        refresh_token = jwt_auth.create_refresh_token(
            subject=test_user["id"],
            additional_claims={
                "roles": test_user["roles"],
                "email": test_user["email"],
                "tenant_id": test_user["tenant_id"]
            }
        )
        
        # Decode refresh token
        refresh_token_data = jwt_auth.decode_token(refresh_token)
        
        # Validate refresh token data
        assert refresh_token_data.sub == test_user["id"]
        assert refresh_token_data.token_type == TokenType.REFRESH
        assert refresh_token_data.roles == test_user["roles"]
        
        # Refresh token should expire later than access token
        assert refresh_token_data.exp > token_data.exp
    
    def test_token_validation(self, jwt_auth, test_user):
        """Test token validation."""
        # Create access token
        access_token = jwt_auth.create_access_token(
            subject=test_user["id"],
            additional_claims={"name": test_user["name"]}
        )
        
        # Validate token
        token_data = jwt_auth.decode_token(access_token)
        assert token_data.sub == test_user["id"]
        assert token_data.name == test_user["name"]
        
        # Test with invalid token
        with pytest.raises(jwt.InvalidTokenError):
            jwt_auth.decode_token("invalid.token.string")
        
        # Test with manipulated token
        parts = access_token.split(".")
        manipulated_token = f"{parts[0]}.{parts[1]}altered.{parts[2]}"
        with pytest.raises(jwt.InvalidTokenError):
            jwt_auth.decode_token(manipulated_token)
    
    def test_token_expiration(self, jwt_config, test_user):
        """Test token expiration validation."""
        # Create a config with very short expiration
        config = JWTConfig(
            secret_key=jwt_config.secret_key,
            algorithm=jwt_config.algorithm,
            access_token_expire_minutes=0,  # Expire immediately
            refresh_token_expire_days=0     # Expire immediately
        )
        
        # Create JWT auth with this config
        jwt_auth = JWTAuth(config)
        
        # Create access token that expires immediately
        access_token = jwt_auth.create_access_token(
            subject=test_user["id"],
            expires_delta=timedelta(seconds=1)  # Expire in 1 second
        )
        
        # Wait for token to expire
        time.sleep(2)
        
        # Validate token should fail
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt_auth.decode_token(access_token)
    
    def test_refresh_token(self, jwt_auth, test_user):
        """Test refreshing an access token."""
        # Create refresh token
        refresh_token = jwt_auth.create_refresh_token(
            subject=test_user["id"],
            additional_claims={
                "roles": test_user["roles"],
                "email": test_user["email"],
                "tenant_id": test_user["tenant_id"]
            }
        )
        
        # Refresh token to get new access token
        access_token = jwt_auth.refresh_access_token(refresh_token)
        
        # Validate the new access token
        token_data = jwt_auth.decode_token(access_token)
        assert token_data.sub == test_user["id"]
        assert token_data.token_type == TokenType.ACCESS
        assert token_data.roles == test_user["roles"]
        assert token_data.email == test_user["email"]
        assert token_data.tenant_id == test_user["tenant_id"]
        
        # Try to refresh with an access token (should fail)
        with pytest.raises(ValueError, match="Not a refresh token"):
            jwt_auth.refresh_access_token(access_token)
    
    def test_token_revocation(self, jwt_auth, test_user):
        """Test token revocation."""
        # Create tokens
        access_token = jwt_auth.create_access_token(subject=test_user["id"])
        refresh_token = jwt_auth.create_refresh_token(subject=test_user["id"])
        
        # Validate tokens before revocation
        access_data = jwt_auth.decode_token(access_token)
        refresh_data = jwt_auth.decode_token(refresh_token)
        assert access_data.sub == test_user["id"]
        assert refresh_data.sub == test_user["id"]
        
        # Revoke access token
        revoked = jwt_auth.revoke_token(access_token)
        assert revoked is True
        
        # Validate revoked token should fail
        with pytest.raises(jwt.InvalidTokenError, match="Token has been revoked"):
            jwt_auth.decode_token(access_token)
        
        # Refresh token should still be valid
        refresh_data = jwt_auth.decode_token(refresh_token)
        assert refresh_data.sub == test_user["id"]
        
        # Revoke refresh token
        revoked = jwt_auth.revoke_token(refresh_token)
        assert revoked is True
        
        # Validate revoked refresh token should fail
        with pytest.raises(jwt.InvalidTokenError, match="Token has been revoked"):
            jwt_auth.decode_token(refresh_token)
    
    def test_token_caching(self, jwt_auth, test_user):
        """Test token caching for improved performance."""
        # Create token
        access_token = jwt_auth.create_access_token(subject=test_user["id"])
        
        # First validation should cache the token
        token_data = jwt_auth.decode_token(access_token)
        assert token_data.sub == test_user["id"]
        
        # Check that the token is cached
        assert jwt_auth.token_cache.get(access_token) is not None
        
        # Invalidate token in cache
        jwt_auth.token_cache.invalidate(access_token)
        
        # Token should no longer be in cache
        assert jwt_auth.token_cache.get(access_token) is None
        
        # But should still be valid when decoded
        token_data = jwt_auth.decode_token(access_token)
        assert token_data.sub == test_user["id"]
        
        # And should be back in cache
        assert jwt_auth.token_cache.get(access_token) is not None


class TestJWTFastAPIIntegration:
    """Tests for JWT authentication integration with FastAPI."""
    
    def test_protected_route_access(self, test_client):
        """Test access to a protected route with valid token."""
        # Login to get tokens
        login_response = test_client.post("/auth/login")
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # Access protected route with token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = test_client.get("/protected", headers=headers)
        
        # Verify successful access
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "You have access to the protected resource"
        assert "user_id" in data
        assert "roles" in data
        assert "tenant_id" in data
    
    def test_protected_route_without_token(self, test_client):
        """Test access to a protected route without a token."""
        # Try to access protected route without token
        response = test_client.get("/protected")
        
        # Verify authentication failure
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    
    def test_protected_route_with_invalid_token(self, test_client):
        """Test access to a protected route with an invalid token."""
        # Try to access protected route with invalid token
        headers = {"Authorization": "Bearer invalid.token.string"}
        response = test_client.get("/protected", headers=headers)
        
        # Verify authentication failure
        assert response.status_code == 401
        assert "Invalid authentication token" in response.json()["detail"]
    
    def test_admin_route_without_role(self, test_client):
        """Test access to an admin route without the required role."""
        # Login to get tokens
        login_response = test_client.post("/auth/login")
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # Try to access admin route (user doesn't have admin role)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = test_client.get("/admin", headers=headers)
        
        # Verify authorization failure
        assert response.status_code == 403
        assert response.json()["detail"] == "Admin role required"
    
    def test_token_refresh_endpoint(self, test_client):
        """Test the token refresh endpoint."""
        # Login to get tokens
        login_response = test_client.post("/auth/login")
        assert login_response.status_code == 200
        token_data = login_response.json()
        refresh_token = token_data["refresh_token"]
        
        # Use refresh token to get a new access token
        refresh_response = test_client.post("/auth/refresh", json={"refresh_token": refresh_token})
        
        # Verify successful refresh
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert "expires_in" in refresh_data
        
        # Use the new access token to access a protected route
        headers = {"Authorization": f"Bearer {refresh_data['access_token']}"}
        response = test_client.get("/protected", headers=headers)
        
        # Verify successful access with the refreshed token
        assert response.status_code == 200
    
    def test_token_revocation_endpoint(self, test_client):
        """Test the token revocation endpoint."""
        # Login to get tokens
        login_response = test_client.post("/auth/login")
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # Verify access before revocation
        headers = {"Authorization": f"Bearer {access_token}"}
        response = test_client.get("/protected", headers=headers)
        assert response.status_code == 200
        
        # Revoke the token
        revoke_response = test_client.post("/auth/revoke", json={"token": access_token})
        assert revoke_response.status_code == 200
        assert revoke_response.json()["success"] is True
        
        # Try to access protected route with revoked token
        response = test_client.get("/protected", headers=headers)
        
        # Verify authentication failure with revoked token
        assert response.status_code == 401
        assert "Invalid authentication token" in response.json()["detail"]


class TestJWTWithRBAC:
    """Tests for JWT authentication integration with RBAC."""
    
    @pytest.fixture
    def rbac_service(self):
        """Create an RBAC service for testing."""
        rbac = RbacService()
        
        # Create roles
        rbac.create_role("user", ["resource:read"])
        rbac.create_role("editor", ["resource:read", "resource:write"])
        rbac.create_role("admin", ["resource:read", "resource:write", "resource:delete", "user:manage"])
        
        # Create users
        rbac.create_user("user-123", ["user", "editor"])
        rbac.create_user("admin-456", ["admin"])
        
        return rbac
    
    @pytest.fixture
    def jwt_app_with_rbac(self, jwt_auth, rbac_service):
        """Create a FastAPI test application with JWT and RBAC integration."""
        app = FastAPI()
        
        # Configure JWT auth with the app
        jwt_bearer = JWTBearer(jwt_auth)
        
        # Add middleware for JWT auth
        app.add_middleware(
            JWTAuthMiddleware,
            jwt_auth=jwt_auth,
            exclude_paths=["/auth/login"]
        )
        
        # Add routes for testing
        router = APIRouter()
        
        @router.post("/auth/login")
        async def login(user_id: str):
            """Login endpoint that returns tokens with roles from RBAC."""
            # Get user from RBAC service
            user = rbac_service.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Create tokens with roles
            access_token = jwt_auth.create_access_token(
                subject=user.id,
                additional_claims={
                    "roles": list(user.roles)
                }
            )
            
            refresh_token = jwt_auth.create_refresh_token(
                subject=user.id,
                additional_claims={
                    "roles": list(user.roles)
                }
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": jwt_auth.config.access_token_expire_minutes * 60
            }
        
        @router.get("/resources")
        async def get_resources(token_data: TokenData = Depends(jwt_bearer)):
            """A route that requires resource:read permission."""
            # Check permission through RBAC
            has_permission = any(
                rbac_service.has_permission(token_data.sub, "resource:read")
                for role in token_data.roles
            )
            
            if not has_permission:
                raise HTTPException(status_code=403, detail="Permission denied")
            
            return {"resources": ["resource1", "resource2"]}
        
        @router.post("/resources")
        async def create_resource(token_data: TokenData = Depends(jwt_bearer)):
            """A route that requires resource:write permission."""
            # Check permission through RBAC
            has_permission = False
            for role in token_data.roles:
                if rbac_service.get_role(role) and rbac_service.get_role(role).has_permission("resource:write"):
                    has_permission = True
                    break
            
            if not has_permission:
                raise HTTPException(status_code=403, detail="Permission denied")
            
            return {"message": "Resource created"}
        
        @router.delete("/resources/{resource_id}")
        async def delete_resource(resource_id: str, token_data: TokenData = Depends(jwt_bearer)):
            """A route that requires resource:delete permission."""
            if not any(role == "admin" for role in token_data.roles):
                raise HTTPException(status_code=403, detail="Admin role required")
            
            return {"message": f"Resource {resource_id} deleted"}
        
        app.include_router(router)
        
        return app
    
    @pytest.fixture
    def rbac_test_client(self, jwt_app_with_rbac):
        """Create a test client for the RBAC-enabled application."""
        return TestClient(jwt_app_with_rbac)
    
    def test_rbac_login_with_roles(self, rbac_test_client):
        """Test login that returns tokens with proper roles."""
        # Login as regular user
        login_response = rbac_test_client.post("/auth/login?user_id=user-123")
        assert login_response.status_code == 200
        token_data = login_response.json()
        
        # Decode token to verify roles
        access_token_parts = token_data["access_token"].split(".")
        import base64
        import json
        payload = json.loads(base64.b64decode(
            # Add padding if needed
            access_token_parts[1] + "=" * (4 - len(access_token_parts[1]) % 4)
        ).decode("utf-8"))
        
        # Verify user roles
        assert "roles" in payload
        assert set(payload["roles"]) == {"user", "editor"}
    
    def test_rbac_resource_access(self, rbac_test_client):
        """Test access to resources with different roles."""
        # Login as regular user
        login_response = rbac_test_client.post("/auth/login?user_id=user-123")
        assert login_response.status_code == 200
        user_token = login_response.json()["access_token"]
        
        # Login as admin
        login_response = rbac_test_client.post("/auth/login?user_id=admin-456")
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]
        
        # Test resource read (both user and admin should have access)
        headers_user = {"Authorization": f"Bearer {user_token}"}
        response = rbac_test_client.get("/resources", headers=headers_user)
        assert response.status_code == 200
        
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        response = rbac_test_client.get("/resources", headers=headers_admin)
        assert response.status_code == 200
        
        # Test resource create (both user and admin should have access)
        response = rbac_test_client.post("/resources", headers=headers_user)
        assert response.status_code == 200
        
        response = rbac_test_client.post("/resources", headers=headers_admin)
        assert response.status_code == 200
        
        # Test resource delete (only admin should have access)
        response = rbac_test_client.delete("/resources/123", headers=headers_user)
        assert response.status_code == 403
        
        response = rbac_test_client.delete("/resources/123", headers=headers_admin)
        assert response.status_code == 200
        assert response.json()["message"] == "Resource 123 deleted"