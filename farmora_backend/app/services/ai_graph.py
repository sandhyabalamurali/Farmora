import logging
import json
from typing import TypedDict, List, Dict, Optional, Any
from langgraph.graph import StateGraph, END
from farmora_backend.app.config import settings
from farmora_backend.app.services.disease_service import analyze_disease
from farmora_backend.app.services.dashboard_service import get_dashboard_context
from farmora_backend.app.services.planner_service import generate_planner_suggestions
from farmora_backend.app.services.chat_service import get_context_from_history
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# Store user profile in state
_user_profile = None
_user_language = "en"  # Default language


# --- State Definition ---
class FarmoraState(TypedDict):
    user_id: str
    message: str
    image: Optional[str]
    intent: str
    response: str
    context_data: Dict[Any, Any]
    planner_data: List[Dict]
    disease_data: Dict[str, Any]
    confidence: float


def call_gemini(prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 1000) -> str:
    """Helper function to call Gemini API."""
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    
    response = gemini_model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    )
    return response.text


# --- NODES ---

async def detect_intent_node(state: FarmoraState) -> FarmoraState:
    """
    Use Gemini to classify user intent with high precision.
    """
    try:
        # If image provided, likely disease detection
        if state.get("image"):
            state["intent"] = "disease_detection"
            return state

        # Use Gemini for intelligent intent detection
        system_prompt = """You are an intent classification expert for agricultural AI.
        Analyze the user message and classify into ONE category with absolute certainty.
        
        Categories:
        - 'disease_detection': User asking about crop disease, symptoms, pest issues, or asking to analyze an image
        - 'planner_create': User asking to schedule tasks, create farming timeline, plan activities
        - 'dashboard_query': User asking for weather, market prices, news, government announcements, reports
        - 'general_chat': General advice, Q&A, conversation, tips, learning
        
        Respond with ONLY the category name in lowercase, nothing else."""
        
        intent = call_gemini(state["message"], system_prompt, temperature=0.1, max_tokens=20)
        intent = intent.strip().lower().replace("'", "").replace('"', "")
        
        # Validate intent
        valid_intents = ["disease_detection", "planner_create", "dashboard_query", "general_chat"]
        state["intent"] = intent if intent in valid_intents else "general_chat"
        
    except Exception as e:
        logger.error(f"Error in intent detection: {e}")
        state["intent"] = "general_chat"
    
    return state


async def disease_detection_node(state: FarmoraState) -> FarmoraState:
    """Analyze crop disease using Gemini intelligence."""
    try:
        result = await analyze_disease(state["image"], state["message"], _user_profile)
        state["disease_data"] = result
        
        # Get user's preferred language
        language = _user_profile.get("language", "en") if _user_profile else "en"
        
        # Format response using Gemini
        format_prompt = f"""Format this disease analysis into a helpful farmer-friendly response:

Disease: {result.get('label', 'Unknown')}
Confidence: {result.get('confidence', 0):.0f}%
Severity: {result.get('severity', 'unknown')}
Remedy: {result.get('remedy', 'N/A')}
Prevention Tips: {', '.join(result.get('prevention_tips', []))}
Immediate Action: {result.get('immediate_action', 'Monitor crop')}
Follow-up: {result.get('follow_up', 'Review in 1 week')}

Create a clear, emoji-enriched response for the farmer. 
IMPORTANT: Generate the response directly in {language} language."""

        system_prompt = f"Format agricultural analysis into clear, actionable farmer advice. Use emojis appropriately. Respond in {language} language."
        
        state["response"] = call_gemini(format_prompt, system_prompt, temperature=0.6, max_tokens=800)
        state["confidence"] = result.get('confidence', 0) / 100.0
        
    except Exception as e:
        logger.error(f"Error in disease detection: {e}")
        state["response"] = f"❌ Error analyzing disease: {str(e)}. Please try again or consult a local agricultural expert."
        state["disease_data"] = {}
        state["confidence"] = 0.0
    
    return state


async def planner_node(state: FarmoraState) -> FarmoraState:
    """Generate intelligent farm planning suggestions using Gemini."""
    try:
        suggestions = await generate_planner_suggestions(
            state["user_id"],
            state["message"],
            _user_profile
        )
        state["planner_data"] = suggestions
        
        # Get user's preferred language
        language = _user_profile.get("language", "en") if _user_profile else "en"
        
        # Format using Gemini
        format_prompt = f"""Format these farm task suggestions into an engaging response for a farmer:

Tasks: {json.dumps(suggestions, indent=2)}

Create a response that:
1. Lists each task with clear dates and priorities
2. Explains why each task matters right now
3. Provides encouragement
4. Asks for confirmation to add tasks

Use emojis and farm-friendly language.
IMPORTANT: Generate the response directly in {language} language."""

        system_prompt = f"Format farm planning tasks into engaging, action-oriented advice for farmers. Respond in {language} language."
        
        state["response"] = call_gemini(format_prompt, system_prompt, temperature=0.7, max_tokens=1000)
        state["confidence"] = 0.85
        
    except Exception as e:
        logger.error(f"Error in planner node: {e}")
        state["response"] = f"❌ Unable to generate planner suggestions: {str(e)}"
        state["planner_data"] = []
        state["confidence"] = 0.0
    
    return state


