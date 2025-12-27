"""
Authentication service for user signup and login.
Handles user creation, password verification, and JWT token generation.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from farmora_backend.app.core.database import db
from farmora_backend.app.core.security import hash_password, verify_password, create_access_token
from farmora_backend.app.schemas.chat_schema import SignupRequest, LoginRequest, TokenResponse, UserResponseSchema
from farmora_backend.app.models.user import User

logger = logging.getLogger(__name__)


async def signup_user(signup_data: SignupRequest) -> TokenResponse:
    """
    Register a new user and return JWT token.
    
    Args:
        signup_data: SignupRequest with email, name, password, GPS location, etc.
    
    Returns:
        TokenResponse with access token and user info
    
    Raises:
        Exception: If user already exists or database error occurs
    """
    try:
        # Check if user already exists
        existing_user = await db.db.users.find_one({"email": signup_data.email})
        if existing_user:
            raise ValueError(f"User with email {signup_data.email} already exists")
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(signup_data.password)
        
        user = User(
            user_id=user_id,
            email=signup_data.email,
            name=signup_data.name,
            password_hash=password_hash,
            farm_location=signup_data.farm_location or "",
            crops=signup_data.crops or [],
            phone=signup_data.phone or "",
            latitude=signup_data.latitude,
            longitude=signup_data.longitude,
            language=signup_data.language or "en",
        )
        
        # Save to MongoDB
        user_doc = user.to_dict()
        result = await db.db.users.insert_one(user_doc)
        
        if not result.inserted_id:
            raise Exception("Failed to insert user into database")
        
        logger.info(f"✅ New user registered: {user_id} ({signup_data.email}) at lat:{signup_data.latitude}, lon:{signup_data.longitude}")
        
        # Create JWT token
        token = create_access_token(
            data={"user_id": user_id, "email": signup_data.email}
        )
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=user_id,
            email=signup_data.email,
            name=signup_data.name,
            language=signup_data.language or "en",
            expires_in=86400
        )
        
    except ValueError as e:
        logger.warning(f"Signup error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during signup: {e}", exc_info=True)
        raise


async def login_user(login_data: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT token.
    
    Args:
        login_data: LoginRequest with email and password
    
    Returns:
        TokenResponse with access token and user info
    
    Raises:
        Exception: If user not found or password incorrect
    """
    try:
        # Find user by email
        user_doc = await db.db.users.find_one({"email": login_data.email})
        if not user_doc:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not verify_password(login_data.password, user_doc["password_hash"]):
            raise ValueError("Invalid email or password")
        
        logger.info(f"✅ User logged in: {user_doc['user_id']} ({login_data.email})")
        
        # Create JWT token
        token = create_access_token(
            data={"user_id": user_doc["user_id"], "email": user_doc["email"]}
        )
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=user_doc["user_id"],
            email=user_doc["email"],
            name=user_doc["name"],
            language=user_doc.get("language", "en"),
            expires_in=86400
        )
        
    except ValueError as e:
        logger.warning(f"Login error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        raise


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user by ID from MongoDB.
    
    Args:
        user_id: User ID string
    
    Returns:
        User document or None if not found
    """
    try:
        user = await db.db.users.find_one({"user_id": user_id})
        return user
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None


async def get_user_profile_full(user_id: str) -> Optional[UserResponseSchema]:
    """
    Get full user profile as response schema.
    
    Args:
        user_id: User ID string
    
    Returns:
        UserResponseSchema or None if not found
    """
    try:
        user = await get_user_by_id(user_id)
        if not user:
            return None
        
        return UserResponseSchema(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            farm_location=user.get("farm_location", ""),
            crops=user.get("crops", []),
            phone=user.get("phone", ""),
            latitude=user.get("latitude"),
            longitude=user.get("longitude"),
            language=user.get("language", "en"),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at")
        )
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None
