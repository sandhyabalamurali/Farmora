import httpx
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from farmora_backend.app.core.database import db
from groq import Groq
from farmora_backend.app.config import settings

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.GROQ_API_KEY)

# Configuration
NEWS_API_URL = "https://api.apitube.io/v1/news/everything"
CACHE_KEY = "dashboard:market_news"
API_KEY = settings.NEWS_API_KEY
async def fetch_and_process_market_data():
    """
    Background Job: Fetches real market data and uses AI to filter & analyze relevance.
    """
    logger.info("🔄 [Background Job] Fetching and analyzing market news...")
    
    market_news = []
    try:
        async with httpx.AsyncClient() as client_http:
            # Try agriculture-specific news first
            response = await client_http.get(
                NEWS_API_URL,
                params={
                    "api_key": API_KEY,
                    "limit": 50,
                    "language": "en",
                    "q": "agriculture farming crop India"
                },
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📰 [Background Job] API Response keys: {list(data.keys())}")
                
                # Check for API errors
                if data.get("errors"):
                    logger.error(f"❌ [Background Job] API Error: {data.get('errors')}")
                    return
                
                # Try different response structure keys
                results = data.get("results", []) or data.get("articles", []) or data.get("news", []) or data.get("data", [])
                logger.info(f"📰 [Background Job] Found {len(results)} articles")
                
                # Use AI to intelligently filter and rank news
                if results:
                    market_news = await _ai_filter_and_rank_news(results)
                    logger.info(f"🔍 [Background Job] AI selected {len(market_news)} relevant items")
                else:
                    logger.warning("⚠️ [Background Job] No results from API")
                
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
                logger.warning(f"⚠️ [Background Job] API Error: {response.status_code} - {response.text[:200]}")
                
    except Exception as e:
        logger.error(f"❌ [Background Job] Failed: {e}", exc_info=True)


async def _ai_filter_and_rank_news(articles: List[Dict]) -> List[Dict[str, Any]]:
    """
    Summarize the top 10 articles using the LLM and return concise structured summaries.
    Falls back to raw articles if AI is unavailable.
    """
    try:
        # Take top 10 articles from API
        top_articles = articles[:10]

        # Build a readable list for the LLM
        articles_text = "\n\n".join([
            f"TITLE: {art.get('title','')}\nDESC: {art.get('description','') or ''}\nSOURCE: {art.get('source',{}).get('domain','') or art.get('source','') or ''}\nURL: {art.get('href','') or art.get('url','')}"
            for art in top_articles
        ])

        prompt = f"""Summarize each of the following articles in one concise paragraph (20-50 words). Return a JSON array of objects with fields: title, description, summary, source, url, published_at.

Do NOT invent new articles or change titles. Use the provided title and description. Return ONLY valid JSON.

Articles:
{articles_text}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an assistant that summarizes news for Indian farmers. Be concise, factual, and do not add new content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1600
        )

        response_text = response.choices[0].message.content.strip()
        logger.info(f"🤖 [LLM Response] Raw response:\n{response_text[:1000]}")

        # Extract JSON if wrapped in code fences
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            logger.info(f"🤖 [LLM Response] Extracted JSON (truncated):\n{response_text[:500]}")
            ranked = json.loads(response_text)
        except Exception as e:
            logger.warning(f"Failed to parse LLM JSON: {e}; falling back to simple summaries")
            ranked = []

        processed_news: List[Dict[str, Any]] = []

        if isinstance(ranked, list) and ranked:
            for item in ranked:
                processed_news.append({
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "summary": item.get("summary", item.get("relevance_reason", "")),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "published_at": item.get("published_at", "")
                })
        else:
            # Fallback: create simple summaries from descriptions
            for art in top_articles:
                desc = art.get("description") or ""
                summary = (desc[:280] + "...") if len(desc) > 300 else desc
                processed_news.append({
                    "title": art.get("title", ""),
                    "description": desc,
                    "summary": summary,
                    "source": art.get("source", {}).get("domain", "") if isinstance(art.get("source"), dict) else art.get("source", ""),
                    "url": art.get("href", "") or art.get("url", ""),
                    "published_at": art.get("published_at", "")
                })

        logger.info(f"📰 Final processed news count: {len(processed_news)}")
        return processed_news

    except Exception as e:
        logger.error(f"Error in AI news summarization: {e}", exc_info=True)
        # Return raw articles as fallback when AI completely fails
        logger.info("⚠️ Falling back to raw articles without AI processing")
        fallback_news = []
        for art in articles[:10]:
            desc = art.get("description") or art.get("title") or ""
            fallback_news.append({
                "title": art.get("title", "Agricultural Update"),
                "description": desc,
                "summary": (desc[:280] + "...") if len(desc) > 300 else desc,
                "source": art.get("source", {}).get("domain", "") if isinstance(art.get("source"), dict) else art.get("source", ""),
                "url": art.get("href", "") or art.get("url", ""),
                "published_at": art.get("published_at", "")
            })
        return fallback_news


async def generate_weather_insights(user_profile: Optional[Dict] = None) -> str:
    """
    Generate AI-based weather insights and farming recommendations.
    """
    try:
        location = user_profile.get("farm_location", "India") if user_profile else "India"
        crops = ", ".join(user_profile.get("crops", [])) if user_profile else "general crops"
        
        weather_prompt = f"""Provide current weather insights for a farm in {location} growing {crops}.
        
        Generate a concise but detailed weather forecast focusing on:
        - Current conditions and 7-day forecast
        - Impact on crop growth
        - Irrigation recommendations
        - Risk assessment (pest, disease, floods)
        - Actionable advice for today
        
        Keep response practical and specific."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a agricultural meteorologist. Provide precise, actionable weather advice for farmers."
                },
                {
                    "role": "user",
                    "content": weather_prompt
                }
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating weather insights: {e}")
        return "Unable to fetch weather data. Please try again later."


async def get_dashboard_context(user_id: str, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Retrieve comprehensive dashboard data with AI-processed insights.
    """
    try:
        # Get market news
        market_news = []
        record = await db.db.dashboard_data.find_one({"type": "market_news"})
        if record:
            market_news = record.get("data", [])
        
        # Generate weather insights
        weather_insights = await generate_weather_insights(user_profile)
        
        # Get government announcements if stored
        announcements = []
        announce_record = await db.db.dashboard_data.find_one({"type": "announcements"})
        if announce_record:
            announcements = announce_record.get("data", [])
        
        return {
            "weather": weather_insights,
            "market_news": market_news,
            "government_announcements": announcements,
            "user_id": user_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"Error in get_dashboard_context: {e}")
        return {
            "weather": "Unable to fetch data",
            "market_news": [],
            "government_announcements": [],
            "user_id": user_id
        }


# Keep old function name for backward compatibility
async def fetch_and_cache_market_data():
    """Backward compatibility wrapper."""
    await fetch_and_process_market_data()
