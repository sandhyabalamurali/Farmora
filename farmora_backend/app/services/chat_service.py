import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from farmora_backend.app.core.database import db

logger = logging.getLogger(__name__)


async def save_chat_history(user_id: str, user_message: str, ai_response: str, 
                           intent: str, metadata: Optional[Dict] = None) -> bool:
    """Save chat interaction to MongoDB."""
    try:
        chat_entry = {
            "chat_id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "intent": intent,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        
        await db.db.chat_history.insert_one(chat_entry)
        logger.info(f"Chat saved for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")
        return False


async def get_user_chat_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent chat history for a user."""
    try:
        chats = await db.db.chat_history.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).to_list(limit)
        return chats
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        return []


async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get or create user profile."""
    try:
        user = await db.db.users.find_one({"user_id": user_id})
        
        if not user:
            # Create default profile
            user = {
                "user_id": user_id,
                "name": None,
                "farm_location": None,
                "crops": [],
                "preferences": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.db.users.insert_one(user)
            logger.info(f"New user profile created: {user_id}")
        
        return user
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None


async def update_user_profile(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user profile information."""
    try:
        updates["updated_at"] = datetime.utcnow()
        result = await db.db.users.update_one(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True
        )
        logger.info(f"User profile updated: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return False


async def get_context_from_history(user_id: str, limit: int = 5) -> str:
    """Build context from recent chat history for LLM."""
    try:
        chats = await get_user_chat_history(user_id, limit)
        context = ""
        for chat in reversed(chats):  # Most recent last
            context += f"User: {chat.get('user_message', '')}\nAssistant: {chat.get('ai_response', '')}\n\n"
        return context
    except Exception as e:
        logger.error(f"Error building context: {e}")
        return ""
