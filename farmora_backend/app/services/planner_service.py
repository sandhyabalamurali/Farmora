import logging
import json
import re
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from farmora_backend.app.core.database import db
from farmora_backend.app.config import settings
import google.genai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def create_task(user_id: str, task_name: str, scheduled_date: str, 
                     description: Optional[str] = None, priority: str = "medium") -> Dict[str, Any]:
    """Create a new farm task for the user and refresh timeline cache."""
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
        
        # Update timeline cache if task is created with confirmed status
        if task.get("status") == "confirmed":
            await update_timeline_cache(user_id)
        
        return task
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise


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
        raise


async def update_timeline_cache(user_id: str):
    """
    Update the cached timeline for a user in the database.
    Should be called whenever tasks are created, updated, or deleted.
    """
    try:
        # Get all confirmed tasks for the user
        tasks = await get_user_tasks(user_id, status="confirmed")
        
        # Format tasks for timeline frontend
        timeline_items = [
            {
                "id": t.get("task_id"),
                "title": t.get("task_name"),
                "date": t.get("scheduled_date"),
                "description": t.get("description", ""),
                "priority": t.get("priority", "medium"),
                "status": t.get("status", "confirmed"),
            }
            for t in tasks
        ]
        
        # Sort by date (chronological order)
        timeline_items.sort(key=lambda x: x.get("date", "9999-12-31"))
        
        # Upsert timeline cache in database
        await db.db.timeline_cache.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "timeline": timeline_items,
                    "last_updated": datetime.utcnow(),
                    "count": len(timeline_items)
                }
            },
            upsert=True
        )
        
        logger.info(f"✅ Timeline cache updated for user {user_id}: {len(timeline_items)} tasks")
        return True
        
    except Exception as e:
        logger.error(f"Error updating timeline cache: {e}", exc_info=True)
        return False


