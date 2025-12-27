import logging
import json
from typing import TypedDict, List, Dict, Optional, Any
from langgraph.graph import StateGraph, END
from farmora_backend.app.config import settings
from farmora_backend.app.services.disease_service import analyze_disease
from farmora_backend.app.services.dashboard_service import get_dashboard_context
from farmora_backend.app.services.planner_service import generate_planner_suggestions
from farmora_backend.app.services.chat_service import get_context_from_history
import google.genai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)


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
    user_profile: Optional[Dict[str, Any]]  # User-specific profile data


def call_gemini(prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 1000) -> str:
    """Helper function to call Gemini API."""
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    
    response = gemini_client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=full_prompt,
        config=genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    )
    return response.text if response.text else ""


# --- NODES ---

async def detect_intent_node(state: FarmoraState) -> FarmoraState:
    """
    Use Gemini to classify user intent with high precision and context awareness.
    Enhanced disease detection with comprehensive keyword matching.
    """
    try:
        # If image provided, definitely disease detection
        if state.get("image"):
            state["intent"] = "disease_detection"
            logger.info(f"Intent: disease_detection (image provided)")
            return state

        message_lower = state["message"].lower()
        
        # Enhanced keyword-based classification for accuracy
        weather_keywords = [
            'weather', 'temperature', 'rain', 'climate', 'forecast', 'humid', 
            'wind', 'sunny', 'cloudy', 'monsoon', 'season', 'barish', 'mausam'
        ]
        market_keywords = [
            'market', 'price', 'news', 'mandi', 'sell', 'buy', 'crop price', 
            'commodity', 'rate', 'cost', 'daam', 'bazaar', 'bazar'
        ]
        planner_keywords = [
            'schedule', 'plan', 'task', 'remind', 'calendar', 'timeline', 
            'when to', 'create task', 'add task', 'set reminder', 'kab', 
            'planning', 'shedule', 'todo', 'to do', 'to-do'
        ]
        
        # ENHANCED: Comprehensive disease keywords for better detection
        disease_keywords = [
            # English disease/pest terms
            'disease', 'pest', 'infection', 'leaf', 'spot', 'rot', 'fungus', 
            'insect', 'damage', 'yellow', 'wilting', 'blight', 'mold', 'mildew',
            'rust', 'wilt', 'brown', 'black', 'white', 'lesion', 'hole', 'curl',
            'dying', 'dead', 'sick', 'unhealthy', 'problem', 'issue', 'wrong',
            # Symptoms
            'spots', 'patches', 'discolor', 'drooping', 'drying', 'burnt',
            'stunted', 'withering', 'falling', 'dropping', 'shriveling',
            # Crop health terms
            'crop health', 'plant health', 'leaves turning', 'stem', 'root',
            'fruit', 'flower', 'grain', 'pod', 'affected', 'infected', 'attacked',
            # Hindi/regional terms
            'rog', 'bimari', 'keera', 'keet', 'pila', 'safed', 'kala', 
            'sukha', 'murjhana', 'girna', 'pattiyan', 'patti', 'daag',
            # Specific diseases
            'blast', 'borer', 'aphid', 'whitefly', 'caterpillar', 'mite',
            'bacterial', 'viral', 'fungal', 'nematode', 'larvae',
            # Common crop problems
            'yellowing', 'browning', 'blackening', 'spotting', 'curling',
            'wilted', 'rotten', 'moldy', 'infested', 'eaten', 'chewed',
            # Question patterns about disease
            'what is wrong', "what's wrong", 'what happened', 'why is my',
            'help my', 'save my', 'cure', 'treat', 'remedy', 'medicine',
            'spray', 'pesticide', 'fungicide', 'insecticide'
        ]
        
        # Check for disease patterns (highest priority after image)
        disease_match_count = sum(1 for word in disease_keywords if word in message_lower)
        if disease_match_count >= 1:  # Even single match indicates disease concern
            state["intent"] = "disease_detection"
            logger.info(f"Intent: disease_detection (keyword match count: {disease_match_count})")
            return state
        
        # Check for planner patterns
        if any(word in message_lower for word in planner_keywords):
            state["intent"] = "planner_create"
            logger.info(f"Intent: planner_create (keyword match)")
            return state
        
        # Check for dashboard/info patterns
        if any(word in message_lower for word in weather_keywords + market_keywords):
            state["intent"] = "dashboard_query"
            logger.info(f"Intent: dashboard_query (keyword match)")
            return state

        # Use Gemini for ambiguous cases with improved prompt
        system_prompt = """You are an intent classification expert for agricultural AI.
Analyze the user message and classify into ONE category with absolute certainty.

Categories:
- 'disease_detection': ANY questions about crop diseases, symptoms, pest issues, plant health problems, dying/yellowing/wilting plants, treatment/remedy requests, crop damage reports
- 'planner_create': Requests to schedule tasks, create farming timeline, set reminders, plan activities, when to do something
- 'dashboard_query': Questions about weather, market prices, news, government announcements, current conditions, commodity rates
- 'general_chat': General farming advice, Q&A, tips, techniques, best practices, learning, greetings

Rules:
- If message mentions ANY plant symptoms (color change, wilting, spots, holes, etc.) = 'disease_detection'
- If asking for treatment, cure, remedy, spray, pesticide = 'disease_detection'
- If message says "my crop", "my plant" with concern/worry = 'disease_detection'
- Weather/market/news queries = 'dashboard_query'
- Task/schedule/planning = 'planner_create'
- If unsure but seems farming related = 'disease_detection'
- Only use 'general_chat' for clear non-problem questions

Respond with ONLY the category name in lowercase, nothing else."""
        
        intent = call_gemini(state["message"], system_prompt, temperature=0.1, max_tokens=20)
        intent = intent.strip().lower().replace("'", "").replace('"', "") if intent else "general_chat"
        
        # Validate intent
        valid_intents = ["disease_detection", "planner_create", "dashboard_query", "general_chat"]
        state["intent"] = intent if intent in valid_intents else "general_chat"
        
        logger.info(f"Intent detected: {state['intent']}")
        
    except Exception as e:
        logger.error(f"Error in intent detection: {e}")
        state["intent"] = "general_chat"
    
    return state


