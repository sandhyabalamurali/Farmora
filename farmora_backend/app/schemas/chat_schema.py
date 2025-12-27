from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# ===== AUTHENTICATION SCHEMAS =====

class SignupRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    farm_location: Optional[str] = None
    crops: Optional[List[str]] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str
    expires_in: int = 86400  # 24 hours in seconds


class UserResponseSchema(BaseModel):
    """Schema for user profile response."""
    user_id: str
    email: str
    name: str
    farm_location: Optional[str] = None
    crops: List[str] = []
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ===== INPUT SCHEMAS =====

class ChatInput(BaseModel):
    user_id: str
    text_message: str
    crop_image: Optional[str] = None  # Base64 encoded image
    caption: Optional[str] = None

# ===== PLANNER SCHEMAS =====

class PlannerSuggestion(BaseModel):
    task_id: Optional[str] = None
    task_name: str
    date: str
    reason: str
    priority: str = Field(default="medium")
    requires_confirmation: bool = True
    status: str = Field(default="pending")

class PlannedTask(BaseModel):
    task_id: str
    user_id: str
    task_name: str
    description: Optional[str] = None
    scheduled_date: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

# ===== DISEASE DETECTION SCHEMAS =====

class DiseaseDetectionResult(BaseModel):
    label: str
    confidence: float  # 0-100
    remedy: str
    prevention_tips: List[str]
    severity: str  # low, medium, high
    requires_intervention: bool

# ===== DASHBOARD SCHEMAS =====

class MarketNews(BaseModel):
    title: str
    description: Optional[str] = None
    source: str
    url: str
    published_at: str

class DashboardData(BaseModel):
    weather: Optional[str] = None
    market_news: List[MarketNews] = []

# ===== OUTPUT SCHEMAS =====

class ChatResponse(BaseModel):
    ai_response: str
    intent: str
    planner_suggestions: Optional[List[PlannerSuggestion]] = None
    disease_result: Optional[DiseaseDetectionResult] = None
    dashboard_data: Optional[DashboardData] = None
    confidence_score: float = Field(default=0.8)

# ===== CHAT HISTORY SCHEMA =====

class ChatHistoryEntry(BaseModel):
    chat_id: str
    user_id: str
    user_message: str
    ai_response: str
    intent: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime

class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    farm_location: Optional[str] = None
    crops: List[str] = []
    preferences: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime