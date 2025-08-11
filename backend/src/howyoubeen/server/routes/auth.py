"""Authentication routes for user login/registration"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
import logging

from ...auth.auth_service import get_auth_service, AuthService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Request/Response Models
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class AuthResponse(BaseModel):
    user: Dict[str, Any]
    token: str
    expires_in: int

class UserResponse(BaseModel):
    user: Dict[str, Any]

def get_auth() -> AuthService:
    """Get auth service dependency"""
    return get_auth_service()

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth)
) -> Dict[str, Any]:
    """Dependency to get current user from JWT token"""
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return user


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth)
) -> Dict[str, Any]:
    """Register a new user with email/password"""
    try:
        result = await auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        return result
        
    except ValueError as e:
        # Handle duplicate username/email
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth)
) -> Dict[str, Any]:
    """Login user with email/password"""
    try:
        result = await auth_service.login_user(
            email=request.email,
            password=request.password
        )
        return result
        
    except ValueError as e:
        # Invalid credentials
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Get current authenticated user information"""
    return {"user": current_user}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    auth_service: AuthService = Depends(get_auth)
) -> Dict[str, str]:
    """Change user password"""
    try:
        user_id = current_user['user_id']
        await auth_service.change_password(
            user_id=user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        return {"message": "Password changed successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, str]:
    """Logout user (client should discard token)"""
    # Since we're using stateless JWT tokens, logout is handled client-side
    # by discarding the token. In a production app, you might maintain a 
    # blacklist of invalidated tokens.
    return {"message": "Logged out successfully"}


# Optional: Token refresh endpoint
@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    auth_service: AuthService = Depends(get_auth)
) -> Dict[str, Any]:
    """Refresh JWT token for authenticated user"""
    try:
        # Generate new token for current user
        user_id = current_user['user_id']
        username = current_user['username']
        
        token = auth_service.generate_jwt_token(user_id, username)
        
        return {
            'user': current_user,
            'token': token,
            'expires_in': auth_service.jwt_expiry_hours * 3600
        }
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
