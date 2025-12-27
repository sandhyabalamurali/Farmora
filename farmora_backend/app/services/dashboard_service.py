import httpx
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from farmora_backend.app.core.database import db
from farmora_backend.app.config import settings
import google.genai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
client = genai.Client(api_key=settings.GEMINI_API_KEY)

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
                    logger.warning(f"⚠️ [Background Job] API Error: {data.get('errors')}")
                    return  # Exit gracefully
                
                results = data.get("results", [])
                logger.info(f"📰 [Background Job] Found {len(results)} articles")
                
                if results:
                    market_news = await _ai_summarize_news(results)
                    logger.info(f"🔍 [Background Job] AI processed {len(market_news)} relevant items")
                else:
                    logger.warning("⚠️ [Background Job] No results from News API")
                    return  # Exit gracefully
                
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
                logger.warning(f"⚠️ [Background Job] API returned status {response.status_code}")
                return  # Exit gracefully
                
    except httpx.ConnectTimeout:
        logger.warning("⚠️ [Background Job] Connection timeout - news API may be unreachable. Will retry later.")
    except httpx.ConnectError as ce:
        logger.warning(f"⚠️ [Background Job] Connection error: {str(ce)}. Will retry later.")
    except httpx.HTTPError as he:
        logger.warning(f"⚠️ [Background Job] HTTP error: {str(he)}. Will retry later.")
    except Exception as e:
        logger.warning(f"⚠️ [Background Job] Failed: {str(e)}. Will retry later.")


async def _ai_summarize_news(articles: List[Dict]) -> List[Dict[str, Any]]:
    """
    Summarize articles using Gemini AI and filter irrelevant content.
    """
    try:
        top_articles = articles[:10]
        
        # Build a mapping of original article data (for images and URLs)
        article_extras = {}
        for i, art in enumerate(top_articles):
            # Get image URL from various possible fields
            image_url = art.get('image_url') or art.get('thumbnail') or art.get('urlToImage') or ''
            if not image_url and isinstance(art.get('media'), list) and art.get('media'):
                image_url = art['media'][0].get('url', '')
            # Get article URL - API uses 'href' field
            article_url = art.get('href') or art.get('url') or art.get('link') or ''
            # Get source properly
            source_data = art.get('source', {})
            if isinstance(source_data, dict):
                source_name = source_data.get('name', '') or source_data.get('domain', '')
            else:
                source_name = str(source_data) if source_data else ''
            article_extras[i] = {
                'image_url': image_url,
                'published_at': art.get('published_at', '') or art.get('publishedAt', ''),
                'url': article_url,
                'source': source_name
            }

        articles_text = "\n\n".join([
            f"Article {i+1}:\nTITLE: {art.get('title','')}\nDESC: {art.get('description','') or ''}\nSOURCE: {article_extras[i].get('source', 'Unknown')}\nURL: {article_extras[i].get('url', '')}"
            for i, art in enumerate(top_articles)
        ])

        prompt = f"""You are an agricultural news curator. Analyze the following {len(top_articles)} news articles and:

1. FILTER OUT articles that are NOT relevant to agriculture, farming, crops, livestock, weather impact on farming, or agricultural markets
2. For each RELEVANT article, create a professional 25-40 word summary

Return a JSON array with ONLY the relevant articles. Each object must have:
- "index": the original article number (1-based)
- "title": the exact original article title
- "description": original description or empty string
- "summary": your professional 25-40 word summary focusing on the farming/agricultural impact
- "source": the source name (clean it if needed, remove .com etc for display)
- "url": the original URL exactly as provided
- "published_at": publication date
- "is_relevant": true (only include relevant articles)

IMPORTANT RULES:
- ONLY include articles about: agriculture, farming, crops, weather, markets, government schemes for farmers, food prices, livestock, seeds, fertilizers, irrigation
- EXCLUDE: general politics (unless directly about farm policy), entertainment, sports, technology (unless agritech), crime news
- Return ONLY valid JSON array, no markdown, no explanation

Articles:
{articles_text}
"""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4000,
            )
        )

        response_text = response.text.strip()
        logger.info(f"🤖 [Gemini Response] Raw response (first 500 chars):\n{response_text[:500]}")

        # Clean up the response text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("["):
                    response_text = part
                    break
        
        # Try to find JSON array in response
        if not response_text.startswith("["):
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx != -1 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx]

        try:
            ranked = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini JSON: {e}")
            # Fall back to creating summaries from raw articles
            processed_news = []
            for idx, art in enumerate(top_articles):
                desc = art.get("description") or art.get("title") or ""
                summary = (desc[:150] + "...") if len(desc) > 150 else desc
                extras = article_extras.get(idx, {})
                processed_news.append({
                    "title": art.get("title", "Agricultural Update"),
                    "description": desc,
                    "summary": summary,
                    "source": art.get("source", {}).get("domain", "") if isinstance(art.get("source"), dict) else str(art.get("source", "")),
                    "url": art.get("href", "") or art.get("url", ""),
                    "published_at": art.get("published_at", "") or extras.get('published_at', ''),
                    "image_url": extras.get('image_url', '')
                })
            logger.info(f"📰 Fallback: processed {len(processed_news)} news items without AI summary")
            return processed_news

        processed_news: List[Dict[str, Any]] = []

        if isinstance(ranked, list) and ranked:
            for item in ranked:
                # Get the original article index (1-based from AI, convert to 0-based)
                original_idx = item.get("index", 0) - 1
                if original_idx < 0:
                    original_idx = len(processed_news)  # Fallback to sequential
                
                extras = article_extras.get(original_idx, {})
                
                # Clean source name (remove .com, www., etc)
                source = item.get("source", "") or extras.get('source', '')
                if source:
                    source = source.replace('www.', '').split('.com')[0].split('.in')[0].split('.org')[0]
                    source = source.title() if source else 'News'
                
                # Use URL from extras (original API data) as it's more reliable
                final_url = extras.get('url', '') or item.get("url", "")
                
                # Skip if no valid URL
                if not final_url or final_url == 'undefined' or final_url == 'null':
                    logger.warning(f"Skipping article without valid URL: {item.get('title', 'Unknown')[:50]}")
                    continue
                
                processed_news.append({
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "summary": item.get("summary", ""),
                    "source": source or "Agricultural News",
                    "url": final_url,
                    "published_at": item.get("published_at", "") or extras.get('published_at', ''),
                    "image_url": extras.get('image_url', '')
                })
        
        if not processed_news:
            raise Exception("No news items processed from AI response")

        logger.info(f"📰 Final processed news count: {len(processed_news)}")
        return processed_news

    except Exception as e:
        logger.error(f"Error in AI news summarization: {e}", exc_info=True)
        # Return simplified news without AI summary as fallback
        fallback_news = []
        for idx, art in enumerate(articles[:10]):
            desc = art.get("description") or art.get("title") or ""
            # Get image URL from various possible fields
            image_url = art.get('image_url') or art.get('thumbnail') or art.get('urlToImage') or ''
            if not image_url and isinstance(art.get('media'), list) and art.get('media'):
                image_url = art['media'][0].get('url', '')
            fallback_news.append({
                "title": art.get("title", "Agricultural Update"),
                "description": desc,
                "summary": (desc[:150] + "...") if len(desc) > 150 else desc,
                "source": art.get("source", {}).get("domain", "") if isinstance(art.get("source"), dict) else str(art.get("source", "")),
                "url": art.get("href", "") or art.get("url", ""),
                "published_at": art.get("published_at", "") or art.get("publishedAt", ""),
                "image_url": image_url
            })
        logger.info(f"📰 Exception fallback: returning {len(fallback_news)} news items without AI processing")
        return fallback_news


