import httpx
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from farmora_backend.app.core.database import db
from farmora_backend.app.config import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# Configuration
NEWS_API_URL = "https://api.apitube.io/v1/news/everything"
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = settings.NEWS_API_KEY
WEATHER_API_KEY = settings.OPENWEATHER_API_KEY


async def fetch_weather_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch real weather data from OpenWeatherMap API.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                WEATHER_API_URL,
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": WEATHER_API_KEY,
                    "units": "metric"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                weather = {
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"],
                    "icon": data["weather"][0]["icon"],
                    "wind_speed": data["wind"]["speed"],
                    "clouds": data["clouds"]["all"],
                    "visibility": data.get("visibility", 10000),
                    "city": data.get("name", "Unknown"),
                    "country": data.get("sys", {}).get("country", ""),
                    "sunrise": data["sys"].get("sunrise"),
                    "sunset": data["sys"].get("sunset"),
                }
                
                # Check for weather alerts relevant to farming
                alerts = []
                if weather["temperature"] > 40:
                    alerts.append("🔥 EXTREME HEAT ALERT: Temperature above 40°C. Avoid outdoor work during peak hours. Ensure livestock has adequate water and shade.")
                if weather["temperature"] < 5:
                    alerts.append("❄️ FROST ALERT: Low temperatures may damage crops. Consider protective covering for sensitive plants.")
                if weather["humidity"] > 85:
                    alerts.append("💧 HIGH HUMIDITY ALERT: Increased risk of fungal diseases. Monitor crops closely and ensure proper ventilation.")
                if weather["wind_speed"] > 10:
                    alerts.append("💨 STRONG WIND ALERT: Secure greenhouse structures and young plants. Delay spraying operations.")
                if "rain" in weather["description"].lower():
                    alerts.append("🌧️ RAIN EXPECTED: Good time to delay irrigation. Prepare drainage systems.")
                
                weather["alerts"] = alerts
                return weather
            else:
                logger.error(f"Weather API error: {response.status_code}")
                raise Exception(f"Weather API returned status {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        raise


async def fetch_and_process_market_data():
    """
    Background Job: Fetches real market data and uses Gemini AI to summarize.
    """
    logger.info("🔄 [Background Job] Fetching and analyzing market news...")
    
    market_news = []
    try:
        async with httpx.AsyncClient() as client_http:
            response = await client_http.get(
                NEWS_API_URL,
                params={
                    "api_key": API_KEY,
                    "per_page": 10,
                    "category.id": "medtop:20000210",
                    "language.code": "en",
                    "source.country.code": "in"
                },
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📰 [Background Job] API Response keys: {list(data.keys())}")
                
                if data.get("errors"):
                    logger.error(f"❌ [Background Job] API Error: {data.get('errors')}")
                    raise Exception(f"News API Error: {data.get('errors')}")
                
                results = data.get("results", [])
                logger.info(f"📰 [Background Job] Found {len(results)} articles")
                
                if results:
                    market_news = await _ai_summarize_news(results)
                    logger.info(f"🔍 [Background Job] AI processed {len(market_news)} relevant items")
                else:
                    raise Exception("No results from News API")
                
                # Save to MongoDB
                await db.db.dashboard_data.update_one(
                    {"type": "market_news"},
                    {
                        "$set": {
                            "data": market_news,
                            "last_updated": datetime.utcnow(),
                            "source": "apitube"
                        }
                    },
                    upsert=True
                )
                logger.info(f"✅ [Background Job] Stored {len(market_news)} relevant news items.")
            else:
                logger.error(f"⚠️ [Background Job] API Error: {response.status_code} - {response.text[:200]}")
                raise Exception(f"News API returned status {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ [Background Job] Failed: {e}", exc_info=True)
        raise


async def _ai_summarize_news(articles: List[Dict]) -> List[Dict[str, Any]]:
    """
    Summarize articles using Gemini AI.
    """
    try:
        top_articles = articles[:10]

        articles_text = "\n\n".join([
            f"TITLE: {art.get('title','')}\nDESC: {art.get('description','') or ''}\nSOURCE: {art.get('source',{}).get('domain','') or art.get('source','') or ''}\nURL: {art.get('href','') or art.get('url','')}"
            for art in top_articles
        ])

        prompt = f"""Summarize each of the following agricultural news articles in one concise paragraph (20-50 words). 
Return a JSON array of objects with fields: title, description, summary, source, url, published_at.

Do NOT invent new articles or change titles. Use the provided title and description. Return ONLY valid JSON array.

Articles:
{articles_text}
"""

        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=2000,
            )
        )

        response_text = response.text.strip()
        logger.info(f"🤖 [Gemini Response] Raw response:\n{response_text[:1000]}")

        # Extract JSON
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            ranked = json.loads(response_text)
        except Exception as e:
            logger.error(f"Failed to parse Gemini JSON: {e}")
            raise Exception(f"Failed to parse AI response: {e}")

        processed_news: List[Dict[str, Any]] = []

        if isinstance(ranked, list) and ranked:
            for item in ranked:
                processed_news.append({
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "summary": item.get("summary", ""),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "published_at": item.get("published_at", "")
                })
        else:
            raise Exception("AI returned invalid response format")

        logger.info(f"📰 Final processed news count: {len(processed_news)}")
        return processed_news

    except Exception as e:
        logger.error(f"Error in AI news summarization: {e}", exc_info=True)
        raise


async def generate_weather_insights(user_profile: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate real weather data with AI insights for farming.
    """
    try:
        # Get user's location from profile
        lat = None
        lon = None
        
        if user_profile:
            lat = user_profile.get("latitude")
            lon = user_profile.get("longitude")
        
        if not lat or not lon:
            raise Exception("User location not available. Please update your profile with GPS location.")
        
        # Fetch real weather data
        weather_data = await fetch_weather_data(lat, lon)
        
        # Generate AI insights using Gemini
        crops = ", ".join(user_profile.get("crops", [])) if user_profile else "general crops"
        location = user_profile.get("farm_location", weather_data.get("city", "Unknown"))
        
        weather_prompt = f"""Based on this real weather data for a farm in {location} growing {crops}:
- Temperature: {weather_data['temperature']}°C (feels like {weather_data['feels_like']}°C)
- Humidity: {weather_data['humidity']}%
- Wind Speed: {weather_data['wind_speed']} m/s
- Conditions: {weather_data['description']}
- Cloud Cover: {weather_data['clouds']}%

Provide brief, actionable farming advice for today in 2-3 sentences. Focus on:
1. What farming activities are ideal today
2. Any precautions needed
3. Irrigation recommendations"""

        response = gemini_model.generate_content(
            weather_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=300,
            )
        )
        
        weather_data["ai_insights"] = response.text
        return weather_data
        
    except Exception as e:
        logger.error(f"Error generating weather insights: {e}")
        raise


async def get_dashboard_context(user_id: str, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Retrieve comprehensive dashboard data with real weather and AI-processed insights.
    """
    try:
        # Get market news
        market_news = []
        record = await db.db.dashboard_data.find_one({"type": "market_news"})
        if record:
            market_news = record.get("data", [])
        
        # Generate weather insights with real data
        weather_data = None
        try:
            weather_data = await generate_weather_insights(user_profile)
        except Exception as e:
            logger.warning(f"Weather fetch failed: {e}")
            weather_data = {"error": str(e)}
        
        return {
            "weather": weather_data,
            "market_news": market_news,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_dashboard_context: {e}")
        raise


# Keep old function name for backward compatibility
async def fetch_and_cache_market_data():
    """Backward compatibility wrapper."""
    await fetch_and_process_market_data()
