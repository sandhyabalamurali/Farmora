import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Header, Body
from fastapi.encoders import jsonable_encoder
from farmora_backend.app.schemas.chat_schema import (
    ChatInput, ChatResponse, DiseaseDetectionResult, MarketNews, DashboardData,
    SignupRequest, LoginRequest, TokenResponse, UserResponseSchema
)
from farmora_backend.app.schemas.planner_schema import ConfirmTaskRequest, TaskCompleteRequest
from farmora_backend.app.services.ai_graph import farmora_ai
from farmora_backend.app.services.chat_service import save_chat_history, get_user_profile, update_user_profile
from farmora_backend.app.services.disease_service import analyze_disease
from farmora_backend.app.services.planner_service import generate_planner_suggestions
from farmora_backend.app.services.dashboard_service import get_dashboard_context
from farmora_backend.app.services.auth_service import signup_user, login_user, get_user_profile_full
from farmora_backend.app.core.database import db
from farmora_backend.app.core.security import verify_token, extract_token_from_header
from datetime import datetime
from farmora_backend.app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== AUTHENTICATION ENDPOINTS =====

@router.post("/auth/signup", response_model=TokenResponse)
async def signup(signup_data: SignupRequest):
    """
    User registration endpoint.
    
    Creates new user account and returns JWT token for immediate authentication.
    
    Args:
        signup_data: SignupRequest with email, name, password, farm details
    
    Returns:
        TokenResponse with JWT access token and user info
    """
    try:
        logger.info(f"Signup request for: {signup_data.email}")
        token_response = await signup_user(signup_data)
        return token_response
    except ValueError as e:
        logger.warning(f"Signup validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup failed. Please try again."
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    User login endpoint.
    
    Authenticates user with email and password, returns JWT token.
    
    Args:
        login_data: LoginRequest with email and password
    
    Returns:
        TokenResponse with JWT access token and user info
    """
    try:
        logger.info(f"Login request for: {login_data.email}")
        token_response = await login_user(login_data)
        return token_response
    except ValueError as e:
        logger.warning(f"Login validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.get("/auth/profile", response_model=UserResponseSchema)
async def get_profile(authorization: str = Header(None)):
    """
    Get authenticated user's profile.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        authorization: Authorization header with Bearer token
    
    Returns:
        UserResponseSchema with user profile details
    """
    try:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        # Extract and verify token
        token = extract_token_from_header(authorization)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("user_id")
        user_profile = await get_user_profile_full(user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile"
        )


# ===== CHAT ENDPOINTS =====

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatInput, background_tasks: BackgroundTasks):
    """
    Main chat endpoint: processes user input through the AI graph.
    Supports text messages, image analysis, and context-aware responses.
    """
    try:
        # 1. Get or create user profile
        user_profile = await get_user_profile(payload.user_id)
        if not user_profile:
            raise HTTPException(status_code=500, detail="Failed to create user profile")
        
        # 2. Initialize state for LangGraph
        initial_state = {
            "user_id": payload.user_id,
            "message": payload.text_message,
            "image": payload.crop_image,
            "intent": "",
            "response": "",
            "context_data": {},
            "planner_data": [],
            "disease_data": {},
            "confidence": 0.0
        }
        
        # 3. Run AI Graph
        logger.info(f"Processing chat for user {payload.user_id}: {payload.text_message[:50]}...")
        final_state = await farmora_ai.ainvoke(initial_state, user_profile)
        
        # 4. Save history in background
        background_tasks.add_task(
            save_chat_history,
            payload.user_id,
            payload.text_message,
            final_state["response"],
            final_state["intent"],
            {"image": bool(payload.crop_image), "confidence": final_state.get("confidence", 0)}
        )
        
        # 5. Build response with proper schema
        disease_result = None
        dashboard_data = None
        
        if final_state.get("disease_data"):
            disease_data = final_state["disease_data"]
            disease_result = DiseaseDetectionResult(
                label=disease_data.get("label", "Unknown"),
                confidence=disease_data.get("confidence", 0),
                remedy=disease_data.get("remedy", ""),
                prevention_tips=disease_data.get("prevention_tips", []),
                severity=disease_data.get("severity", "low"),
                requires_intervention=disease_data.get("requires_intervention", False)
            )
        
        if final_state.get("context_data") and "dashboard" in final_state.get("intent", "").lower():
            context = final_state["context_data"]
            market_news_list = [
                MarketNews(
                    title=news.get("title", ""),
                    description=news.get("description"),
                    source=news.get("source", ""),
                    url=news.get("url", ""),
                    published_at=news.get("published_at", "")
                )
                for news in context.get("market_news", [])
            ]
            dashboard_data = DashboardData(
                weather=context.get("weather"),
                market_news=market_news_list
            )
        
        # Format planner suggestions
        planner_suggestions = []
        for task in final_state.get("planner_data", []):
            planner_suggestions.append({
                "task_name": task.get("task_name", ""),
                "date": task.get("date", ""),
                "reason": task.get("reason", ""),
                "priority": task.get("priority", "medium"),
                "requires_confirmation": task.get("requires_confirmation", True),
                "status": task.get("status", "pending")
            })
        
        return ChatResponse(
            ai_response=final_state["response"],
            intent=final_state["intent"],
            planner_suggestions=planner_suggestions if planner_suggestions else None,
            disease_result=disease_result,
            dashboard_data=dashboard_data,
            confidence_score=final_state.get("confidence", 0.7)
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ===== TASK CONFIRMATION ENDPOINTS =====

@router.post("/tasks/confirm")
async def confirm_task(payload: ConfirmTaskRequest = Body(...)):
    """
    Farmer confirmation endpoint for suggested tasks.
    
    After planner suggests tasks, farmer must confirm acceptance.
    Once confirmed, task is saved to schedule.
    """
    try:
        from farmora_backend.app.services.planner_service import validate_and_confirm_task
        
        success = await validate_and_confirm_task(payload.task_id, payload.user_id, payload.confirmation)
        
        if success:
            status = "accepted" if payload.confirmation else "rejected"
            message = f"✅ Task {status}. " if payload.confirmation else f"❌ Task {status}. "
            
            if payload.confirmation:
                message += "Task added to your schedule. Track progress by marking complete when done."
                logger.info(f"Task {payload.task_id} confirmed for user {payload.user_id}")
            else:
                message += "Task removed from suggestions."
                logger.info(f"Task {payload.task_id} rejected by user {payload.user_id}")
            
            return {
                "success": True,
                "status": status,
                "message": message,
                "next_action": "View tasks" if payload.confirmation else "Get new suggestions"
            }
        else:
            # Task not found or already in the target status
            raise HTTPException(
                status_code=404, 
                detail=f"Task {payload.task_id} not found or already processed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to confirm task: {str(e)}")


@router.post("/tasks/{task_id}/complete")
async def mark_task_complete(task_id: str, payload: TaskCompleteRequest = Body(...)):
    """
    Mark task as completed.
    Triggers Gemini to generate encouraging message and next steps.
    """
    try:
        from farmora_backend.app.services.planner_service import update_task_status, get_user_tasks
        import google.generativeai as genai
        
        # Mark task as completed
        success = await update_task_status(task_id, "completed")
        
        if success:
            # Generate encouraging message using Gemini
            completion_prompt = f"""User just completed a farm task. Generate a short, encouraging message:
- Task ID: {task_id}
- User: {payload.user_id}

Message should:
1. Congratulate the farmer (use farm-appropriate enthusiasm)
2. Explain the impact of this action
3. Suggest next steps if relevant
4. Keep it to 2-3 sentences

Use appropriate emojis."""
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            response = model.generate_content(
                f"You are an encouraging agricultural assistant. Celebrate farmer achievements warmly and briefly.\n\n{completion_prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=300,
                )
            )
            
            encouragement = response.text
            logger.info(f"Task {task_id} marked complete by user {payload.user_id}")
            
            return {
                "success": True,
                "status": "completed",
                "message": encouragement,
                "next_action": "View upcoming tasks"
            }
        else:
            raise HTTPException(status_code=404, detail="Task not found")
        
    except Exception as e:
        logger.error(f"Error marking task complete: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to mark task complete: {str(e)}")


@router.get("/tasks/{user_id}")
async def get_user_tasks(user_id: str, status: str = None):
    """
    Retrieve all tasks for a user.
    Can filter by status: pending, confirmed, completed, rejected.
    
    Args:
        user_id: User ID
        status: Optional status filter
    
    Returns:
        List of tasks with their details and progress
    """
    try:
        from farmora_backend.app.services.planner_service import get_user_tasks
        
        tasks = await get_user_tasks(user_id, status=status)

        # Normalize tasks for JSON response: remove Mongo internal _id and serialize datetimes
        normalized = []
        from datetime import datetime
        for t in tasks:
            out = {}
            for k, v in t.items():
                if k == "_id":
                    continue
                if isinstance(v, datetime):
                    out[k] = v.isoformat()
                else:
                    out[k] = v
            normalized.append(out)

        return {
            "user_id": user_id,
            "status_filter": status or "all",
            "total_tasks": len(normalized),
            "tasks": normalized
        }
        
    except Exception as e:
        logger.exception(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")


@router.get("/timeline/{user_id}")
async def get_timeline(user_id: str):
    """
    Timeline endpoint: returns confirmed tasks formatted for timeline UI.
    """
    try:
        from farmora_backend.app.services.planner_service import get_user_tasks

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

        return {"user_id": user_id, "timeline": timeline_items}

    except Exception as e:
        logger.error(f"Error fetching timeline for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch timeline data")


@router.get("/market/{user_id}")
async def get_market_data(user_id: str):
    """
    Market data endpoint: returns latest market news and price insights.
    Fetches AI-processed market news and farming-relevant information.
    """
    try:
        # Get user profile for context
        user_profile = await get_user_profile(user_id)
        
        # Get dashboard context which includes market news
        dashboard_context = await get_dashboard_context(user_id, user_profile)
        
        market_news = dashboard_context.get("market_news", [])
        
        # Format market data for frontend
        market_items = []
        for news in market_news:
            market_items.append({
                "id": news.get("url", "")[:50],  # Use URL as simple ID
                "title": news.get("title", "Market Update"),
                "description": news.get("description", ""),
                "summary": news.get("summary", ""),
                "source": news.get("source", ""),
                "url": news.get("url", ""),
                "published_at": news.get("published_at", ""),
                "type": "news"
            })
        
        return {
            "user_id": user_id,
            "market_data": market_items,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching market data for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Verify MongoDB connection
        await db.db.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}



# ===== VOICE TRANSCRIPTION ENDPOINT =====

@router.post("/voice/transcribe")
async def transcribe_voice(
    audio: bytes = Body(..., media_type="audio/*"),
    authorization: str = Header(None)
):
    """
    Transcribe voice input to text using GROQ Whisper.
    
    Accepts audio file and returns transcribed text.
    """
    try:
        from groq import Groq
        import tempfile
        import os
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp:
            tmp.write(audio)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(tmp_path, file.read()),
                    model="whisper-large-v3-turbo",
                    temperature=0,
                    response_format="verbose_json",
                )
            
            return {
                "success": True,
                "text": transcription.text,
                "language": getattr(transcription, 'language', 'unknown')
            }
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Voice transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/voice/transcribe-file")
async def transcribe_voice_file(
    file: bytes = Body(...),
    filename: str = Body("audio.m4a"),
    authorization: str = Header(None)
):
    """
    Transcribe voice input from base64 encoded audio.
    """
    try:
        from groq import Groq
        import tempfile
        import os
        import base64
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Decode base64 if needed
        try:
            audio_data = base64.b64decode(file) if isinstance(file, str) else file
        except:
            audio_data = file
        
        # Get file extension
        ext = filename.split('.')[-1] if '.' in filename else 'm4a'
        
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    file=(filename, f.read()),
                    model="whisper-large-v3-turbo",
                    temperature=0,
                    response_format="verbose_json",
                )
            
            return {
                "success": True,
                "text": transcription.text,
                "language": getattr(transcription, 'language', 'unknown')
            }
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Voice transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# ===== USER PROFILE UPDATE ENDPOINT =====

@router.put("/auth/profile")
async def update_profile(
    authorization: str = Header(None),
    language: str = Body(None),
    latitude: float = Body(None),
    longitude: float = Body(None),
    farm_location: str = Body(None),
):
    """
    Update user profile settings including language and location.
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        token = extract_token_from_header(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("user_id")
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        if language is not None:
            update_doc["language"] = language
        if latitude is not None:
            update_doc["latitude"] = latitude
        if longitude is not None:
            update_doc["longitude"] = longitude
        if farm_location is not None:
            update_doc["farm_location"] = farm_location
        
        result = await db.db.users.update_one(
            {"user_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count > 0:
            logger.info(f"Profile updated for user {user_id}")
            return {"success": True, "message": "Profile updated successfully"}
        else:
            return {"success": True, "message": "No changes made"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
