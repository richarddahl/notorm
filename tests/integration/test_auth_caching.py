"""
Integration tests for JWT authentication with token caching.

This module tests the token caching functionality for JWT authentication,
ensuring that token validation is properly cached and tokens can be revoked.
"""

import time
import uuid
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os
import logging

import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from uno.security.config import SecurityConfig, AuthenticationConfig
from uno.security.auth.jwt import JWTAuth, TokenType, TokenData
from uno.security.auth.token_cache import (
    TokenCache, TokenCacheConfig, MemoryTokenCache, RedisTokenCache
)
from uno.security.auth.fastapi_integration import JWTBearer


@pytest.fixture
def security_config() -> SecurityConfig:
    """Create test security configuration."""
    auth_config = AuthenticationConfig(
        jwt_secret_key="test_secret_key_for_testing_purposes_only",
        jwt_algorithm="HS256",
        jwt_expiration_minutes=60,
        refresh_token_expiration_days=7,
        token_cache_enabled=True,
        token_cache_type="memory",
        token_cache_ttl=300,
        token_blacklist_enabled=True
    )
    
    return SecurityConfig(
        authentication=auth_config
    )


@pytest.fixture
def token_cache_config() -> TokenCacheConfig:
    """Create test token cache configuration."""
    return TokenCacheConfig(
        enabled=True,
        cache_type="memory",
        ttl=300,
        max_size=1000,
        blacklist_enabled=True,
        blacklist_ttl=86400
    )


@pytest.fixture
def token_cache(token_cache_config: TokenCacheConfig) -> TokenCache:
    """Create test token cache."""
    return MemoryTokenCache(token_cache_config)


@pytest.fixture
def jwt_auth(security_config: SecurityConfig, token_cache: TokenCache) -> JWTAuth:
    """Create test JWT authentication manager."""
    return JWTAuth(
        config=security_config,
        token_cache=token_cache
    )


@pytest.fixture
def access_token(jwt_auth: JWTAuth) -> str:
    """Create a test access token."""
    user_id = str(uuid.uuid4())
    return jwt_auth.create_access_token(
        subject=user_id,
        additional_claims={
            "roles": ["user"],
            "email": "test@example.com",
            "name": "Test User"
        }
    )


@pytest.fixture
def refresh_token(jwt_auth: JWTAuth) -> str:
    """Create a test refresh token."""
    user_id = str(uuid.uuid4())
    return jwt_auth.create_refresh_token(
        subject=user_id,
        additional_claims={
            "roles": ["user"],
            "email": "test@example.com",
            "name": "Test User"
        }
    )


@pytest.fixture
def app(jwt_auth: JWTAuth) -> FastAPI:
    """Create test FastAPI application."""
    app = FastAPI()
    
    # Create security dependencies
    auth = JWTBearer(jwt_auth=jwt_auth)
    
    @app.get("/protected")
    def protected_route(token_data: TokenData = Depends(auth)):
        return {"user_id": token_data.sub, "roles": token_data.roles}
    
    @app.post("/refresh")
    def refresh_token_route(refresh_token: str):
        try:
            access_token = jwt_auth.refresh_access_token(refresh_token)
            return {"access_token": access_token}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}"
            )
    
    @app.get("/revoke/{token}")
    def revoke_token(token: str):
        success = jwt_auth.revoke_token(token)
        return {"revoked": success}
    
    @app.get("/cache-metrics")
    def cache_metrics():
        # Simple metrics endpoint to check cache size and contents
        # This would be more sophisticated in a real application
        cache_size = len(getattr(jwt_auth.token_cache, "token_cache", {}).cache)
        blacklist_size = len(getattr(jwt_auth.token_cache, "blacklist", {}).cache)
        return {
            "cache_size": cache_size,
            "blacklist_size": blacklist_size
        }
    
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_token_cache_get_set(token_cache: TokenCache):
    """Test token cache get and set operations."""
    token = "test_token"
    claims = {"sub": "user_id", "exp": int(time.time()) + 3600, "jti": str(uuid.uuid4())}
    
    # Cache should be empty initially
    assert token_cache.get(token) is None
    
    # Set token in cache
    token_cache.set(token, claims)
    
    # Get token from cache
    cached_claims = token_cache.get(token)
    assert cached_claims is not None
    assert cached_claims["sub"] == claims["sub"]
    assert cached_claims["exp"] == claims["exp"]
    assert cached_claims["jti"] == claims["jti"]
    
    # Invalidate token
    token_cache.invalidate(token)
    
    # Cache should be empty again
    assert token_cache.get(token) is None


def test_token_blacklist(token_cache: TokenCache):
    """Test token blacklisting functionality."""
    jti = str(uuid.uuid4())
    expiry = int(time.time()) + 3600
    
    # JTI should not be blacklisted initially
    assert not token_cache.is_blacklisted(jti)
    
    # Blacklist JTI
    token_cache.blacklist(jti, expiry)
    
    # JTI should be blacklisted now
    assert token_cache.is_blacklisted(jti)


def test_jwt_auth_with_cache(jwt_auth: JWTAuth, token_cache: TokenCache):
    """Test JWT authentication with token caching."""
    # Create token
    user_id = str(uuid.uuid4())
    token = jwt_auth.create_access_token(
        subject=user_id,
        additional_claims={"roles": ["user"]}
    )
    
    # First decode should not use cache
    token_data = jwt_auth.decode_token(token)
    assert token_data.sub == user_id
    
    # Check token is in cache
    cached_token = token_cache.get(token)
    assert cached_token is not None
    assert cached_token["sub"] == user_id
    
    # Second decode should use cache
    token_data = jwt_auth.decode_token(token)
    assert token_data.sub == user_id


def test_token_revocation(jwt_auth: JWTAuth, token_cache: TokenCache):
    """Test token revocation functionality."""
    # Create token
    user_id = str(uuid.uuid4())
    token = jwt_auth.create_access_token(
        subject=user_id,
        additional_claims={"roles": ["user"]}
    )
    
    # Decode token first to ensure it's valid
    token_data = jwt_auth.decode_token(token)
    assert token_data.sub == user_id
    
    # Revoke token
    revoked = jwt_auth.revoke_token(token)
    assert revoked
    
    # Try to decode revoked token
    with pytest.raises(jwt.InvalidTokenError):
        jwt_auth.decode_token(token)


def test_protected_route(client: TestClient, access_token: str):
    """Test protected route with valid token."""
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Make another request to use cached token
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200


def test_revoked_token_route(client: TestClient, access_token: str):
    """Test route access with revoked token."""
    # First request should succeed
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Revoke the token
    response = client.get(f"/revoke/{access_token}")
    assert response.status_code == 200
    assert response.json()["revoked"] == True
    
    # Request with revoked token should fail
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401


