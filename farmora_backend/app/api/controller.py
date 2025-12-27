import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Header, Body, UploadFile, File, Request
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
                "task_id": task.get("task_id"),  # Ensure task_id is included
                "task_name": task.get("task_name", ""),
                "date": task.get("date", ""),
                "reason": task.get("reason", ""),
                "priority": task.get("priority", "medium"),
                "description": task.get("description", ""),
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
        import google.genai as genai
        
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
            
            import google.genai as genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=f"You are an encouraging agricultural assistant. Celebrate farmer achievements warmly and briefly.\n\n{completion_prompt}",
                config=genai.types.GenerateContentConfig(
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
    Uses cached timeline from DB for better performance.
    """
    try:
        from farmora_backend.app.services.planner_service import get_cached_timeline

        timeline_data = await get_cached_timeline(user_id)
        
        return {
            "user_id": user_id, 
            "timeline": timeline_data.get("timeline", []),
            "last_updated": timeline_data.get("last_updated")
        }

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
        
        # Get dashboard context which includes market news and weather
        dashboard_context = await get_dashboard_context(user_id, user_profile)
        
        market_news = dashboard_context.get("market_news", [])
        weather_data = dashboard_context.get("weather", {})
        
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
                "image_url": news.get("image_url", ""),
                "type": "news"
            })
        
        # Format weather insights
        weather_insights = "Weather data unavailable"
        if weather_data and not weather_data.get("error"):
            temp = weather_data.get("temperature", "N/A")
            desc = weather_data.get("description", "N/A")
            ai_insights = weather_data.get("ai_insights", "")
            weather_insights = f"🌡️ {temp}°C, {desc}. {ai_insights}" if ai_insights else f"🌡️ {temp}°C, {desc}"
        
        return {
            "user_id": user_id,
            "market_data": market_items,
            "weather": weather_insights,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching market data for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@router.get("/weather/{user_id}")
async def get_weather_data(user_id: str, language: str = "en"):
    """
    Weather data endpoint: returns weather insights translated to user's language.
    """
    try:
        from farmora_backend.app.services.dashboard_service import generate_weather_insights
        
        # Get user profile for location and context
        user_profile = await get_user_profile(user_id)
        
        # Generate weather insights
        weather_data = await generate_weather_insights(user_profile, language)
        
        # Format response
        weather_insights = "Weather data unavailable"
        weather_structured = None
        
        if weather_data and not weather_data.get("error"):
            temp = weather_data.get("temperature", "N/A")
            desc = weather_data.get("description", "N/A")
            ai_insights = weather_data.get("ai_insights", "")
            weather_insights = f"🌡️ {temp}°C, {desc}.\n\n{ai_insights}" if ai_insights else f"🌡️ {temp}°C, {desc}"
            
            weather_structured = {
                "temperature": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity"),
                "wind_speed": f"{weather_data.get('wind_speed', 0)} m/s",
                "visibility": f"{weather_data.get('visibility', 10000) / 1000:.1f} km",
                "description": desc
            }
        
        return {
            "user_id": user_id,
            "weather": weather_insights,
            "weather_structured": weather_structured,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching weather for {user_id}: {e}", exc_info=True)
        return {
            "user_id": user_id,
            "weather": "Weather data unavailable. Please check your location settings.",
            "weather_structured": None,
            "last_updated": datetime.utcnow().isoformat()
        }


@router.get("/news/{user_id}")
async def get_news_data(user_id: str, language: str = "en", refresh: bool = False):
    """
    News data endpoint: returns market news translated to user's language.
    If refresh=True, fetches fresh data from the news API.
    """
    try:
        from farmora_backend.app.services.dashboard_service import get_translated_news, fetch_and_process_market_data
        
        # If refresh requested, fetch fresh data from API
        if refresh:
            logger.info(f"🔄 Refreshing news data for user {user_id}")
            await fetch_and_process_market_data()
        
        # Get user profile
        user_profile = await get_user_profile(user_id)
        
        # Get news with translation
        market_news = await get_translated_news(language)
        
        # Format market data for frontend
        market_items = []
        for news in market_news:
            market_items.append({
                "id": news.get("url", "")[:50],
                "title": news.get("title", "Market Update"),
                "description": news.get("description", ""),
                "summary": news.get("summary", ""),
                "source": news.get("source", ""),
                "url": news.get("url", ""),
                "published_at": news.get("published_at", ""),
                "image_url": news.get("image_url", ""),
                "type": "news"
            })
        
        return {
            "user_id": user_id,
            "market_data": market_items,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching news for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch news data")


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

        # Try to get user language for optional post-translation
        user_lang = None
        try:
            if authorization:
                token = extract_token_from_header(authorization)
                if token:
                    payload = verify_token(token)
                    if payload:
                        user_profile = await get_user_profile(payload.get("user_id"))
                        user_lang = user_profile.get("language") if user_profile else None

            try:
                # send as (filename, bytes) tuple which matches Groq example
                with open(tmp_path, "rb") as file_obj:
                    file_bytes = file_obj.read()
                transcription = client.audio.transcriptions.create(
                    file=("audio.m4a", file_bytes),
                    model=settings.WHISPER_MODEL,
                    temperature=0,
                    response_format="verbose_json",
                )

                text = getattr(transcription, "text", None) or transcription.get("text") if isinstance(transcription, dict) else None
                detected_lang = getattr(transcription, 'language', None) or (transcription.get('language') if isinstance(transcription, dict) else None)

                # If user language is set and differs from detected language, translate using Gemini
                if user_lang and detected_lang and user_lang.lower() != detected_lang.lower() and text:
                    try:
                        import google.genai as genai
                        client = genai.Client(api_key=settings.GEMINI_API_KEY)
                        prompt = f"Translate the following text to {user_lang} preserving meaning and tone. Return only the translated text.\n\nText:\n{text}"
                        resp = client.models.generate_content(
                            model=settings.GEMINI_MODEL,
                            contents=prompt,
                            config=genai.types.GenerateContentConfig(
                                temperature=0.2,
                                max_output_tokens=1000,
                            )
                        )
                        translated = resp.text
                        logger.info(f"Voice transcription translated to {user_lang}")
                        text = translated
                    except Exception as te:
                        logger.error(f"Translation failed: {te}", exc_info=True)

                return {
                    "success": True,
                    "text": text,
                    "language": detected_lang or getattr(transcription, 'language', 'unknown')
                }
            finally:
                os.unlink(tmp_path)
        except Exception:
            # Ensure temp file is removed on any failure
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass
            raise
            
    except Exception as e:
        logger.error(f"Voice transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/voice/transcribe-file")
async def transcribe_voice_file(
    request: Request,
    authorization: str = Header(None)
):
    """
    Transcribe voice input from base64 encoded audio in JSON body.
    Frontend sends: {"file": "<base64>", "filename": "audio.webm"}
    """
    try:
        from groq import Groq
        import tempfile
        import os
        import base64
        
        client = Groq(api_key=settings.GROQ_API_KEY)

        # Parse JSON body
        body = None
        try:
            body = await request.json()
            base64_audio = body.get("file")
            filename = body.get("filename", "audio.webm")
            
            if not base64_audio:
                raise HTTPException(status_code=400, detail="No audio data in request body")
            
            # Decode base64 to bytes
            file_bytes = base64.b64decode(base64_audio)
            logger.info(f"Received base64 audio: {filename} ({len(file_bytes)} bytes)")
        except ValueError as e:
            logger.error(f"Invalid base64 data: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail="Invalid base64 encoded audio data")
        except Exception as e:
            logger.error(f"Failed parsing request body: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail="Invalid request body")

        # Save to temp file (optional) — we'll send bytes directly to SDK
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or ".m4a") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        # Try to get user language for optional post-translation
        # First check if language is provided in request body, then fall back to profile
        user_lang = body.get("language") if body else None
        
        if not user_lang and authorization:
            try:
                token = extract_token_from_header(authorization)
                if token:
                    payload = verify_token(token)
                    if payload:
                        user_profile = await get_user_profile(payload.get("user_id"))
                        user_lang = user_profile.get("language") if user_profile else None
            except Exception as e:
                logger.debug(f"Could not get language from profile: {e}")

        try:
            transcription = client.audio.transcriptions.create(
                file=(filename, file_bytes),
                model=settings.WHISPER_MODEL,
                temperature=0,
                response_format="verbose_json",
            )

            text = getattr(transcription, "text", None) or (transcription.get("text") if isinstance(transcription, dict) else None)
            detected_lang = getattr(transcription, 'language', None) or (transcription.get('language') if isinstance(transcription, dict) else None)

            # If user language is set and differs from detected language, translate using Gemini
            if user_lang and detected_lang and user_lang.lower() != detected_lang.lower() and text:
                try:
                    import google.genai as genai
                    client_genai = genai.Client(api_key=settings.GEMINI_API_KEY)
                    prompt = f"Translate the following text to {user_lang} preserving meaning and tone. Return only the translated text.\n\nText:\n{text}"
                    resp = client_genai.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=prompt,
                        config=genai.types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=1000,
                        )
                    )
                    translated = resp.text
                    logger.info(f"Voice transcription translated to {user_lang}")
                    text = translated
                except Exception as te:
                    logger.error(f"Translation failed: {te}", exc_info=True)

            return {
                "success": True,
                "text": text,
                "language": detected_lang or getattr(transcription, 'language', 'unknown')
            }
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            
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
