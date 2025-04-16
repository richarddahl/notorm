"""
Domain endpoints for the Security module.

This module defines FastAPI endpoints for the Security module.
"""

from typing import Dict, List, Optional, Any, Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

from uno.core.result import Result
from uno.dependencies.service import inject_dependency
from uno.security.config import SecurityConfig
from uno.security.domain_services import (
    SecurityService,
    AuditServiceProtocol,
    EncryptionServiceProtocol,
    AuthenticationServiceProtocol,
    MFAServiceProtocol
)
from uno.security.domain_provider import (
    get_security_service,
    get_audit_service,
    get_encryption_service,
    get_authentication_service,
    get_mfa_service
)
from uno.security.entities import MFAType, TokenType, EventSeverity


# DTOs
class SecurityEventDTO(BaseModel):
    """DTO for security events."""
    
    id: str = Field(..., description="Event ID")
    event_type: str = Field(..., description="Event type")
    user_id: Optional[str] = Field(None, description="User ID")
    timestamp: datetime = Field(..., description="Event timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    success: bool = Field(True, description="Success flag")
    message: Optional[str] = Field(None, description="Event message")
    severity: str = Field(..., description="Event severity")
    details: Optional[Dict[str, Any]] = Field(None, description="Event details")


class CreateSecurityEventDTO(BaseModel):
    """DTO for creating security events."""
    
    event_type: str = Field(..., description="Event type")
    user_id: Optional[str] = Field(None, description="User ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    success: bool = Field(True, description="Success flag")
    message: Optional[str] = Field(None, description="Event message")
    severity: str = Field("info", description="Event severity")
    details: Optional[Dict[str, Any]] = Field(None, description="Event details")
    context: Dict[str, Any] = Field(default_factory=dict, description="Event context")


class PaginationParams(BaseModel):
    """Parameters for pagination."""
    
    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Page size")


class EventSearchParams(PaginationParams):
    """Parameters for security event search."""
    
    event_type: Optional[str] = Field(None, description="Event type")
    user_id: Optional[str] = Field(None, description="User ID")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    severity: Optional[str] = Field(None, description="Event severity")
    success: Optional[bool] = Field(None, description="Success flag")


class TokenRequestDTO(BaseModel):
    """DTO for token requests."""
    
    user_id: str = Field(..., description="User ID")
    token_type: str = Field(..., description="Token type")
    roles: List[str] = Field(default_factory=list, description="User roles")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    custom_claims: Dict[str, Any] = Field(default_factory=dict, description="Custom claims")


class TokenResponseDTO(BaseModel):
    """DTO for token responses."""
    
    token: str = Field(..., description="JWT token")
    token_id: str = Field(..., description="Token ID")
    expires_at: datetime = Field(..., description="Expiration time")
    token_type: str = Field(..., description="Token type")


class TokenValidationDTO(BaseModel):
    """DTO for token validation."""
    
    token: str = Field(..., description="JWT token")


class TokenValidationResponseDTO(BaseModel):
    """DTO for token validation responses."""
    
    valid: bool = Field(..., description="Validity flag")
    claims: Optional[Dict[str, Any]] = Field(None, description="Token claims")
    error: Optional[str] = Field(None, description="Error message")


class MFASetupRequestDTO(BaseModel):
    """DTO for MFA setup requests."""
    
    user_id: str = Field(..., description="User ID")
    mfa_type: str = Field("totp", description="MFA type")


class MFASetupResponseDTO(BaseModel):
    """DTO for MFA setup responses."""
    
    secret: str = Field(..., description="MFA secret")
    backup_codes: List[str] = Field(..., description="Backup codes")
    provision_uri: str = Field(..., description="Provision URI for QR code")
    type: str = Field(..., description="MFA type")


class MFAVerificationRequestDTO(BaseModel):
    """DTO for MFA verification requests."""
    
    user_id: str = Field(..., description="User ID")
    code: str = Field(..., description="MFA code")
    mfa_type: Optional[str] = Field(None, description="MFA type")


class MFAVerificationResponseDTO(BaseModel):
    """DTO for MFA verification responses."""
    
    valid: bool = Field(..., description="Validity flag")
    error: Optional[str] = Field(None, description="Error message")


class BackupCodeRegenerationRequestDTO(BaseModel):
    """DTO for backup code regeneration requests."""
    
    user_id: str = Field(..., description="User ID")


class BackupCodeRegenerationResponseDTO(BaseModel):
    """DTO for backup code regeneration responses."""
    
    backup_codes: List[str] = Field(..., description="Backup codes")


class PasswordValidationRequestDTO(BaseModel):
    """DTO for password validation requests."""
    
    password: str = Field(..., description="Password")


class PasswordValidationResponseDTO(BaseModel):
    """DTO for password validation responses."""
    
    valid: bool = Field(..., description="Validity flag")
    message: str = Field(..., description="Validation message")


# Security scheme
security_scheme = HTTPBearer()


# Endpoints
def create_security_router() -> APIRouter:
    """
    Create FastAPI router for security endpoints.
    
    Returns:
        FastAPI router
    """
    router = APIRouter(
        prefix="/api/security",
        tags=["security"],
        responses={401: {"description": "Unauthorized"}},
    )
    
    # Audit endpoints
    @router.post(
        "/events",
        response_model=SecurityEventDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create security event",
        description="Create a new security event for audit logging"
    )
    async def create_event(
        event: CreateSecurityEventDTO,
        request: Request,
        audit_service: AuditServiceProtocol = Depends(get_audit_service)
    ) -> SecurityEventDTO:
        """Create a new security event."""
        # Augment with request information if not provided
        if not event.ip_address:
            event.ip_address = request.client.host
            
        if not event.user_agent:
            event.user_agent = request.headers.get("user-agent")
        
        try:
            from uno.security.entities import SecurityEvent, EventSeverity
            
            # Create event entity
            event_entity = SecurityEvent(
                id=str(uuid.uuid4()),
                event_type=event.event_type,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                success=event.success,
                message=event.message,
                details=event.details,
                context=event.context,
                severity=EventSeverity(event.severity.upper())
            )
            
            # Log event
            result = await audit_service.log_event(event_entity)
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create security event: {result.error}"
                )
            
            # Return DTO
            return SecurityEventDTO(
                id=event_entity.id,
                event_type=event_entity.event_type,
                user_id=event_entity.user_id,
                timestamp=event_entity.timestamp,
                ip_address=event_entity.ip_address,
                user_agent=event_entity.user_agent,
                success=event_entity.success,
                message=event_entity.message,
                severity=event_entity.severity.value,
                details=event_entity.details
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create security event: {str(e)}"
            )
    
    @router.get(
        "/events",
        response_model=List[SecurityEventDTO],
        summary="Get security events",
        description="Get security events with filtering and pagination"
    )
    async def get_events(
        params: EventSearchParams = Depends(),
        audit_service: AuditServiceProtocol = Depends(get_audit_service),
        credentials: HTTPAuthorizationCredentials = Security(security_scheme)
    ) -> List[SecurityEventDTO]:
        """Get security events with filtering and pagination."""
        # Build search query
        query = {}
        if params.event_type:
            query["event_type"] = params.event_type
        if params.user_id:
            query["user_id"] = params.user_id
        if params.severity:
            query["severity"] = params.severity
        if params.success is not None:
            query["success"] = params.success
        if params.start_time and params.end_time:
            query["timestamp"] = {"$gte": params.start_time, "$lte": params.end_time}
        elif params.start_time:
            query["timestamp"] = {"$gte": params.start_time}
        elif params.end_time:
            query["timestamp"] = {"$lte": params.end_time}
        
        # Search events
        result = await audit_service.search_events(query, params.page, params.page_size)
        
        if result.is_failure():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get security events: {result.error}"
            )
        
        # Convert to DTOs
        return [
            SecurityEventDTO(
                id=event.id,
                event_type=event.event_type,
                user_id=event.user_id,
                timestamp=event.timestamp,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                success=event.success,
                message=event.message,
                severity=event.severity.value,
                details=event.details
            )
            for event in result.value
        ]
    
    # Authentication endpoints
    @router.post(
        "/tokens",
        response_model=TokenResponseDTO,
        summary="Generate token",
        description="Generate a new JWT token"
    )
    async def generate_token(
        request: TokenRequestDTO,
        auth_service: AuthenticationServiceProtocol = Depends(get_authentication_service)
    ) -> TokenResponseDTO:
        """Generate a new JWT token."""
        try:
            # Convert token type
            token_type = TokenType(request.token_type.upper())
            
            # Generate token
            result = await auth_service.generate_token(
                request.user_id,
                token_type,
                request.roles,
                request.tenant_id,
                request.custom_claims
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate token: {result.error}"
                )
            
            token_string, token_entity = result.value
            
            # Return DTO
            return TokenResponseDTO(
                token=token_string,
                token_id=token_entity.id.value,
                expires_at=token_entity.expires_at,
                token_type=token_entity.token_type.value
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate token: {str(e)}"
            )
    
    @router.post(
        "/tokens/validate",
        response_model=TokenValidationResponseDTO,
        summary="Validate token",
        description="Validate a JWT token"
    )
    async def validate_token(
        request: TokenValidationDTO,
        auth_service: AuthenticationServiceProtocol = Depends(get_authentication_service)
    ) -> TokenValidationResponseDTO:
        """Validate a JWT token."""
        try:
            # Validate token
            result = await auth_service.validate_token(request.token)
            
            if result.is_failure():
                return TokenValidationResponseDTO(
                    valid=False,
                    error=result.error
                )
            
            # Return validation result
            return TokenValidationResponseDTO(
                valid=True,
                claims=result.value
            )
        except Exception as e:
            return TokenValidationResponseDTO(
                valid=False,
                error=str(e)
            )
    
    @router.post(
        "/tokens/revoke/{token_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Revoke token",
        description="Revoke a JWT token"
    )
    async def revoke_token(
        token_id: str,
        auth_service: AuthenticationServiceProtocol = Depends(get_authentication_service),
        credentials: HTTPAuthorizationCredentials = Security(security_scheme)
    ) -> None:
        """Revoke a JWT token."""
        try:
            from uno.security.entities import TokenId
            
            # Revoke token
            result = await auth_service.revoke_token(TokenId(token_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to revoke token: {result.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to revoke token: {str(e)}"
            )
    
    @router.post(
        "/tokens/revoke-all/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Revoke all tokens",
        description="Revoke all tokens for a user"
    )
    async def revoke_all_tokens(
        user_id: str,
        auth_service: AuthenticationServiceProtocol = Depends(get_authentication_service),
        credentials: HTTPAuthorizationCredentials = Security(security_scheme)
    ) -> None:
        """Revoke all tokens for a user."""
        try:
            # Revoke all tokens
            result = await auth_service.revoke_all_user_tokens(user_id)
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to revoke tokens: {result.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to revoke tokens: {str(e)}"
            )
    
    # MFA endpoints
    @router.post(
        "/mfa/setup",
        response_model=MFASetupResponseDTO,
        summary="Set up MFA",
        description="Set up multi-factor authentication for a user"
    )
    async def setup_mfa(
        request: MFASetupRequestDTO,
        mfa_service: MFAServiceProtocol = Depends(get_mfa_service),
        credentials: HTTPAuthorizationCredentials = Security(security_scheme)
    ) -> MFASetupResponseDTO:
        """Set up multi-factor authentication for a user."""
        try:
            # Convert MFA type
            mfa_type = MFAType(request.mfa_type.upper())
            
            # Set up MFA
            result = await mfa_service.setup_mfa(request.user_id, mfa_type)
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to set up MFA: {result.error}"
                )
            
            # Return DTO
            return MFASetupResponseDTO(
                secret=result.value["secret"],
                backup_codes=result.value["backup_codes"],
                provision_uri=result.value["provision_uri"],
                type=result.value["type"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to set up MFA: {str(e)}"
            )
    
    @router.post(
        "/mfa/verify",
        response_model=MFAVerificationResponseDTO,
        summary="Verify MFA",
        description="Verify a multi-factor authentication code"
    )
    async def verify_mfa(
        request: MFAVerificationRequestDTO,
        mfa_service: MFAServiceProtocol = Depends(get_mfa_service)
    ) -> MFAVerificationResponseDTO:
        """Verify a multi-factor authentication code."""
        try:
            # Convert MFA type if provided
            mfa_type = MFAType(request.mfa_type.upper()) if request.mfa_type else None
            
            # Verify MFA
            result = await mfa_service.verify_mfa(request.user_id, request.code, mfa_type)
            
            if result.is_failure():
                return MFAVerificationResponseDTO(
                    valid=False,
                    error=result.error
                )
            
            # Return verification result
            return MFAVerificationResponseDTO(
                valid=result.value,
                error=None if result.value else "Invalid code"
            )
        except Exception as e:
            return MFAVerificationResponseDTO(
                valid=False,
                error=str(e)
            )
    
    @router.post(
        "/mfa/verify-backup",
        response_model=MFAVerificationResponseDTO,
        summary="Verify backup code",
        description="Verify a backup code for MFA"
    )
    async def verify_backup_code(
        request: MFAVerificationRequestDTO,
        mfa_service: MFAServiceProtocol = Depends(get_mfa_service)
    ) -> MFAVerificationResponseDTO:
        """Verify a backup code for MFA."""
        try:
            # Verify backup code
            result = await mfa_service.verify_backup_code(request.user_id, request.code)
            
            if result.is_failure():
                return MFAVerificationResponseDTO(
                    valid=False,
                    error=result.error
                )
            
            # Return verification result
            return MFAVerificationResponseDTO(
                valid=result.value,
                error=None if result.value else "Invalid backup code"
            )
        except Exception as e:
            return MFAVerificationResponseDTO(
                valid=False,
                error=str(e)
            )
    
    @router.post(
        "/mfa/deactivate/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Deactivate MFA",
        description="Deactivate multi-factor authentication for a user"
    )
    async def deactivate_mfa(
        user_id: str,
        mfa_service: MFAServiceProtocol = Depends(get_mfa_service),
        credentials: HTTPAuthorizationCredentials = Security(security_scheme)
    ) -> None:
        """Deactivate multi-factor authentication for a user."""
        try:
            # Deactivate MFA
            result = await mfa_service.deactivate_mfa(user_id)
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to deactivate MFA: {result.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deactivate MFA: {str(e)}"
            )
    
    @router.post(
        "/mfa/regenerate-backup-codes",
        response_model=BackupCodeRegenerationResponseDTO,
        summary="Regenerate backup codes",
        description="Regenerate backup codes for MFA"
    )
    async def regenerate_backup_codes(
        request: BackupCodeRegenerationRequestDTO,
        mfa_service: MFAServiceProtocol = Depends(get_mfa_service),
        credentials: HTTPAuthorizationCredentials = Security(security_scheme)
    ) -> BackupCodeRegenerationResponseDTO:
        """Regenerate backup codes for MFA."""
        try:
            # Regenerate backup codes
            result = await mfa_service.regenerate_backup_codes(request.user_id)
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to regenerate backup codes: {result.error}"
                )
            
            # Return backup codes
            return BackupCodeRegenerationResponseDTO(
                backup_codes=result.value
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to regenerate backup codes: {str(e)}"
            )
    
    # Password validation endpoint
    @router.post(
        "/password/validate",
        response_model=PasswordValidationResponseDTO,
        summary="Validate password",
        description="Validate a password against the password policy"
    )
    async def validate_password(
        request: PasswordValidationRequestDTO,
        auth_service: AuthenticationServiceProtocol = Depends(get_authentication_service)
    ) -> PasswordValidationResponseDTO:
        """Validate a password against the password policy."""
        try:
            # Validate password
            result = await auth_service.validate_password_policy(request.password)
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to validate password: {result.error}"
                )
            
            # Return validation result
            return PasswordValidationResponseDTO(
                valid=result.value["valid"],
                message=result.value["message"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to validate password: {str(e)}"
            )
    
    return router