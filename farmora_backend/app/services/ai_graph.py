import logging
import json
from typing import TypedDict, List, Dict, Optional, Any
from langgraph.graph import StateGraph, END
from groq import Groq
from farmora_backend.app.config import settings
from farmora_backend.app.services.disease_service import analyze_disease
from farmora_backend.app.services.dashboard_service import get_dashboard_context
from farmora_backend.app.services.planner_service import generate_planner_suggestions
from farmora_backend.app.services.chat_service import get_context_from_history

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.GROQ_API_KEY)

# Store user profile in state
_user_profile = None


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


# --- NODES ---

async def detect_intent_node(state: FarmoraState) -> FarmoraState:
    """
    Use LLM to classify user intent with high precision.
    """
    try:
        # If image provided, likely disease detection
        if state.get("image"):
            state["intent"] = "disease_detection"
            return state

        # Use LLM for intelligent intent detection
        system_prompt = """You are an intent classification expert for agricultural AI.
        Analyze the user message and classify into ONE category with absolute certainty.
        
        Categories:
        - 'disease_detection': User asking about crop disease, symptoms, pest issues, or asking to analyze an image
        - 'planner_create': User asking to schedule tasks, create farming timeline, plan activities
        - 'dashboard_query': User asking for weather, market prices, news, government announcements, reports
        - 'general_chat': General advice, Q&A, conversation, tips, learning
        
        Respond with ONLY the category name in lowercase, nothing else."""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state["message"]}
            ],
            temperature=0.1,
            max_tokens=20
        )
        
        intent = completion.choices[0].message.content.strip().lower().replace("'", "").replace('"', "")
        
        # Validate intent
        valid_intents = ["disease_detection", "planner_create", "dashboard_query", "general_chat"]
        state["intent"] = intent if intent in valid_intents else "general_chat"
        
    except Exception as e:
        logger.error(f"Error in intent detection: {e}")
        state["intent"] = "general_chat"
    
    return state


async def disease_detection_node(state: FarmoraState) -> FarmoraState:
    """Analyze crop disease using pure LLM intelligence."""
    try:
        result = await analyze_disease(state["image"], state["message"], _user_profile)
        state["disease_data"] = result
        
        # Format response using LLM for better presentation
        format_prompt = f"""Format this disease analysis into a helpful farmer-friendly response:

Disease: {result.get('label', 'Unknown')}
Confidence: {result.get('confidence', 0):.0f}%
Severity: {result.get('severity', 'unknown')}
Remedy: {result.get('remedy', 'N/A')}
Prevention Tips: {', '.join(result.get('prevention_tips', []))}
Immediate Action: {result.get('immediate_action', 'Monitor crop')}
Follow-up: {result.get('follow_up', 'Review in 1 week')}

Create a clear, emoji-enriched response for the farmer."""

        format_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Format agricultural analysis into clear, actionable farmer advice. Use emojis appropriately."
                },
                {
                    "role": "user",
                    "content": format_prompt
                }
            ],
            temperature=0.6,
            max_tokens=800
        )
        
        state["response"] = format_response.choices[0].message.content
        state["confidence"] = result.get('confidence', 0) / 100.0
        
    except Exception as e:
        logger.error(f"Error in disease detection: {e}")
        state["response"] = f"❌ Error analyzing disease: {str(e)}. Please try again or consult a local agricultural expert."
        state["disease_data"] = {}
        state["confidence"] = 0.0
    
    return state


async def planner_node(state: FarmoraState) -> FarmoraState:
    """Generate intelligent farm planning suggestions using LLM."""
    try:
        suggestions = await generate_planner_suggestions(
            state["user_id"],
            state["message"],
            _user_profile
        )
        state["planner_data"] = suggestions
        
        # Format using LLM for better presentation
        format_prompt = f"""Format these farm task suggestions into an engaging response for a farmer:

Tasks: {json.dumps(suggestions, indent=2)}

Create a response that:
1. Lists each task with clear dates and priorities
2. Explains why each task matters right now
3. Provides encouragement
4. Asks for confirmation to add tasks

Use emojis and farm-friendly language."""

        format_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Format farm planning tasks into engaging, action-oriented advice for farmers."
                },
                {
                    "role": "user",
                    "content": format_prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        state["response"] = format_response.choices[0].message.content
        state["confidence"] = 0.85
        
    except Exception as e:
        logger.error(f"Error in planner node: {e}")
        state["response"] = f"❌ Unable to generate planner suggestions: {str(e)}"
        state["planner_data"] = []
        state["confidence"] = 0.0
    
    return state


async def dashboard_node(state: FarmoraState) -> FarmoraState:
    """Fetch dashboard data and format using LLM."""
    try:
        data = await get_dashboard_context(state["user_id"], _user_profile)
        state["context_data"] = data
        
        # Format dashboard data using LLM
        format_prompt = f"""Format this farm dashboard data into a helpful summary:

Weather Insights: {data.get('weather', 'No data')}

Market News:
{json.dumps(data.get('market_news', [])[:3], indent=2)}

Create a response that:
1. Summarizes today's weather and what it means
2. Highlights 2-3 most relevant market updates
3. Suggests one action based on weather/market
4. Is conversational and encouraging

Use emojis appropriately."""

        format_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Format farm dashboard data into actionable insights for farmers. Be conversational."
                },
                {
                    "role": "user",
                    "content": format_prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        state["response"] = format_response.choices[0].message.content
        state["confidence"] = 0.75
        
    except Exception as e:
        logger.error(f"Error in dashboard node: {e}")
        state["response"] = f"❌ Unable to fetch dashboard data: {str(e)}"
        state["context_data"] = {}
        state["confidence"] = 0.0
    
    return state


async def general_chat_node(state: FarmoraState) -> FarmoraState:
    """Handle general farming questions using LLM with full context."""
    try:
        # Get conversation context
        context = await get_context_from_history(state["user_id"], limit=5)
        
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
Respond in a warm, supportive tone. Use relevant emojis to make advice engaging."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation context
        if context:
            messages.append({
                "role": "user",
                "content": f"Previous conversation context:\n{context}\n\nCurrent question: {state['message']}"
            })
        else:
            messages.append({"role": "user", "content": state["message"]})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8,
            max_tokens=1200
        )
        
        state["response"] = completion.choices[0].message.content
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
    """Invoke the graph with user profile context without causing recursion.

    This wrapper sets a module-level `_user_profile` used by nodes, then
    delegates to the original `ainvoke` implementation saved above.
    """
    global _user_profile
    _user_profile = user_profile
    # Call the preserved original ainvoke to avoid recursion
    return await _original_ainvoke(state)


# Replace the graph's ainvoke with the profile-aware wrapper
farmora_ai.ainvoke = ainvoke_with_profile

