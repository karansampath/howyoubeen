"""
Authentication service for password-based authentication
"""

import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import os

from ..data_models.models import User
from ..storage.storage_factory import get_storage_service

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self):
        self.storage = get_storage_service()
        # Use environment variable for JWT secret, fallback to default for dev
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
        self.jwt_algorithm = "HS256"
        self.jwt_expiry_hours = 24
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def generate_jwt_token(self, user_id: str, username: str) -> str:
        """Generate a JWT token for authenticated user"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token and return the payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
    
    async def register_user(self, username: str, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """
        Register a new user with password authentication
        
        Args:
            username: Unique username
            email: User email
            password: Plain text password (will be hashed)
            full_name: User's full name
            
        Returns:
            Dict with user info and JWT token
            
        Raises:
            ValueError: If username/email already exists
        """
        # Check if username or email already exists
        existing_user_by_username = await self.storage.get_user_by_username(username)
        if existing_user_by_username:
            raise ValueError("Username already exists")
        
        existing_user_by_email = await self.storage.get_user_by_email(email)
        if existing_user_by_email:
            raise ValueError("Email already exists")
        
        # Hash password and create user
        password_hash = self.hash_password(password)
        
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'is_public': True,
            'onboarding_completed': False,
        }
        
        # Create user in storage
        created_user = await self.storage.create_user(user_data)
        user_id = created_user.get('user_id') or created_user.get('id')
        
        # Generate JWT token
        token = self.generate_jwt_token(user_id, username)
        
        return {
            'user': {
                'user_id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'is_public': created_user.get('is_public', True),
                'onboarding_completed': created_user.get('onboarding_completed', False),
                'created_at': created_user.get('created_at')
            },
            'token': token,
            'expires_in': self.jwt_expiry_hours * 3600  # seconds
        }
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user with email and password
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Dict with user info and JWT token
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Get user by email
        user = await self.storage.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Check if user has password_hash (for backward compatibility)
        password_hash = user.get('password_hash')
        if not password_hash:
            raise ValueError("User account not set up for password authentication")
        
        # Verify password
        if not self.verify_password(password, password_hash):
            raise ValueError("Invalid email or password")
        
        # Update last login time
        user_id = user.get('user_id') or user.get('id')
        await self.storage.update_user(user_id, {'last_login': datetime.utcnow()})
        
        # Generate JWT token
        username = user.get('username')
        token = self.generate_jwt_token(user_id, username)
        
        return {
            'user': {
                'user_id': user_id,
                'username': username,
                'email': user.get('email'),
                'full_name': user.get('full_name'),
                'is_public': user.get('is_public', True),
                'onboarding_completed': user.get('onboarding_completed', False),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login')
            },
            'token': token,
            'expires_in': self.jwt_expiry_hours * 3600  # seconds
        }
    
    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get current user from JWT token
        
        Args:
            token: JWT token
            
        Returns:
            User data or None if token invalid
        """
        payload = self.verify_jwt_token(token)
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        # Get fresh user data from storage
        user = await self.storage.get_user(user_id)
        if not user:
            return None
        
        return {
            'user_id': user.get('user_id') or user.get('id'),
            'username': user.get('username'),
            'email': user.get('email'),
            'full_name': user.get('full_name'),
            'is_public': user.get('is_public', True),
            'onboarding_completed': user.get('onboarding_completed', False),
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login')
        }
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user's password
        
        Args:
            user_id: User ID
            current_password: Current plain text password
            new_password: New plain text password
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If current password is incorrect
        """
        # Get user
        user = await self.storage.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        current_hash = user.get('password_hash')
        if not current_hash or not self.verify_password(current_password, current_hash):
            raise ValueError("Current password is incorrect")
        
        # Hash new password and update
        new_hash = self.hash_password(new_password)
        await self.storage.update_user(user_id, {'password_hash': new_hash})
        
        return True


# Singleton instance
_auth_service = None

def get_auth_service() -> AuthService:
    """Get global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
