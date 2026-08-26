"""Authentication endpoints for user registration, login, and token refresh.

This module provides REST API endpoints for user authentication:
- Registration: Create a new user account
- Login: Authenticate and receive JWT tokens
- Refresh: Get a new access token using a refresh token
- Logout: Invalidate the current session (optional)
- Current User: Get the authenticated user's profile
"""

import re
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_active_user,
    decode_token,
)
from app.core.rabbitmq import rabbitmq_client
from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus

# ============================================
# LOGGING
# ============================================

logger = logging.getLogger(settings.SERVICE_NAME)

# ============================================
# PYDANTIC MODELS
# ============================================

# Router prefix is set here - will be combined with main router prefix
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


class UserRegister(BaseModel):
    """User registration request model."""

    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=30, description="Unique username")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")
    full_name: Optional[str] = Field(None, max_length=200, description="User's full name")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "securepassword123",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """User login request model."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "securepassword123"
            }
        }


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="JWT access token (expires in 15 minutes)")
    refresh_token: str = Field(..., description="JWT refresh token (expires in 7 days)")
    token_type: str = Field(default="bearer", description="Token type")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str = Field(..., description="Refresh token to get a new access token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        }


class UserResponse(BaseModel):
    """User response model."""

    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    status: str
    is_email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request model."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 characters)")

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newsecurepassword456"
            }
        }


# ============================================
# ENDPOINTS
# ============================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Creates a new user with the provided email, username, and password.
    The user will be in PENDING status until email verification.

    Args:
        user_data: The registration data.
        request: The HTTP request object.
        db: The database session.

    Returns:
        UserResponse: The created user data.

    Raises:
        HTTPException: If email or username already exists, or validation fails.
    """
    # Validate username (alphanumeric and underscore only)
    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 3-30 characters and contain only letters, numbers, and underscores"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Validate password strength (optional)
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=UserRole.USER,
        status=UserStatus.PENDING,
        is_email_verified=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Publish UserRegistered event
    try:
        rabbitmq_client.publish_event(
            event_type="UserRegistered",
            data={
                "user_id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": request.client.host if request.client else "unknown",
            },
            routing_key="user.registered"
        )
    except Exception as e:
        logger.warning(f"Failed to publish UserRegistered event: {e}")

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    Validates username and password, then returns access and refresh tokens.

    Args:
        login_data: The login credentials.
        request: The HTTP request object.
        db: The database session.

    Returns:
        TokenResponse: Access and refresh tokens.

    Raises:
        HTTPException: If credentials are invalid or account is inactive.
    """
    # Find user by username
    user = db.query(User).filter(User.username == login_data.username).first()

    # Validate user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active (not pending, inactive, or suspended)
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is pending verification. Please verify your email.",
        )

    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Please contact support.",
        )

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create tokens
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value,
    }

    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # Store user in request state for rate limiting
    request.state.user_id = user.id
    request.state.current_user = user

    # Publish UserLoggedIn event
    try:
        rabbitmq_client.publish_event(
            event_type="UserLoggedIn",
            data={
                "user_id": user.id,
                "username": user.username,
                "ip_address": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            routing_key="user.loggedin"
        )
    except Exception as e:
        logger.warning(f"Failed to publish UserLoggedIn event: {e}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh the access token using a valid refresh token.

    Returns a new access token and a new refresh token.

    Args:
        refresh_request: The refresh token request.
        request: The HTTP request object.
        db: The database session.

    Returns:
        TokenResponse: New access and refresh tokens.

    Raises:
        HTTPException: If the refresh token is invalid or expired.
    """
    try:
        # Decode the refresh token
        payload = decode_token(refresh_request.refresh_token)

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token.",
            )

        # Extract user ID
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value}. Cannot refresh token.",
            )

        # Create new tokens
        token_data = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        # Store user in request state for rate limiting
        request.state.user_id = user.id
        request.state.current_user = user

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout the current user.

    Note: Since JWT tokens are stateless, this endpoint is primarily
    for notifying the client to discard tokens. A real logout would
    require a token blacklist (implemented separately).

    Args:
        request: The HTTP request object.
        current_user: The authenticated user.

    Returns:
        dict: Success message.
    """
    return {
        "message": "Successfully logged out",
        "user_id": current_user.id,
        "username": current_user.username,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current authenticated user's profile.

    Returns the authenticated user's information.

    Args:
        request: The HTTP request object.
        current_user: The authenticated user.

    Returns:
        UserResponse: The user's profile data.
    """
    # Store user in request state for rate limiting
    request.state.user_id = current_user.id
    request.state.current_user = current_user

    return current_user


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.

    Requires the current password for verification.

    Args:
        password_data: The current and new passwords.
        request: The HTTP request object.
        current_user: The authenticated user.
        db: The database session.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If the current password is incorrect.
    """
    # Store user in request state for rate limiting
    request.state.user_id = current_user.id
    request.state.current_user = current_user

    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long",
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Password changed successfully",
        "user_id": current_user.id,
    }


@router.get("/verify", response_model=UserResponse)
async def verify_email(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify a user's email address using a verification token.

    This endpoint is called from the verification link sent via email.

    Args:
        token: The verification token (JWT containing user_id).
        request: The HTTP request object.
        db: The database session.

    Returns:
        UserResponse: The verified user data.

    Raises:
        HTTPException: If the token is invalid or user not found.
    """
    try:
        # Decode the verification token
        payload = decode_token(token)

        # Verify it's a verification token
        if payload.get("type") != "verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token type",
            )

        # Extract user ID
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check if already verified
        if user.is_email_verified:
            return {
                "message": "Email already verified",
                "user": user,
            }

        # Verify the user
        user.is_email_verified = True
        user.status = UserStatus.ACTIVE
        user.email_verified_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

        # Store user in request state for rate limiting
        request.state.user_id = user.id
        request.state.current_user = user

        return {
            "message": "Email verified successfully",
            "user": user,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification token: {str(e)}",
        )