async def disease_detection_node(state: FarmoraState) -> FarmoraState:
    """Analyze crop disease using Gemini intelligence with personalized guidance."""
    try:
        # Get user-specific profile from state
        user_profile = state.get("user_profile") or {}
        
        result = await analyze_disease(state["image"], state["message"], user_profile)
        state["disease_data"] = result
        
        # Get user's preferred language
        language = user_profile.get("language", "en")
        
        # Get user context
        crops = ', '.join(user_profile.get('crops', [])) if user_profile.get('crops') else 'your crops'
        location = user_profile.get('farm_location', 'your location')
        
        # Format response using Gemini with empathy and actionable advice
        format_prompt = f"""You are Farmora AI, helping a farmer at {location} who grows {crops}.

Disease Analysis Results:
- Disease Identified: {result.get('label', 'Unknown')}
- Confidence Level: {result.get('confidence', 0):.0f}%
- Severity: {result.get('severity', 'unknown')}
- Immediate Action Required: {result.get('immediate_action', 'Monitor crop')}

Treatment Plan:
{result.get('remedy', 'N/A')}

Prevention Measures:
{', '.join(result.get('prevention_tips', []))}

Follow-up:
{result.get('follow_up', 'Review in 1 week')}

Create a compassionate, actionable response following this structure:

1. **Diagnosis & Empathy:**
   - Acknowledge the concern and reassure the farmer
   - State the disease clearly with confidence level
   - Explain the severity in simple terms

2. **Immediate Actions (Next 24-48 hours):**
   - List 3-4 specific steps they should take RIGHT NOW
   - Include quantities, timing, and methods
   - Mention safety precautions if using chemicals

3. **Treatment Plan (This week):**
   - Detailed remedy instructions
   - Alternative organic options if available
   - Cost-effective solutions
   - Expected timeline for improvement

4. **Prevention for Future:**
   - Practical tips to avoid recurrence
   - Crop management practices
   - Monitoring suggestions

5. **Encouragement & Support:**
   - Positive note about catching it early/managing it
   - Reminder that you're here to help with follow-up questions
   - When to consult a local agricultural expert if needed

**Formatting:**
- Use emojis for engagement (⚠️ ✅ 💊 🌿 📋 etc.)
- Use numbered lists for clarity
- Highlight urgent actions with bold or emojis
- Keep language simple and practical

CRITICAL RULES:
1. Generate the ENTIRE response in {language} language ONLY
2. DO NOT include any English translation or "(Translation for context...)" notes
3. DO NOT add meta-commentary about language
4. Respond naturally as if {language} is your native language"""

        system_prompt = f"""You are Farmora AI - a knowledgeable, empathetic agricultural health expert. You understand farmers' concerns about crop health and provide clear, actionable guidance.

Your approach:
- Show empathy for the farmer's concern
- Provide confidence through clear explanation
- Give specific, step-by-step instructions
- Explain the 'why' behind recommendations
- Offer both chemical and organic solutions when possible
- Prioritize farmer safety and crop health
- Be encouraging and supportive

Always respond in {language} language."""
        
        state["response"] = call_gemini(format_prompt, system_prompt, temperature=0.7, max_tokens=1200)
        state["confidence"] = result.get('confidence', 0) / 100.0
        
    except Exception as e:
        logger.error(f"Error in disease detection: {e}")
        state["response"] = f"❌ Error analyzing disease: {str(e)}. Please try again or consult a local agricultural expert."
        state["disease_data"] = {}
        state["confidence"] = 0.0
    
    return state


