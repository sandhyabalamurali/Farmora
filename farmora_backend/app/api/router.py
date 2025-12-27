"""
API router configuration for Farmora backend.
Includes all routes: authentication, chat, tasks, health checks.
"""

from fastapi import APIRouter
from farmora_backend.app.api.controller import router as controller_router

# Create main API router
api_router = APIRouter(prefix="/api", tags=["farmora"])

# Include all controller routes
api_router.include_router(controller_router)

# Routes organized by prefix:
# POST /api/auth/signup - User registration
# POST /api/auth/login - User login
# GET /api/auth/profile - Get user profile (requires JWT)
# POST /api/chat - Main chat endpoint for intent classification & responses
# POST /api/tasks/confirm - Confirm suggested task
# POST /api/tasks/{task_id}/complete - Mark task as completed
# GET /api/tasks/{user_id} - Get all user tasks (with optional status filter)
# GET /api/health - Health check
