import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from farmora_backend.app.api.controller import router as chat_router
from farmora_backend.app.api.router import api_router
from farmora_backend.app.core.database import db
from farmora_backend.app.core.security import verify_token, extract_token_from_header
from farmora_backend.app.services.dashboard_service import fetch_and_cache_market_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Background Task Loop ---
async def periodic_data_fetch_loop():
    """Runs the data fetcher every 30 minutes."""
    while True:
        try:
            await fetch_and_cache_market_data()
        except Exception as e:
            logger.error(f"Error in periodic data fetch: {e}")
        await asyncio.sleep(1800)  # Sleep for 30 minutes


# --- JWT Middleware ---
async def jwt_middleware(request: Request, call_next):
    """
    Verify JWT token for protected endpoints.
    Protected routes: /api/chat, /api/tasks/*, /api/auth/profile
    Public routes: /api/auth/signup, /api/auth/login, /api/health, /
    """
    protected_paths = [
        "/api/chat",
        "/api/tasks",
        "/api/auth/profile"
    ]
    
    # Check if route is protected
    is_protected = any(request.url.path.startswith(path) for path in protected_paths)
    
    if is_protected:
        # Allow CORS preflight requests to pass without auth
        if request.method == "OPTIONS":
            return await call_next(request)
        # Get authorization header
        auth_header = request.headers.get("authorization")
        
        if not auth_header:
            logger.warning(f"Missing authorization header for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"}
            )
        
        # Extract and verify token
        token = extract_token_from_header(auth_header)
        if not token:
            logger.warning(f"Invalid authorization header format for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"}
            )
        
        payload = verify_token(token)
        if not payload:
            logger.warning(f"Invalid or expired token for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"}
            )
        
        # Add user_id to request state for use in endpoints
        request.state.user_id = payload.get("user_id")
        request.state.email = payload.get("email")
    
    response = await call_next(request)
    return response


# --- Lifespan (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Connect to DB
    try:
        await db.connect_db()
        logger.info("✅ Database connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise
    
    # 2. Startup: Trigger periodic data fetch in background
    task = asyncio.create_task(periodic_data_fetch_loop())
    logger.info("✅ Background data fetch task started")
    
    yield
    
    # 3. Shutdown: Cleanup
    task.cancel()
    try:
        await db.close_db()
        logger.info("✅ Database connection closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")


# --- App Definition ---
app = FastAPI(
    title="Farmora AI Backend",
    description="AI-powered agricultural assistant for Indian farmers",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT middleware
app.middleware("http")(jwt_middleware)

# Register routers
app.include_router(api_router)  # Includes all routes with /api prefix


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "message": "Farmora AI Backend is running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "auth": {
                "signup": "POST /api/auth/signup",
                "login": "POST /api/auth/login",
                "profile": "GET /api/auth/profile (requires JWT)"
            },
            "chat": {
                "message": "POST /api/chat (requires JWT)",
                "health": "GET /api/health"
            },
            "tasks": {
                "confirm": "POST /api/tasks/confirm (requires JWT)",
                "complete": "POST /api/tasks/{task_id}/complete (requires JWT)",
                "list": "GET /api/tasks/{user_id} (requires JWT)"
            }
        }
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "farmora_backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