async def planner_node(state: FarmoraState) -> FarmoraState:
    """Generate intelligent farm planning suggestions using Gemini with personalization."""
    try:
        # Get user-specific profile from state
        user_profile = state.get("user_profile") or {}
        
        # Get conversation history for context (user-specific)
        from farmora_backend.app.services.chat_service import get_context_from_history
        context = await get_context_from_history(state["user_id"], limit=5)
        
        # Get user's preferred language
        language = user_profile.get("language", "en")
        
        suggestions = await generate_planner_suggestions(
            state["user_id"],
            state["message"],
            user_profile,
            language=language
        )
        state["planner_data"] = suggestions
        
        # Build personalized context
        user_name = "Farmer friend"
        crops = ', '.join(user_profile.get('crops', [])) if user_profile.get('crops') else 'your crops'
        location = user_profile.get('farm_location', 'your location')
        
        # Format using Gemini with rich personalization
        format_prompt = f"""You are Farmora AI, speaking to a farmer at {location} who grows {crops}.

Generated Task Suggestions:
{json.dumps(suggestions, indent=2)}

Context from Recent Conversations:
{context if context else "No previous context"}

Create a warm, personalized response that:

1. **Greeting & Acknowledgment:**
   - Greet the farmer warmly and acknowledge their request
   - Reference their location and crops to show you understand their context

2. **Task Presentation:**
   - Present each task clearly with:
     * Task name and date (format: Month DD, YYYY)
     * Priority level (High/Medium/Low) with an emoji (🔴/🟡/🟢)
     * Why this task matters RIGHT NOW (tie to season, crop cycle, or current conditions)
     * Brief description of what needs to be done

3. **Encouragement & Benefits:**
   - Explain how completing these tasks will benefit their farm
   - Share a motivational note about good farming practices
   - Mention expected outcomes (better yield, disease prevention, etc.)

4. **Call to Action:**
   - Ask them to confirm which tasks they'd like to add to their schedule
   - Let them know they can modify dates or priorities if needed
   - Offer to provide more details about any specific task

**Formatting Guidelines:**
- Use emojis to make it engaging (✅ 📅 🌾 🚜 ⏰ etc.)
- Number the tasks (1., 2., 3.)
- Keep it conversational, not formal
- Show empathy and understanding of their farming challenges

CRITICAL RULES:
1. Generate the ENTIRE response in {language} language ONLY
2. DO NOT include any English translation or "(Translation for context...)" notes
3. DO NOT add meta-commentary about language
4. Respond naturally as if {language} is your native language"""

        system_prompt = f"""You are Farmora AI - a supportive, knowledgeable farming mentor. You understand the challenges farmers face and provide encouragement along with practical advice. 

Your tone is:
- Warm and friendly (like talking to a friend)
- Respectful of the farmer's experience
- Optimistic and encouraging
- Specific and actionable (not vague)

Always respond in {language} language."""
        
        state["response"] = call_gemini(format_prompt, system_prompt, temperature=0.75, max_tokens=1200)
        state["confidence"] = 0.88
        
    except Exception as e:
        logger.error(f"Error in planner node: {e}")
        state["response"] = f"❌ Unable to generate planner suggestions: {str(e)}"
        state["planner_data"] = []
        state["confidence"] = 0.0
    
    return state