async def dashboard_node(state: FarmoraState) -> FarmoraState:
    """Fetch dashboard data and format using Gemini."""
    try:
        data = await get_dashboard_context(state["user_id"], _user_profile)
        state["context_data"] = data
        
        # Get user's preferred language
        language = _user_profile.get("language", "en") if _user_profile else "en"
        
        # Format weather data
        weather_info = data.get('weather', {})
        if isinstance(weather_info, dict) and not weather_info.get('error'):
            weather_text = f"""
Temperature: {weather_info.get('temperature', 'N/A')}°C (feels like {weather_info.get('feels_like', 'N/A')}°C)
Humidity: {weather_info.get('humidity', 'N/A')}%
Conditions: {weather_info.get('description', 'N/A')}
Wind: {weather_info.get('wind_speed', 'N/A')} m/s
Location: {weather_info.get('city', 'Unknown')}
Alerts: {', '.join(weather_info.get('alerts', [])) or 'None'}
AI Insights: {weather_info.get('ai_insights', 'N/A')}
"""
        else:
            weather_text = f"Weather data unavailable: {weather_info.get('error', 'Unknown error')}"
        
        # Format dashboard data using Gemini
        format_prompt = f"""Format this farm dashboard data into a helpful summary:

Weather Information:
{weather_text}

Market News (Top 3):
{json.dumps(data.get('market_news', [])[:3], indent=2)}

Create a conversational response that:
1. Summarizes today's weather and what it means for farming
2. Highlights any weather alerts
3. Mentions 2-3 relevant market updates
4. Suggests one action based on weather/market

Use emojis appropriately.
IMPORTANT: Generate the response directly in {language} language."""

        system_prompt = f"Format farm dashboard data into actionable insights for farmers. Be conversational. Respond in {language} language."
        
        state["response"] = call_gemini(format_prompt, system_prompt, temperature=0.7, max_tokens=1000)
        state["confidence"] = 0.75
        
    except Exception as e:
        logger.error(f"Error in dashboard node: {e}")
        state["response"] = f"❌ Unable to fetch dashboard data: {str(e)}"
        state["context_data"] = {}
        state["confidence"] = 0.0
    
    return state


async def general_chat_node(state: FarmoraState) -> FarmoraState:
    """Handle general farming questions using Gemini with full context."""
    try:
        # Get conversation context
        context = await get_context_from_history(state["user_id"], limit=5)
        
        # Get user's preferred language
        language = _user_profile.get("language", "en") if _user_profile else "en"
        
        # Build system prompt with user profile context
        profile_context = ""
        if _user_profile:
            profile_context = f"""User Context:
- Crops: {', '.join(_user_profile.get('crops', [])) or 'Not specified'}
- Location: {_user_profile.get('farm_location', 'Unknown')}
- Experience: Farmer using Farmora AI
"""
        
        system_prompt = f"""You are a highly knowledgeable agricultural expert AI assistant specifically trained for Indian farmers.
{profile_context}

Provide:
- Practical, field-tested advice
- Specific solutions with quantities and timing
- Local/regional best practices
- Government scheme information when relevant
- Cost-effective options
- Sustainable farming promotion

Be conversational, encouraging, and always tailor advice to the user's crops and location.
Respond in a warm, supportive tone. Use relevant emojis to make advice engaging.

IMPORTANT: You MUST respond in {language} language. Generate your response directly in {language}."""
        
        if context:
            prompt = f"Previous conversation context:\n{context}\n\nCurrent question: {state['message']}"
        else:
            prompt = state["message"]
        
        state["response"] = call_gemini(prompt, system_prompt, temperature=0.8, max_tokens=1200)
        state["confidence"] = 0.9
        
    except Exception as e:
        logger.error(f"Error in general chat: {e}")
        state["response"] = f"Sorry, I encountered an error: {str(e)}. Please try again."
        state["confidence"] = 0.0
    
    return state


# --- GRAPH CONSTRUCTION ---

def build_graph():
    """Build the LangGraph state machine."""
    graph = StateGraph(FarmoraState)
    
    # Add nodes
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("disease_detection", disease_detection_node)
    graph.add_node("planner", planner_node)
    graph.add_node("dashboard", dashboard_node)
    graph.add_node("general_chat", general_chat_node)
    
    # Set entry point
    graph.set_entry_point("detect_intent")
    
    # Define routing logic
    def route_based_on_intent(state):
        intent = state.get("intent", "general_chat").lower()
        
        if "disease" in intent:
            return "disease_detection"
        elif "planner" in intent or "plan" in intent:
            return "planner"
        elif "dashboard" in intent or "weather" in intent or "market" in intent:
            return "dashboard"
        else:
            return "general_chat"
    
    # Add conditional edges from intent detection
    graph.add_conditional_edges("detect_intent", route_based_on_intent)
    
    # Add edges to END
    graph.add_edge("disease_detection", END)
    graph.add_edge("planner", END)
    graph.add_edge("dashboard", END)
    graph.add_edge("general_chat", END)
    
    return graph.compile()


# Initialize the graph
farmora_ai = build_graph()


# Preserve original ainvoke implementation
_original_ainvoke = getattr(farmora_ai, "ainvoke")


async def ainvoke_with_profile(state: FarmoraState, user_profile: Optional[Dict] = None):
    """Invoke the graph with user profile context."""
    global _user_profile
    _user_profile = user_profile
    return await _original_ainvoke(state)


# Replace the graph's ainvoke with the profile-aware wrapper
farmora_ai.ainvoke = ainvoke_with_profile