def test_token_refresh_with_cache(client: TestClient, refresh_token: str, jwt_auth: JWTAuth):
    """Test token refresh functionality with caching."""
    # Use refresh token to get access token
    response = client.post(
        "/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    
    # Check that token is cached
    cached_token = jwt_auth.token_cache.get(access_token)
    assert cached_token is not None
    
    # Use the new access token to access protected route
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200


def test_invalid_refresh_token(client: TestClient):
    """Test using an invalid refresh token."""
    response = client.post(
        "/refresh",
        json={"refresh_token": "invalid.token.string"}
    )
    assert response.status_code == 401


def test_expired_token_with_cache(jwt_auth: JWTAuth, token_cache: TokenCache):
    """Test handling of expired tokens in cache."""
    # Create token that expires very quickly
    user_id = str(uuid.uuid4())
    token = jwt_auth.create_access_token(
        subject=user_id,
        additional_claims={"roles": ["user"]},
        expires_delta=timedelta(seconds=1)
    )
    
    # First decode should not use cache
    token_data = jwt_auth.decode_token(token)
    assert token_data.sub == user_id
    
    # Wait for token to expire
    time.sleep(2)
    
    # Try to decode expired token
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt_auth.decode_token(token)
    
    # Check that expired token is removed from cache
    assert token_cache.get(token) is None


def test_cache_under_load(jwt_auth: JWTAuth, client: TestClient):
    """Test cache behavior under load (many tokens)."""
    # Generate many tokens
    tokens = [jwt_auth.create_access_token(subject=str(uuid.uuid4())) for _ in range(50)]
    
    # Access protected route with each token
    for token in tokens:
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    # Check cache metrics
    response = client.get("/cache-metrics")
    assert response.status_code == 200
    metrics = response.json()
    
    # Cache should contain entries for tokens
    assert metrics["cache_size"] > 0
    
    # Blacklist should be empty (no revocations yet)
    assert metrics["blacklist_size"] == 0
    
    # Revoke a few tokens
    for token in tokens[:5]:
        client.get(f"/revoke/{token}")
    
    # Check cache metrics again
    response = client.get("/cache-metrics")
    assert response.status_code == 200
    metrics = response.json()
    
    # Blacklist should now have entries
    assert metrics["blacklist_size"] > 0


def test_token_cache_ttl(jwt_auth: JWTAuth, token_cache_config: TokenCacheConfig):
    """Test token cache TTL functionality."""
    # Create a cache with very short TTL
    ttl_config = TokenCacheConfig(
        enabled=True,
        cache_type="memory",
        ttl=1,  # 1 second TTL
        max_size=1000,
        blacklist_enabled=True,
        blacklist_ttl=1  # 1 second TTL for blacklist
    )
    
    short_ttl_cache = MemoryTokenCache(ttl_config)
    
    # Store a token in cache
    token = "test_ttl_token"
    claims = {"sub": "user_id", "exp": int(time.time()) + 3600, "jti": str(uuid.uuid4())}
    short_ttl_cache.set(token, claims)
    
    # Verify token is in cache
    assert short_ttl_cache.get(token) is not None
    
    # Wait for TTL to expire
    time.sleep(2)
    
    # Token should no longer be in cache
    assert short_ttl_cache.get(token) is None
    
    # Test blacklist TTL
    jti = str(uuid.uuid4())
    expiry = int(time.time()) + 3600
    short_ttl_cache.blacklist(jti, expiry)
    
    # Verify JTI is blacklisted
    assert short_ttl_cache.is_blacklisted(jti)
    
    # Wait for TTL to expire
    time.sleep(2)
    
    # JTI should no longer be blacklisted
    assert not short_ttl_cache.is_blacklisted(jti)


def test_disabled_cache(jwt_auth: JWTAuth, token_cache_config: TokenCacheConfig):
    """Test that disabled cache doesn't store tokens."""
    # Create a disabled cache
    disabled_config = TokenCacheConfig(
        enabled=False,
        cache_type="memory",
        ttl=300,
        max_size=1000,
        blacklist_enabled=True
    )
    
    disabled_cache = MemoryTokenCache(disabled_config)
    
    # Store a token in cache
    token = "test_disabled_token"
    claims = {"sub": "user_id", "exp": int(time.time()) + 3600, "jti": str(uuid.uuid4())}
    disabled_cache.set(token, claims)
    
    # Token should not be stored
    assert disabled_cache.get(token) is None
    
    # Blacklisting should also do nothing
    jti = str(uuid.uuid4())
    expiry = int(time.time()) + 3600
    disabled_cache.blacklist(jti, expiry)
    
    # JTI should not be blacklisted
    assert not disabled_cache.is_blacklisted(jti)


def test_cache_max_size(jwt_auth: JWTAuth, token_cache_config: TokenCacheConfig):
    """Test cache max size limitation."""
    # Create a cache with small max size
    small_cache_config = TokenCacheConfig(
        enabled=True,
        cache_type="memory",
        ttl=300,
        max_size=5,  # Only store 5 tokens
        blacklist_enabled=True
    )
    
    small_cache = MemoryTokenCache(small_cache_config)
    
    # Store more tokens than max size
    for i in range(10):
        token = f"test_token_{i}"
        claims = {"sub": f"user_{i}", "exp": int(time.time()) + 3600, "jti": str(uuid.uuid4())}
        small_cache.set(token, claims)
    
    # Check that cache size is limited to max size
    # This assumes the MemoryCache implementation uses LRU eviction policy
    # which would keep the most recently accessed items
    cache_size = len(getattr(small_cache, "token_cache", {}).cache)
    assert cache_size <= small_cache_config.max_size


# Redis cache tests - these will be skipped if Redis is not available
@pytest.fixture
def redis_url():
    """Get Redis URL from environment variable or use default."""
    return os.environ.get("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
def redis_token_cache(redis_url):
    """Create Redis token cache if Redis is available."""
    if not redis_url:
        pytest.skip("Redis URL not provided")
        
    try:
        # Create token cache config
        redis_config = TokenCacheConfig(
            enabled=True,
            cache_type="redis",
            ttl=300,
            max_size=1000,
            blacklist_enabled=True,
            blacklist_ttl=86400,
            redis_url=redis_url
        )
        
        # Try to create Redis cache
        redis_cache = RedisTokenCache(redis_config, logger=logging.getLogger("test_redis_cache"))
        
        # If we get here, Redis is available
        return redis_cache
    except Exception as e:
        pytest.skip(f"Redis not available: {str(e)}")


@pytest.mark.redis
def test_redis_token_cache_basic(redis_token_cache):
    """Test basic Redis token cache operations."""
    token = "test_redis_token"
    claims = {"sub": "user_id", "exp": int(time.time()) + 3600, "jti": str(uuid.uuid4())}
    
    # Cache should be empty initially
    assert redis_token_cache.get(token) is None
    
    # Set token in cache
    redis_token_cache.set(token, claims)
    
    # Get token from cache
    cached_claims = redis_token_cache.get(token)
    assert cached_claims is not None
    assert cached_claims["sub"] == claims["sub"]
    assert cached_claims["exp"] == claims["exp"]
    assert cached_claims["jti"] == claims["jti"]
    
    # Invalidate token
    redis_token_cache.invalidate(token)
    
    # Cache should be empty again
    assert redis_token_cache.get(token) is None


@pytest.mark.redis
def test_redis_blacklist(redis_token_cache):
    """Test Redis blacklist functionality."""
    jti = str(uuid.uuid4())
    expiry = int(time.time()) + 3600
    
    # JTI should not be blacklisted initially
    assert not redis_token_cache.is_blacklisted(jti)
    
    # Blacklist JTI
    redis_token_cache.blacklist(jti, expiry)
    
    # JTI should be blacklisted now
    assert redis_token_cache.is_blacklisted(jti)
    
    # Clear cache and blacklist
    redis_token_cache.clear()


@pytest.mark.redis
def test_redis_jwt_auth_integration(jwt_auth: JWTAuth, redis_token_cache, token_cache_config: TokenCacheConfig):
    """Test JWT auth with Redis cache integration."""
    # Create a new JWT auth with Redis cache
    redis_jwt_auth = JWTAuth(
        config=token_cache_config,
        token_cache=redis_token_cache
    )
    
    # Create token
    user_id = str(uuid.uuid4())
    token = redis_jwt_auth.create_access_token(
        subject=user_id,
        additional_claims={"roles": ["user"]}
    )
    
    # First decode should not use cache
    token_data = redis_jwt_auth.decode_token(token)
    assert token_data.sub == user_id
    
    # Check token is in cache
    cached_token = redis_token_cache.get(token)
    assert cached_token is not None
    assert cached_token["sub"] == user_id
    
    # Second decode should use cache
    token_data = redis_jwt_auth.decode_token(token)
    assert token_data.sub == user_id
    
    # Revoke token
    revoked = redis_jwt_auth.revoke_token(token)
    assert revoked
    
    # Try to decode revoked token
    with pytest.raises(jwt.InvalidTokenError):
        redis_jwt_auth.decode_token(token)
        
    # Clear cache after test
    redis_token_cache.clear()