async def dashboard_node(state: FarmoraState) -> FarmoraState:
    """Fetch dashboard data and format using Gemini - only when intent requires it."""
    try:
        # Get user-specific profile from state
        user_profile = state.get("user_profile") or {}
        
        # Determine what context to fetch based on the query
        message_lower = state["message"].lower()
        needs_weather = any(word in message_lower for word in ['weather', 'temperature', 'rain', 'climate', 'forecast', 'humid', 'wind'])
        needs_market = any(word in message_lower for word in ['market', 'price', 'news', 'sell', 'buy', 'crop price', 'mandi'])
        
        # Get user's preferred language
        language = user_profile.get("language", "en")
        
        weather_text = ""
        market_news_text = ""
        
        # Fetch only what's needed
        if needs_weather:
            try:
                from farmora_backend.app.services.dashboard_service import generate_weather_insights
                weather_data = await generate_weather_insights(user_profile)
                state["context_data"]["weather"] = weather_data
                
                if not weather_data.get('error'):
                    weather_text = f"""
🌡️ Temperature: {weather_data.get('temperature', 'N/A')}°C (feels like {weather_data.get('feels_like', 'N/A')}°C)
💧 Humidity: {weather_data.get('humidity', 'N/A')}%
🌤️ Conditions: {weather_data.get('description', 'N/A')}
💨 Wind: {weather_data.get('wind_speed', 'N/A')} m/s
📍 Location: {weather_data.get('city', 'Unknown')}
⚠️ Alerts: {', '.join(weather_data.get('alerts', [])) or 'None'}
🤖 AI Insights: {weather_data.get('ai_insights', 'No insights available')}
"""
                else:
                    weather_text = f"⚠️ Weather data unavailable: {weather_data.get('error', 'Unknown error')}"
            except Exception as we:
                logger.warning(f"Weather fetch failed: {we}")
                weather_text = "⚠️ Weather service temporarily unavailable"
        
        if needs_market:
            try:
                from farmora_backend.app.core.database import db
                record = await db.db.dashboard_data.find_one({"type": "market_news"})
                if record:
                    market_news = record.get("data", [])[:5]
                    state["context_data"]["market_news"] = market_news
                    market_news_text = "📰 Latest Agricultural News:\n"
                    for idx, news in enumerate(market_news[:3], 1):
                        market_news_text += f"{idx}. {news.get('title', 'Update')} - {news.get('summary', '')[:100]}...\n"
                else:
                    market_news_text = "📰 Market news will be available soon"
            except Exception as me:
                logger.warning(f"Market news fetch failed: {me}")
                market_news_text = "📰 Market news temporarily unavailable"
        
        # Build context-aware prompt
        context_parts = []
        if weather_text:
            context_parts.append(f"Weather Information:\n{weather_text}")
        if market_news_text:
            context_parts.append(market_news_text)
        
        if not context_parts:
            # If no specific context needed, get basic dashboard data
            context_parts.append("Provide general farm dashboard insights based on the user's query.")
        
        format_prompt = f"""User Query: {state['message']}

Available Context:
{chr(10).join(context_parts)}

Create a helpful, conversational response that:
1. Directly answers the user's question using the available context
2. Provides actionable advice relevant to their farming needs
3. Uses emojis appropriately for engagement
4. If weather-related: explain implications for farming activities
5. If market-related: highlight key trends or opportunities

CRITICAL RULES:
1. Generate the ENTIRE response in {language} language ONLY
2. DO NOT include any English translation or "(Translation for context...)" notes
3. DO NOT add meta-commentary about language
4. Respond naturally as if {language} is your native language"""

        system_prompt = f"""You are an agricultural expert providing contextual farming insights. Be direct, practical, and conversational.
Rules: Respond ONLY in {language}. NO English translations. NO meta-commentary about language."""
        
        state["response"] = call_gemini(format_prompt, system_prompt, temperature=0.7, max_tokens=1000)
        state["confidence"] = 0.85
        
    except Exception as e:
        logger.error(f"Error in dashboard node: {e}")
        state["response"] = f"❌ Unable to fetch dashboard data: {str(e)}"
        state["context_data"] = {}
        state["confidence"] = 0.0
    
    return state


