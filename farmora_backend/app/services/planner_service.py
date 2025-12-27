import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from groq import Groq
from farmora_backend.app.core.database import db
from farmora_backend.app.config import settings

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.GROQ_API_KEY)


async def create_task(user_id: str, task_name: str, scheduled_date: str, 
                     description: Optional[str] = None, priority: str = "medium") -> Dict[str, Any]:
    """Create a new farm task for the user."""
    task_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    task = {
        "task_id": task_id,
        "user_id": user_id,
        "task_name": task_name,
        "description": description or "",
        "scheduled_date": scheduled_date,
        "priority": priority,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "completed_at": None
    }
    
    try:
        await db.db.tasks.insert_one(task)
        logger.info(f"Task created: {task_id} for user {user_id}")
        return task
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return {}


async def get_user_tasks(user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve tasks for a user, optionally filtered by status."""
    try:
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        tasks = await db.db.tasks.find(query).to_list(None)
        return tasks
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        return []


async def update_task_status(task_id: str, status: str) -> bool:
    """Update task status (pending, confirmed, completed)."""
    try:
        completed_at = datetime.utcnow() if status == "completed" else None
        result = await db.db.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow(),
                    "completed_at": completed_at
                }
            }
        )
        if result.modified_count > 0:
            logger.info(f"Task {task_id} status updated to {status}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return False


async def generate_planner_suggestions(user_id: str, user_message: str, 
                                      user_profile: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Generate AI-driven task suggestions based on user request and farm profile.
    Uses LLM to understand user context and create intelligent recommendations.
    Includes minimal safety checks before farmer confirmation.
    """
    suggestions = []
    
    try:
        # Build context from user profile
        context = f"""
        User ID: {user_id}
        User Message: {user_message}
        """
        
        if user_profile:
            context += f"""
        Farm Location: {user_profile.get('farm_location', 'Unknown')}
        Crops Grown: {', '.join(user_profile.get('crops', [])) or 'Not specified'}
        """
        
        # Get existing tasks for context
        existing_tasks = await get_user_tasks(user_id, status="pending")
        if existing_tasks:
            context += f"\nPending tasks: {len(existing_tasks)} tasks already scheduled"
        
        # MINIMAL SAFETY CHECK: Warn if too many pending tasks
        if len(existing_tasks) > 5:
            context += "\n⚠️ NOTE: User has many pending tasks. Suggest consolidation where possible."
        
        # LLM prompt for intelligent task generation
        planning_prompt = f"""{context}

You are an expert farm planning AI. Based on the user's request and farm profile, generate 2-4 specific, actionable farm tasks.

For each task, provide a JSON object with:
{{
    "task_name": "specific action name",
    "date": "YYYY-MM-DD (next 7-30 days)",
    "reason": "why this is important right now (considering season, crop cycle, weather patterns)",
    "priority": "high/medium/low",
    "description": "detailed instructions for completing this task",
    "estimated_hours": 2,
    "resources_needed": ["item1", "item2"],
    "safety_notes": "any safety precautions if pesticides/heavy equipment involved"
}}

Generate tasks that are:
- Specific and measurable
- Actionable for the user's crops/location
- Based on seasonal best practices
- Spread across appropriate timeframes
- Include safety notes where relevant

Respond ONLY with a valid JSON array, no other text."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert agricultural planning assistant. Generate practical, seasonal farm tasks with safety considerations. Always respond with valid JSON array only."
                },
                {
                    "role": "user",
                    "content": planning_prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            tasks_data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse task suggestions JSON")
            tasks_data = []
        
        # SAFETY VALIDATION: Check each task before adding to suggestions
        for task in tasks_data if isinstance(tasks_data, list) else []:
            # Validate task has required fields
            if not task.get("task_name"):
                logger.warning(f"Skipping task without name: {task}")
                continue
            
            # Parse and validate date
            try:
                task_date = task.get("date", (datetime.utcnow() + timedelta(days=1)).isoformat()[:10])
                # Ensure date is in future
                if datetime.fromisoformat(task_date) < datetime.utcnow():
                    task_date = (datetime.utcnow() + timedelta(days=1)).isoformat()[:10]
            except (ValueError, TypeError):
                task_date = (datetime.utcnow() + timedelta(days=1)).isoformat()[:10]
            
            # Validate priority
            priority = task.get("priority", "medium").lower()
            if priority not in ["low", "medium", "high"]:
                priority = "medium"
            
            suggestion = {
                "task_id": None,
                "task_name": task.get("task_name", "Farm task"),
                "date": task_date,
                "reason": task.get("reason", "Regular farm maintenance"),
                "priority": priority,
                "description": task.get("description", ""),
                "estimated_hours": task.get("estimated_hours", 2),
                "resources_needed": task.get("resources_needed", []),
                "safety_notes": task.get("safety_notes", ""),
                "requires_confirmation": True,  # Always require farmer confirmation
                "status": "pending"
            }
            
            # Persist the suggested task as a pending task in DB so it can be confirmed later
            created = await create_task(
                user_id=user_id,
                task_name=suggestion["task_name"],
                scheduled_date=suggestion["date"],
                description=suggestion.get("description", ""),
                priority=suggestion.get("priority", "medium")
            )

            if created and created.get("task_id"):
                suggestion["task_id"] = created.get("task_id")
                # Keep status as 'pending' until user confirms
                suggestion["status"] = created.get("status", "pending")
                logger.info(f"Generated and persisted task: {suggestion['task_name']} ({suggestion['task_id']}) for user {user_id}")
                suggestions.append(suggestion)
            else:
                logger.warning(f"Failed to persist generated task for user {user_id}: {suggestion['task_name']}")
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error generating planner suggestions: {e}", exc_info=True)
        return []


async def validate_and_confirm_task(task_id: str, user_id: str, confirmation: bool) -> bool:
    """
    Farmer confirmation logic: Accept or reject a suggested task.
    Once confirmed, task moves from 'pending' to 'confirmed' status.
    
    Args:
        task_id: Task to confirm
        user_id: User confirming task
        confirmation: True to confirm, False to reject
    
    Returns:
        Boolean indicating success
    """
    try:
        if confirmation:
            # Save confirmed task to database
            status = "confirmed"
            logger.info(f"Task {task_id} confirmed by farmer {user_id}")
        else:
            # Mark as rejected
            status = "rejected"
            logger.info(f"Task {task_id} rejected by farmer {user_id}")
        
        result = await update_task_status(task_id, status)
        return result
        
    except Exception as e:
        logger.error(f"Error in task confirmation: {e}")
        return False


async def get_tasks_awaiting_confirmation(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all tasks awaiting farmer confirmation.
    
    Args:
        user_id: User ID
    
    Returns:
        List of pending tasks requiring confirmation
    """
    try:
        tasks = await get_user_tasks(user_id, status="pending")
        return tasks
    except Exception as e:
        logger.error(f"Error fetching pending tasks: {e}")
        return []

