"""
User model for Farmora backend.
Handles user profile and authentication data.
"""

from datetime import datetime
from typing import Optional, List


class User:
    """User model with authentication fields."""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        name: str,
        password_hash: str,
        farm_location: str = "",
        crops: Optional[List[str]] = None,
        phone: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.farm_location = farm_location
        self.crops = crops or []
        self.phone = phone
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self):
        """Convert user to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "password_hash": self.password_hash,
            "farm_location": self.farm_location,
            "crops": self.crops,
            "phone": self.phone,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @staticmethod
    def from_dict(data: dict):
        """Create User instance from dictionary."""
        return User(
            user_id=data.get("user_id"),
            email=data.get("email"),
            name=data.get("name"),
            password_hash=data.get("password_hash"),
            farm_location=data.get("farm_location", ""),
            crops=data.get("crops", []),
            phone=data.get("phone", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