async def get_cached_timeline(user_id: str) -> Dict[str, Any]:
    """
    Retrieve cached timeline for a user from database.
    If cache doesn't exist or is stale, rebuild it.
    Uses shorter TTL (60s) for more responsive updates.
    """
    try:
        # Try to get cached timeline
        cached = await db.db.timeline_cache.find_one({"user_id": user_id})
        
        if cached:
            # Check if cache is recent (60 seconds for faster updates)
            last_updated = cached.get("last_updated")
            if last_updated and (datetime.utcnow() - last_updated).total_seconds() < 60:
                logger.info(f"📦 Using cached timeline for user {user_id}")
                return {
                    "timeline": cached.get("timeline", []),
                    "last_updated": cached.get("last_updated")
                }
        
        # Cache miss or stale - rebuild
        logger.info(f"🔄 Rebuilding timeline cache for user {user_id}")
        await update_timeline_cache(user_id)
        
        # Fetch the newly created cache
        cached = await db.db.timeline_cache.find_one({"user_id": user_id})
        return {
            "timeline": cached.get("timeline", []) if cached else [],
            "last_updated": cached.get("last_updated") if cached else datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving cached timeline: {e}", exc_info=True)
        # Fallback to direct query
        tasks = await get_user_tasks(user_id, status="confirmed")
        timeline_items = [
            {
                "id": t.get("task_id"),
                "title": t.get("task_name"),
                "date": t.get("scheduled_date"),
                "description": t.get("description", ""),
                "priority": t.get("priority", "medium"),
                "status": t.get("status", "confirmed"),
            }
            for t in tasks
        ]
        return {"timeline": timeline_items, "last_updated": datetime.utcnow()}


async def update_task_status(task_id: str, status: str) -> bool:
    """Update task status (pending, confirmed, completed) and refresh timeline cache."""
    try:
        # First, get the task to find the user_id
        task = await db.db.tasks.find_one({"task_id": task_id})
        if not task:
            logger.warning(f"Task {task_id} not found")
            return False
        
        user_id = task.get("user_id")
        
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
            
            # Update timeline cache for any status change involving confirmed tasks
            # This ensures timeline stays in sync when tasks are confirmed, completed, or rejected
            if status in ["confirmed", "completed", "rejected"] or task.get("status") == "confirmed":
                await update_timeline_cache(user_id)
            
            return True
        
        logger.warning(f"Task {task_id} not found or already has status {status}")
        return False
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return False


async def generate_planner_suggestions(user_id: str, user_message: str, 
                                      user_profile: Optional[Dict] = None,
                                      language: str = "en") -> List[Dict[str, Any]]:
    """
    Generate AI-driven task suggestions using Gemini based on user request and farm profile.
    Supports multiple languages for task descriptions.
    """
    suggestions = []
    
    try:
        # Get current date for context-aware scheduling
        today = datetime.utcnow()
        current_date = today.strftime("%Y-%m-%d")
        current_month = today.strftime("%B")
        current_year = today.year
        
        # Calculate date range for tasks (next 7-30 days)
        min_task_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        max_task_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Build context from user profile
        context = f"""
        User ID: {user_id}
        User Message: {user_message}
        TODAY'S DATE: {current_date} ({current_month} {current_year})
        """
        
        if user_profile:
            lat = user_profile.get('latitude', None)
            lon = user_profile.get('longitude', None)
            location_info = user_profile.get('farm_location', 'Unknown')
            if lat and lon:
                location_info += f" (Lat: {lat}, Lon: {lon})"
            context += f"""
        Farm Location: {location_info}
        Crops Grown: {', '.join(user_profile.get('crops', [])) or 'Not specified'}
        """
        
        # Get existing tasks for context (avoid duplicate scheduling)
        existing_tasks = await get_user_tasks(user_id, status="pending")
        confirmed_tasks = await get_user_tasks(user_id, status="confirmed")
        all_scheduled = existing_tasks + confirmed_tasks
        
        existing_dates = set()
        existing_task_names = []
        for t in all_scheduled:
            if t.get("scheduled_date"):
                existing_dates.add(t.get("scheduled_date"))
            if t.get("task_name"):
                existing_task_names.append(t.get("task_name"))
        
        if all_scheduled:
            context += f"\nAlready scheduled tasks ({len(all_scheduled)} total): {', '.join(existing_task_names[:5])}"
            context += f"\nDates already taken: {', '.join(sorted(list(existing_dates))[:10])}"
        
        # LLM prompt for intelligent task generation
        lang_instruction = f"CRITICAL: Generate all text fields (task_name, reason, description, safety_notes, resources_needed) in {language} language." if language != "en" else ""
        
        existing_dates_str = ', '.join(sorted(list(existing_dates))[:10]) if existing_dates else 'None'
        
        planning_prompt = f"""{context}

You are an expert farm planning AI. Based on the user's request and farm profile, generate 2-4 specific, actionable farm tasks.

IMPORTANT DATE RULES:
- TODAY is {current_date}
- Tasks must be scheduled between {min_task_date} and {max_task_date}
- Each task MUST have a UNIQUE date - DO NOT use the same date for multiple tasks
- Space tasks appropriately (e.g., 3-7 days apart depending on task dependencies)
- Consider crop growth cycles and farming seasonality for {current_month}
- DO NOT schedule on dates already taken: {existing_dates_str}

For each task, provide a JSON object with:
{{
    "task_name": "specific action name",
    "date": "YYYY-MM-DD (MUST be unique, between {min_task_date} and {max_task_date})",
    "reason": "why this is important right now for {current_month} season",
    "priority": "high/medium/low",
    "description": "detailed instructions for completing this task",
    "estimated_hours": 2,
    "resources_needed": ["item1", "item2"],
    "safety_notes": "any safety precautions if pesticides/heavy equipment involved"
}}

Generate tasks that are:
- Specific and measurable with UNIQUE dates for each
- Actionable for the user's crops/location
- Based on seasonal best practices for {current_month}
- Spread across appropriate timeframes (not all on same day!)
- Logically sequenced (e.g., land prep before sowing, etc.)
- Include safety notes where relevant

{lang_instruction}

Respond ONLY with a valid JSON array, no other text. Ensure the JSON is properly formatted without line breaks in string values."""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=planning_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=4000,  # Increased to prevent truncation
            )
        )
        
        response_text = response.text.strip() if response.text else ""
        
        # Extract JSON from response with better error handling
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Try to find JSON array in the text using regex as fallback
            import re
            if not response_text.startswith('['):
                json_match = re.search(r'\[\s*\{[^\]]*\}\s*\]', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0)
            
            tasks_data = json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task suggestions JSON: {e}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}")
            # Return empty list instead of raising exception
            return []
        
        # Track used dates to ensure uniqueness in this batch
        used_dates_in_batch = set()
        task_index = 0
        
        # Process each task
        for task in tasks_data if isinstance(tasks_data, list) else []:
            if not task.get("task_name"):
                logger.warning(f"Skipping task without name: {task}")
                continue
            
            # Parse and validate date with uniqueness guarantee
            try:
                task_date = task.get("date", "")
                parsed_date = datetime.fromisoformat(task_date) if task_date else None
                
                # Ensure date is in the future
                if not parsed_date or parsed_date.date() <= datetime.utcnow().date():
                    parsed_date = datetime.utcnow() + timedelta(days=1 + task_index)
                
                # Ensure date is unique (not used in this batch or existing tasks)
                while parsed_date.strftime("%Y-%m-%d") in used_dates_in_batch:
                    parsed_date += timedelta(days=1)
                
                task_date = parsed_date.strftime("%Y-%m-%d")
                used_dates_in_batch.add(task_date)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Date parse error: {e}, using fallback")
                fallback_date = datetime.utcnow() + timedelta(days=1 + task_index)
                while fallback_date.strftime("%Y-%m-%d") in used_dates_in_batch:
                    fallback_date += timedelta(days=1)
                task_date = fallback_date.strftime("%Y-%m-%d")
                used_dates_in_batch.add(task_date)
            
            task_index += 1
            
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
                "requires_confirmation": True,
                "status": "pending"
            }
            
            # Persist the suggested task
            created = await create_task(
                user_id=user_id,
                task_name=suggestion["task_name"],
                scheduled_date=suggestion["date"],
                description=suggestion.get("description", ""),
                priority=suggestion.get("priority", "medium")
            )

            if created and created.get("task_id"):
                suggestion["task_id"] = created.get("task_id")
                suggestion["status"] = created.get("status", "pending")
                logger.info(f"Generated and persisted task: {suggestion['task_name']} ({suggestion['task_id']}) for user {user_id}")
                suggestions.append(suggestion)
            else:
                raise Exception(f"Failed to persist task: {suggestion['task_name']}")
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error generating planner suggestions: {e}", exc_info=True)
        raise


async def validate_and_confirm_task(task_id: str, user_id: str, confirmation: bool) -> bool:
    """
    Farmer confirmation logic: Accept or reject a suggested task.
    """
    try:
        if confirmation:
            status = "confirmed"
            logger.info(f"Task {task_id} confirmed by farmer {user_id}")
        else:
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
    """
    try:
        tasks = await get_user_tasks(user_id, status="pending")
        return tasks
    except Exception as e:
        logger.error(f"Error fetching pending tasks: {e}")
        raise
