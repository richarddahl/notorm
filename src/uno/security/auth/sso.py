# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Single sign-on provider for Uno applications.

This module provides single sign-on (SSO) functionality for Uno applications,
with support for OAuth 2.0, SAML, and OpenID Connect.
"""

import json
import time
import secrets
import base64
import hashlib
import logging
from typing import Dict, List, Optional, Any, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
import urllib.parse

from uno.security.config import SSOProvider as SSOProviderType


@dataclass
class SSOUser:
    """Single sign-on user information."""
    
    id: str
    email: str
    name: str
    provider: str
    provider_user_id: str
    metadata: Dict[str, Any]


class SSOProvider(ABC):
    """
    Single sign-on provider.
    
    This is a base class for SSO providers, defining the common interface
    for authentication flows.
    """
    
    def __init__(
        self,
        provider_type: SSOProviderType,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the SSO provider.
        
        Args:
            provider_type: SSO provider type
            client_id: Client ID for the SSO provider
            client_secret: Client secret for the SSO provider
            redirect_uri: Redirect URI for the SSO flow
            logger: Logger
        """
        self.provider_type = provider_type
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.logger = logger or logging.getLogger(f"uno.security.auth.sso.{provider_type}")
    
    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get the authorization URL for the SSO flow.
        
        Args:
            state: Optional state parameter for the authorization request
            
        Returns:
            Authorization URL
        """
        pass
    
    @abstractmethod
    def handle_callback(self, code: str, state: Optional[str] = None) -> SSOUser:
        """
        Handle the callback from the SSO provider.
        
        Args:
            code: Authorization code from the callback
            state: State parameter from the callback
            
        Returns:
            User information from the SSO provider
        """
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> bool:
        """
        Validate an SSO token.
        
        Args:
            token: Token to validate
            
        Returns:
            True if the token is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an SSO token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token information
        """
        pass
    
    @abstractmethod
    def get_user_info(self, token: str) -> SSOUser:
        """
        Get user information from the SSO provider.
        
        Args:
            token: Access token
            
        Returns:
            User information
        """
        pass
    
    def generate_state(self) -> str:
        """
        Generate a state parameter for the authorization request.
        
        Returns:
            Generated state parameter
        """
        return secrets.token_urlsafe(32)
    
    def hash_state(self, state: str) -> str:
        """
        Hash a state parameter for verification.
        
        Args:
            state: State parameter
            
        Returns:
            Hashed state parameter
        """
        hasher = hashlib.sha256()
        hasher.update(state.encode())
        return base64.urlsafe_b64encode(hasher.digest()).decode()


class OAuth2Provider(SSOProvider):
    """
    OAuth 2.0 SSO provider.
    
    This class implements the OAuth 2.0 authentication flow.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorization_url: str,
        token_url: str,
        userinfo_url: str,
        scope: str = "openid email profile",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the OAuth 2.0 provider.
        
        Args:
            client_id: Client ID for the OAuth provider
            client_secret: Client secret for the OAuth provider
            redirect_uri: Redirect URI for the OAuth flow
            authorization_url: Authorization endpoint URL
            token_url: Token endpoint URL
            userinfo_url: User info endpoint URL
            scope: OAuth scope
            logger: Logger
        """
        super().__init__(
            SSOProviderType.OAUTH2,
            client_id,
            client_secret,
            redirect_uri,
            logger
        )
        self.authorization_url_base = authorization_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url
        self.scope = scope
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get the authorization URL for the OAuth flow.
        
        Args:
            state: Optional state parameter for the authorization request
            
        Returns:
            Authorization URL
        """
        if state is None:
            state = self.generate_state()
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state
        }
        
        return f"{self.authorization_url_base}?{urllib.parse.urlencode(params)}"
    
    def handle_callback(self, code: str, state: Optional[str] = None) -> SSOUser:
        """
        Handle the callback from the OAuth provider.
        
        Args:
            code: Authorization code from the callback
            state: State parameter from the callback
            
        Returns:
            User information from the OAuth provider
        """
        try:
            import requests
            
            # Exchange the code for a token
            token_response = requests.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code"
                },
                headers={"Accept": "application/json"}
            )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise ValueError("No access token in response")
            
            # Get user information
            user_response = requests.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            user_data = user_response.json()
            
            # Create SSOUser object
            return SSOUser(
                id=user_data.get("sub") or user_data.get("id"),
                email=user_data.get("email", ""),
                name=user_data.get("name", ""),
                provider="oauth2",
                provider_user_id=user_data.get("sub") or user_data.get("id"),
                metadata=user_data
            )
        except Exception as e:
            self.logger.error(f"OAuth callback error: {str(e)}")
            raise
    
    def validate_token(self, token: str) -> bool:
        """
        Validate an OAuth token.
        
        Args:
            token: Token to validate
            
        Returns:
            True if the token is valid, False otherwise
        """
        try:
            import requests
            
            # Get user information to validate the token
            user_response = requests.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            return user_response.status_code == 200
        except Exception as e:
            self.logger.error(f"Token validation error: {str(e)}")
            return False
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an OAuth token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token information
        """
        try:
            import requests
            
            # Exchange the refresh token for a new access token
            token_response = requests.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                },
                headers={"Accept": "application/json"}
            )
            
            return token_response.json()
        except Exception as e:
            self.logger.error(f"Token refresh error: {str(e)}")
            raise
    
    def get_user_info(self, token: str) -> SSOUser:
        """
        Get user information from the OAuth provider.
        
        Args:
            token: Access token
            
        Returns:
            User information
        """
        try:
            import requests
            
            # Get user information
            user_response = requests.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            user_data = user_response.json()
            
            # Create SSOUser object
            return SSOUser(
                id=user_data.get("sub") or user_data.get("id"),
                email=user_data.get("email", ""),
                name=user_data.get("name", ""),
                provider="oauth2",
                provider_user_id=user_data.get("sub") or user_data.get("id"),
                metadata=user_data
            )
        except Exception as e:
            self.logger.error(f"User info error: {str(e)}")
            raise


class OIDCProvider(OAuth2Provider):
    """
    OpenID Connect SSO provider.
    
    This class implements the OpenID Connect authentication flow,
    which is an extension of OAuth 2.0.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        issuer_url: str,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the OIDC provider.
        
        Args:
            client_id: Client ID for the OIDC provider
            client_secret: Client secret for the OIDC provider
            redirect_uri: Redirect URI for the OIDC flow
            issuer_url: OIDC issuer URL (e.g., https://accounts.google.com)
            logger: Logger
        """
        # Discover OIDC endpoints
        discovery_url = f"{issuer_url}/.well-known/openid-configuration"
        
        try:
            import requests
            discovery_response = requests.get(discovery_url)
            discovery_data = discovery_response.json()
            
            authorization_url = discovery_data.get("authorization_endpoint")
            token_url = discovery_data.get("token_endpoint")
            userinfo_url = discovery_data.get("userinfo_endpoint")
            
            if not authorization_url or not token_url or not userinfo_url:
                raise ValueError("Invalid OIDC discovery document")
            
            super().__init__(
                client_id,
                client_secret,
                redirect_uri,
                authorization_url,
                token_url,
                userinfo_url,
                "openid email profile",
                logger
            )
            
            self.provider_type = SSOProviderType.OIDC
            self.issuer_url = issuer_url
            self.jwks_uri = discovery_data.get("jwks_uri")
        except Exception as e:
            # Fall back to default initialization
            if logger:
                logger.error(f"OIDC discovery error: {str(e)}")
            super().__init__(
                client_id,
                client_secret,
                redirect_uri,
                f"{issuer_url}/protocol/openid-connect/auth",
                f"{issuer_url}/protocol/openid-connect/token",
                f"{issuer_url}/protocol/openid-connect/userinfo",
                "openid email profile",
                logger
            )
            self.provider_type = SSOProviderType.OIDC
            self.issuer_url = issuer_url
            self.jwks_uri = None
    
    def validate_token(self, token: str) -> bool:
        """
        Validate an OIDC token.
        
        Args:
            token: Token to validate
            
        Returns:
            True if the token is valid, False otherwise
        """
        try:
            # For OIDC, tokens are typically JWTs
            import jwt
            
            # Decode the token (without verification just to get the header)
            header = jwt.get_unverified_header(token)
            
            # Get the key ID
            kid = header.get("kid")
            if not kid:
                return False
            
            # Get the JWKS
            import requests
            jwks_response = requests.get(self.jwks_uri)
            jwks = jwks_response.json()
            
            # Find the key with the matching ID
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break
            
            if not key:
                return False
            
            # Convert JWK to PEM
            from jwt.algorithms import get_default_algorithms
            algorithms = get_default_algorithms()
            public_key = algorithms["RS256"].from_jwk(key)
            
            # Verify the token
            jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer_url
            )
            
            return True
        except Exception as e:
            self.logger.error(f"OIDC token validation error: {str(e)}")
            return False