async def general_chat_node(state: FarmoraState) -> FarmoraState:
    """Handle general farming questions using Gemini with conversation history and intelligent context."""
    try:
        # Get user-specific profile from state
        user_profile = state.get("user_profile") or {}
        
        # Get conversation context from history (user-specific)
        context = await get_context_from_history(state["user_id"], limit=8)
        
        # Get user's preferred language
        language = user_profile.get("language", "en")
        
        # Analyze if query needs additional context
        message_lower = state["message"].lower()
        needs_weather = any(word in message_lower for word in ['weather', 'temperature', 'rain', 'climate', 'today', 'humid', 'hot', 'cold'])
        needs_market = any(word in message_lower for word in ['market', 'price', 'news', 'sell', 'mandi', 'rate'])
        
        additional_context = []
        
        # Fetch weather if question seems weather-related
        if needs_weather and user_profile:
            try:
                from farmora_backend.app.services.dashboard_service import generate_weather_insights
                weather_data = await generate_weather_insights(user_profile)
                if not weather_data.get('error'):
                    weather_summary = f"🌤️ Current Weather at {weather_data.get('city', 'your location')}: {weather_data.get('temperature')}°C ({weather_data.get('description')}), Humidity: {weather_data.get('humidity')}%, Wind: {weather_data.get('wind_speed')} m/s"
                    if weather_data.get('ai_insights'):
                        weather_summary += f"\n💡 {weather_data.get('ai_insights')}"
                    additional_context.append(weather_summary)
            except Exception as we:
                logger.warning(f"Weather fetch failed: {we}")
        
        # Fetch market news if question seems market-related
        if needs_market:
            try:
                from farmora_backend.app.core.database import db
                record = await db.db.dashboard_data.find_one({"type": "market_news"})
                if record:
                    market_news = record.get("data", [])[:3]
                    market_summary = "📰 Latest Market Updates:\n" + "\n".join([f"- {n.get('title', '')}: {n.get('summary', '')[:80]}..." for n in market_news])
                    additional_context.append(market_summary)
            except Exception as me:
                logger.warning(f"Market news fetch failed: {me}")
        
        # Build comprehensive system prompt with user profile context
        profile_context = ""
        if user_profile:
            crops = ', '.join(user_profile.get('crops', [])) or 'Not specified'
            location = user_profile.get('farm_location', 'Unknown')
            profile_context = f"""Farmer Profile:
- Name/ID: Known farmer in the system
- Location: {location}
- Crops: {crops}
- Experience: Active user of Farmora AI
- Language Preference: {language}
"""
        
        system_prompt = f"""You are Farmora AI - a highly knowledgeable, compassionate agricultural expert specifically trained for Indian farmers.

{profile_context}

Your Core Expertise:
- Deep knowledge of Indian agriculture, crops, and farming practices
- Understanding of regional/seasonal variations across India
- Expertise in organic farming, pest management, irrigation, and soil health
- Awareness of government schemes (PM-KISAN, soil health cards, crop insurance)
- Knowledge of sustainable and climate-smart agriculture
- Understanding of farm economics and market dynamics

Your Communication Style:
- Warm, encouraging, and supportive - like a knowledgeable farming mentor
- Use relevant emojis to make advice engaging (🌾 🚜 💧 ☀️ 🌱 etc.)
- Break down complex topics into simple, actionable steps
- Provide specific measurements, timing, and methods (not vague advice)
- Always consider the user's crops and location when giving advice
- Share both traditional wisdom and modern scientific practices
- Encourage sustainable and economically viable farming

Response Guidelines:
- Be conversational and natural, not robotic
- Address farmers respectfully (you can use terms like "friend", "farmer brother/sister")
- When giving recommendations, explain WHY (help them understand, not just follow)
- Provide 3-4 concrete action items when relevant
- Mention costs/budget when suggesting inputs or practices
- Include safety warnings when dealing with pesticides or equipment
- Reference seasonal timing and local practices
- If uncertain, acknowledge limitations and suggest consulting local experts

Context Awareness:
- Remember and reference previous conversation topics when relevant
- Connect current advice to the farmer's profile (crops, location)
- Use real-time weather/market data when available to make advice timely
- Adapt language complexity to be accessible to all education levels

CRITICAL RULES:
1. You MUST respond ONLY in {language} language
2. Generate your entire response directly in {language}
3. Every word, sentence, and explanation should be in {language}
4. DO NOT include any English translation or "(Translation for context...)" notes
5. DO NOT add any meta-commentary about the language you're using
6. DO NOT explain what language you're responding in
7. Just respond naturally in {language} as if it's your native language"""
        
        # Build prompt with conversation history and additional context
        prompt_parts = []
        
        if context:
            prompt_parts.append(f"Previous Conversation Context:\n{context}\n")
        
        if additional_context:
            prompt_parts.append(f"Real-Time Context:\n{chr(10).join(additional_context)}\n")
        
        prompt_parts.append(f"Current Farmer Question: {state['message']}")
        prompt_parts.append("\nProvide a helpful, contextual response considering their profile, conversation history, and current conditions.")
        
        prompt = "\n".join(prompt_parts)
        
        state["response"] = call_gemini(prompt, system_prompt, temperature=0.8, max_tokens=1500)
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
    """Invoke the graph with user profile context passed through state (thread-safe)."""
    # Pass user profile through state instead of global variable
    state["user_profile"] = user_profile
    return await _original_ainvoke(state)


# Replace the graph's ainvoke with the profile-aware wrapper
farmora_ai.ainvoke = ainvoke_with_profile