# Language name mapping for prompts
LANGUAGE_NAMES = {
    'en': 'English',
    'hi': 'Hindi',
    'bn': 'Bengali',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'mr': 'Marathi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ur': 'Urdu'
}


async def generate_weather_insights(user_profile: Optional[Dict] = None, language: str = 'en') -> Dict[str, Any]:
    """
    Generate real weather data with AI insights for farming, translated to user's language.
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
        lang_name = LANGUAGE_NAMES.get(language, 'English')
        
        weather_prompt = f"""Based on this real weather data for a farm in {location} growing {crops}:
- Temperature: {weather_data['temperature']}°C (feels like {weather_data['feels_like']}°C)
- Humidity: {weather_data['humidity']}%
- Wind Speed: {weather_data['wind_speed']} m/s
- Conditions: {weather_data['description']}
- Cloud Cover: {weather_data['clouds']}%

Provide brief, actionable farming advice for today in 2-3 sentences in {lang_name} language. Focus on:
1. What farming activities are ideal today
2. Any precautions needed
3. Irrigation recommendations

IMPORTANT: Respond ONLY in {lang_name} language."""    

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=weather_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=400,
            )
        )
        
        weather_data["ai_insights"] = response.text
        return weather_data
        
    except Exception as e:
        logger.error(f"Error generating weather insights: {e}")
        raise


async def get_translated_news(language: str = 'en') -> List[Dict[str, Any]]:
    """
    Get market news and translate to user's preferred language.
    """
    try:
        # Get cached news
        record = await db.db.dashboard_data.find_one({"type": "market_news"})
        if not record:
            return []
        
        market_news = record.get("data", [])
        
        # If English, return as-is
        if language == 'en':
            return market_news
        
        # Translate news summaries to target language
        lang_name = LANGUAGE_NAMES.get(language, 'English')
        
        # Build translation prompt for all news items
        news_texts = []
        for i, news in enumerate(market_news[:8]):  # Limit to 8 for token efficiency
            news_texts.append(f"Item {i+1}:\nTitle: {news.get('title', '')}\nSummary: {news.get('summary', '') or news.get('description', '')}")
        
        if not news_texts:
            return market_news
        
        translation_prompt = f"""Translate the following agricultural news items to {lang_name} language.
Keep the same format and structure. Return as JSON array with "title" and "summary" for each item.

{chr(10).join(news_texts)}

Return ONLY a valid JSON array like: [{{"title": "...", "summary": "..."}}]
Respond in {lang_name} language only."""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=translation_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4000,
            )
        )
        
        # Parse translated content
        response_text = response.text.strip()
        
        # Clean up response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("["):
                    response_text = part
                    break
        
        if not response_text.startswith("["):
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx != -1 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx]
        
        try:
            translated = json.loads(response_text)
            
            # Merge translated content with original data
            for i, trans in enumerate(translated):
                if i < len(market_news):
                    market_news[i]["title"] = trans.get("title", market_news[i].get("title"))
                    market_news[i]["summary"] = trans.get("summary", market_news[i].get("summary"))
            
            logger.info(f"📰 Translated {len(translated)} news items to {lang_name}")
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse translated news, returning original")
        
        return market_news
        
    except Exception as e:
        logger.error(f"Error translating news: {e}")
        # Return original news on error
        record = await db.db.dashboard_data.find_one({"type": "market_news"})
        return record.get("data", []) if record else []


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
            language = user_profile.get("language", "en") if user_profile else "en"
            weather_data = await generate_weather_insights(user_profile, language)
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
