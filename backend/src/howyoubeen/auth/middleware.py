"""
Authentication middleware for protecting routes
"""

from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from .auth_service import get_auth_service

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Middleware for protecting routes with JWT authentication"""
    
    def __init__(self):
        self.auth_service = get_auth_service()
        self.bearer_scheme = HTTPBearer()
    
    async def get_current_user_from_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract and verify user from request headers"""
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return None
            
        if not authorization.startswith("Bearer "):
            return None
            
        token = authorization[7:]  # Remove "Bearer " prefix
        
        try:
            user = await self.auth_service.get_current_user(token)
            return user
        except Exception as e:
            logger.warning(f"Failed to authenticate user: {e}")
            return None
    
    async def require_auth(self, request: Request) -> Dict[str, Any]:
        """Require authentication - raise HTTPException if not authenticated"""
        user = await self.get_current_user_from_request(request)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    async def optional_auth(self, request: Request) -> Optional[Dict[str, Any]]:
        """Optional authentication - return user if authenticated, None otherwise"""
        return await self.get_current_user_from_request(request)


# Global middleware instance
_auth_middleware = None

def get_auth_middleware() -> AuthMiddleware:
    """Get global auth middleware instance"""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware()
    return _auth_middleware


# Convenience dependency functions that can be used in route handlers
async def require_authentication(request: Request) -> Dict[str, Any]:
    """Dependency that requires authentication"""
    middleware = get_auth_middleware()
    return await middleware.require_auth(request)

async def optional_authentication(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency for optional authentication"""
    middleware = get_auth_middleware()
    return await middleware.optional_auth(request)
