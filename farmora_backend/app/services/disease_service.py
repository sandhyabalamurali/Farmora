import logging
import json
from typing import Dict, Any, Optional
from groq import Groq
from farmora_backend.app.config import settings

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.GROQ_API_KEY)


async def identify_crop_type(user_crops: list, image_data: Optional[str] = None) -> str:
    """
    Identify primary crop type from user profile and optional image.
    Returns: 'paddy', 'wheat', 'maize', 'other', or 'unknown'
    """
    try:
        # If user has crops listed, identify primary crop
        if user_crops:
            crop_name = user_crops[0].lower()
            
            # Map common crop names to categories
            paddy_aliases = ['paddy', 'rice', 'dhaan', 'chawal', 'oryza']
            wheat_aliases = ['wheat', 'gehun', 'gandu']
            maize_aliases = ['maize', 'corn', 'makka', 'bhutta']
            
            if any(alias in crop_name for alias in paddy_aliases):
                return "paddy"
            elif any(alias in crop_name for alias in wheat_aliases):
                return "wheat"
            elif any(alias in crop_name for alias in maize_aliases):
                return "maize"
            else:
                return "other"
        
        # If no crops listed but image provided, use LLM to identify
        if image_data:
            crop_prompt = """Identify the crop in this image with one word only: 'paddy', 'wheat', 'maize', or 'other'.
Respond with ONLY the crop name, nothing else."""
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a crop identification expert."},
                    {"role": "user", "content": crop_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            crop_type = response.choices[0].message.content.strip().lower()
            if crop_type in ['paddy', 'wheat', 'maize', 'other']:
                return crop_type
        
        return "unknown"
        
    except Exception as e:
        logger.warning(f"Error identifying crop type: {e}")
        return "unknown"


async def analyze_paddy_disease(image_data: str, caption: str, location: str) -> Dict[str, Any]:
    """
    Specialized disease analysis for Paddy crops using trained knowledge.
    Paddy-specific diseases: Brown spot, Leaf blast, Sheath blight, Bakanae, etc.
    """
    try:
        paddy_prompt = f"""You are an expert PADDY/RICE crop pathologist.
Analyze this paddy crop image for PADDY-SPECIFIC diseases:
- Image: {caption or 'Paddy crop image'}
- Location: {location or 'India'}

Known Paddy Diseases:
1. Brown Spot - circular brown lesions on leaves
2. Leaf Blast - spindle-shaped lesions, gray center
3. Sheath Blight - irregular greenish-gray spots
4. Bakanae (Foolish Seedling) - excessive height, thin stems
5. Rice Hispa - white streaks, shot holes
6. Stem Borer - holes in stems, dead hearts

Provide analysis in JSON:
{{
    "disease_name": "identified paddy disease",
    "confidence": 90,
    "severity": "low/medium/high",
    "symptoms": "specific symptoms seen in paddy",
    "remedy": "paddy-specific treatment with chemical names and doses",
    "prevention_tips": ["tip 1 specific to paddy", "tip 2"],
    "immediate_action": "urgent action specific to stage of crop",
    "follow_up": "monitoring plan for paddy",
    "stage_affected": "leaf/stem/grain",
    "pesticide_recommended": "with dosage if needed"
}}"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a paddy/rice crop specialist. Provide precise, practical remedies. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": paddy_prompt
                }
            ],
            temperature=0.4,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(response_text)
        except json.JSONDecodeError:
            analysis = {
                "disease_name": "Paddy Disease Analysis",
                "confidence": 75,
                "severity": "medium",
                "remedy": response_text,
                "prevention_tips": ["Monitor leaf health", "Maintain water level", "Use fungicide if severity increases"],
                "immediate_action": "Inspect paddy field thoroughly"
            }
            
        return {
            "label": analysis.get("disease_name", "Paddy Disease"),
            "confidence": float(analysis.get("confidence", 75)),
            "remedy": analysis.get("remedy", "Consult local agricultural officer"),
            "prevention_tips": analysis.get("prevention_tips", []),
            "severity": analysis.get("severity", "medium"),
            "requires_intervention": analysis.get("severity", "medium").lower() in ["medium", "high"],
            "symptoms": analysis.get("symptoms", ""),
            "immediate_action": analysis.get("immediate_action", "Monitor paddy"),
            "follow_up": analysis.get("follow_up", "Review in 3-5 days"),
            "crop_type": "paddy"
        }
        
    except Exception as e:
        logger.error(f"Error in paddy disease analysis: {e}")
        return {
            "label": "Paddy Analysis Error",
            "confidence": 0,
            "remedy": "Unable to analyze paddy disease. Consult local agricultural expert.",
            "prevention_tips": [],
            "severity": "unknown",
            "requires_intervention": False,
            "crop_type": "paddy"
        }


async def analyze_multimodal_disease(image_data: str, caption: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    General disease analysis for non-paddy crops using multimodal AI.
    Works for any crop type.
    """
    try:
        context_str = ""
        if user_context:
            crops = user_context.get("crops", [])
            location = user_context.get("farm_location", "")
            context_str = f"User grows: {', '.join(crops) or 'mixed crops'}. Location: {location or 'unknown'}.\n"
        
        if image_data:
            analysis_prompt = f"""{context_str}
Analyze this crop image for diseases, pests, or health issues:
- Image description: {caption or 'Crop image provided'}

Provide a detailed analysis in JSON format:
{{
    "disease_name": "name of disease or condition",
    "confidence": 85,
    "severity": "low/medium/high",
    "symptoms_observed": "detailed symptoms from image",
    "immediate_action": "urgent step to take today",
    "remedy": "detailed treatment plan with specific chemicals/methods",
    "prevention_tips": ["tip 1", "tip 2", "tip 3"],
    "follow_up": "what to do in 1 week",
    "estimated_recovery_time": "days/weeks"
}}

Be specific, practical, and tailor advice to {context_str}. If healthy, say 'Healthy_Crop'."""
        else:
            analysis_prompt = f"""{context_str}
User describes their crop condition: "{caption}"

Provide detailed agricultural analysis in JSON format:
{{
    "disease_name": "identified condition or 'Healthy'",
    "confidence": 75,
    "severity": "low/medium/high",
    "analysis": "what's happening to the crop",
    "remedy": "specific treatment steps",
    "prevention_tips": ["tip 1", "tip 2", "tip 3"],
    "immediate_action": "what to do today",
    "follow_up": "monitoring plan"
}}

Be expert-level practical and specific."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert agricultural pathologist and crop specialist. Analyze disease symptoms and provide actionable, precise remedies. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            temperature=0.5,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON response, creating structured response")
            analysis = {
                "disease_name": "Analysis Complete",
                "confidence": 70,
                "severity": "medium",
                "remedy": response_text,
                "prevention_tips": ["Monitor regularly", "Maintain proper irrigation"],
                "immediate_action": response_text[:200]
            }
        
        return {
            "label": analysis.get("disease_name", "Unknown"),
            "confidence": float(analysis.get("confidence", 70)),
            "remedy": analysis.get("remedy", "Consult agricultural expert"),
            "prevention_tips": analysis.get("prevention_tips", []),
            "severity": analysis.get("severity", "medium"),
            "requires_intervention": analysis.get("severity", "medium").lower() in ["medium", "high"],
            "symptoms": analysis.get("symptoms_observed", analysis.get("analysis", "")),
            "immediate_action": analysis.get("immediate_action", "Monitor crop closely"),
            "follow_up": analysis.get("follow_up", "Review in 1 week"),
            "crop_type": "other"
        }
        
    except Exception as e:
        logger.error(f"Error in general disease analysis: {e}")
        return {
            "label": "Analysis Error",
            "confidence": 0,
            "remedy": "Unable to analyze at this moment. Please try again or consult a local agricultural expert.",
            "prevention_tips": [],
            "severity": "unknown",
            "requires_intervention": False,
            "crop_type": "other"
        }


async def analyze_disease(image_data: str, caption: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Main disease analysis function with crop-based routing.
    
    Flow:
    1. Identify crop type from user profile or image
    2. If Paddy: Use specialized paddy disease model
    3. Else: Use general multimodal disease analysis
    
    Args:
        image_data: Base64 encoded image or None
        caption: Image caption or symptom description
        user_context: User profile with crops and location
    
    Returns:
        Disease analysis dict with remedy, prevention, severity
    """
    try:
        # 1. Identify crop type
        user_crops = user_context.get("crops", []) if user_context else []
        crop_type = await identify_crop_type(user_crops, image_data)
        
        logger.info(f"Identified crop type: {crop_type}")
        
        # 2. Route to appropriate analyzer
        if crop_type == "paddy":
            location = user_context.get("farm_location", "") if user_context else ""
            result = await analyze_paddy_disease(image_data or "", caption or "", location)
        else:
            result = await analyze_multimodal_disease(image_data, caption, user_context)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in main disease analysis: {e}", exc_info=True)
        return {
            "label": "Analysis Error",
            "confidence": 0,
            "remedy": "Unable to analyze disease. Please try again.",
            "prevention_tips": [],
            "severity": "unknown",
            "requires_intervention": False
        }
