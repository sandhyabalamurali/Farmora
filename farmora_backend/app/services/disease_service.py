import logging
import json
from typing import Dict, Any, Optional
from farmora_backend.app.config import settings
import google.genai as genai

logger = logging.getLogger(__name__)

# Configure Gemini
client = genai.Client(api_key=settings.GEMINI_API_KEY)


def call_gemini(prompt: str, system_prompt: str = "", temperature: float = 0.5, max_tokens: int = 1500) -> str:
    """Helper function to call Gemini API."""
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=full_prompt,
        config=genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    )
    return response.text


async def identify_crop_type(user_crops: list, image_data: Optional[str] = None) -> str:
    """
    Identify primary crop type from user profile and optional image.
    Returns: 'paddy', 'wheat', 'maize', 'other', or 'unknown'
    """
    try:
        if user_crops:
            crop_name = user_crops[0].lower()
            
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
        
        if image_data:
            crop_prompt = """Identify the crop in this image with one word only: 'paddy', 'wheat', 'maize', or 'other'.
Respond with ONLY the crop name, nothing else."""
            
            response = call_gemini(crop_prompt, "You are a crop identification expert.", temperature=0.1, max_tokens=10)
            crop_type = response.strip().lower()
            if crop_type in ['paddy', 'wheat', 'maize', 'other']:
                return crop_type
        
        return "unknown"
        
    except Exception as e:
        logger.warning(f"Error identifying crop type: {e}")
        return "unknown"


async def analyze_paddy_disease(image_data: str, caption: str, location: str) -> Dict[str, Any]:
    """
    Specialized disease analysis for Paddy crops using Gemini.
    Enhanced with comprehensive disease database and better prompting.
    """
    try:
        paddy_prompt = f"""You are an EXPERT PADDY/RICE crop pathologist with 20+ years experience in Indian agriculture.
Analyze this paddy crop for PADDY-SPECIFIC diseases with HIGH PRECISION.

Input:
- Image/Description: {caption or 'Paddy crop image'}
- Location: {location or 'India'}

=== COMPREHENSIVE PADDY DISEASE DATABASE ===

**FUNGAL DISEASES:**
1. Rice Blast (Magnaporthe oryzae)
   - Symptoms: Spindle-shaped lesions, gray center with brown border, node blast causes stem breakage
   - Severity indicators: Few spots = low, Many spots/node affected = high
   
2. Brown Spot (Bipolaris oryzae)
   - Symptoms: Oval/circular brown lesions with gray center, yellow halo on leaves
   - Common in nutrient-deficient fields
   
3. Sheath Blight (Rhizoctonia solani)
   - Symptoms: Irregular greenish-gray water-soaked spots, spreading to upper parts
   - Usually starts at water level on stems
   
4. Sheath Rot (Sarocladium oryzae)
   - Symptoms: Brown discoloration on sheath, poor panicle emergence
   
5. False Smut (Ustilaginoidea virens)
   - Symptoms: Orange/green spore balls replacing grains
   
6. Leaf Scald (Microdochium oryzae)
   - Symptoms: Zonate lesions with alternating tan and brown bands

**BACTERIAL DISEASES:**
7. Bacterial Leaf Blight (Xanthomonas oryzae)
   - Symptoms: Water-soaked streaks turning yellow to white, V-shaped lesions from leaf tips
   
8. Bacterial Leaf Streak
   - Symptoms: Fine translucent streaks between veins

**VIRAL DISEASES:**
9. Rice Tungro Virus
   - Symptoms: Yellow-orange discoloration, stunted growth, reduced tillering

**PEST DAMAGE:**
10. Stem Borer (Scirpophaga incertulas)
    - Symptoms: Dead hearts in vegetative stage, white heads in flowering
    
11. Leaf Folder (Cnaphalocrocis medinalis)
    - Symptoms: Longitudinally folded leaves with scraping
    
12. Brown Plant Hopper (Nilaparvata lugens)
    - Symptoms: Hopper burn - circular patches of dried plants
    
13. Rice Hispa (Dicladispa armigera)
    - Symptoms: White parallel streaks, shot holes in leaves

14. Bakanae Disease (Fusarium moniliforme)
    - Symptoms: Abnormally tall, thin, pale seedlings

Analyze with EXPERT PRECISION and respond in valid JSON:
{{
    "disease_name": "exact disease name from database above",
    "confidence": 85,
    "severity": "low/medium/high",
    "symptoms": "specific symptoms observed matching database",
    "remedy": "DETAILED treatment: Chemical name + dose (e.g., 'Tricyclazole 75WP @ 0.6g/L') AND organic alternative",
    "prevention_tips": ["crop rotation", "resistant varieties", "water management tip", "field hygiene"],
    "immediate_action": "most urgent action for THIS severity level",
    "follow_up": "monitoring schedule with specific checkpoints",
    "stage_affected": "seedling/tillering/flowering/grain filling",
    "pesticide_recommended": "specific product with exact dosage per acre/hectare",
    "economic_threshold": "spray if X% plants affected"
}}

IMPORTANT: Be SPECIFIC, not generic. Match symptoms to exact disease from database."""

        response = call_gemini(
            paddy_prompt,
            "You are India's top paddy crop pathologist. Provide PRECISE diagnosis with EXACT chemical dosages. Always return valid JSON only, no markdown.",
            temperature=0.3,  # Lower temperature for more consistent results
            max_tokens=1800
        )
        
        response_text = response.strip()
        
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
        raise


async def analyze_multimodal_disease(image_data: str, caption: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Enhanced general disease analysis for all crops using Gemini.
    Comprehensive prompt with expert-level analysis.
    """
    try:
        context_str = ""
        crops_list = ""
        if user_context:
            crops = user_context.get("crops", [])
            location = user_context.get("farm_location", "")
            crops_list = ', '.join(crops) if crops else 'mixed crops'
            context_str = f"Farmer grows: {crops_list}. Location: {location or 'India'}.\n"
        
        if image_data:
            analysis_prompt = f"""{context_str}
=== EXPERT CROP DISEASE ANALYSIS ===

You are an EXPERT agricultural pathologist analyzing a crop image for diseases.

Image Context: {caption or 'Crop image provided'}
Farmer's Crops: {crops_list or 'Unknown'}

=== COMMON CROP DISEASES TO CHECK ===

**FUNGAL DISEASES:**
- Powdery Mildew: White powdery coating on leaves/stems
- Downy Mildew: Yellow/brown patches with fuzzy growth underneath
- Anthracnose: Dark sunken lesions on fruits/leaves
- Fusarium Wilt: Yellowing, wilting from base upward
- Rust: Orange/brown pustules on leaves
- Early Blight: Dark concentric ring spots
- Late Blight: Water-soaked spots turning brown/black
- Root Rot: Wilting despite adequate water, brown roots

**BACTERIAL DISEASES:**
- Bacterial Wilt: Sudden wilting, slimy stem when cut
- Bacterial Spot: Small water-soaked spots turning brown
- Soft Rot: Mushy, foul-smelling tissue

**VIRAL DISEASES:**
- Mosaic Virus: Mottled light/dark green patterns
- Leaf Curl: Distorted, curled leaves
- Yellowing Virus: Uniform yellowing, stunted growth

**PEST DAMAGE:**
- Aphids: Curled leaves, sticky residue, sooty mold
- Caterpillars: Large irregular holes, frass present
- Whitefly: Yellowing, sticky residue, flying white insects
- Mites: Fine stippling, webbing, bronzing
- Thrips: Silver streaks, distorted growth
- Borers: Holes in stems/fruits, sawdust-like frass

**NUTRIENT DEFICIENCIES:**
- Nitrogen: Overall yellowing starting from older leaves
- Phosphorus: Purple/red coloration, stunted growth
- Potassium: Brown leaf edges, weak stems
- Iron: Interveinal chlorosis on new leaves
- Magnesium: Interveinal chlorosis on older leaves

Analyze with EXPERT PRECISION:
{{
    "disease_name": "specific disease/condition identified",
    "confidence": 85,
    "severity": "low/medium/high",
    "symptoms_observed": "detailed symptoms matching the condition",
    "immediate_action": "most urgent action to take TODAY",
    "remedy": "DETAILED treatment with specific products and doses. Include both chemical and organic options.",
    "prevention_tips": ["tip 1 - specific", "tip 2 - actionable", "tip 3 - practical"],
    "follow_up": "specific monitoring plan with timeline",
    "estimated_recovery_time": "X days/weeks with proper treatment",
    "warning_signs": "when to seek professional help"
}}

If crop appears HEALTHY, respond with disease_name: "Healthy Crop" and provide maintenance tips.
Be SPECIFIC and PRACTICAL - farmers need exact dosages and product names."""
        else:
            analysis_prompt = f"""{context_str}
=== TEXT-BASED CROP DIAGNOSIS ===

Farmer's Description: "{caption}"
Crops Grown: {crops_list or 'Unknown'}

Based on the description, analyze potential diseases/conditions and provide:
{{
    "disease_name": "most likely condition based on symptoms described",
    "confidence": 75,
    "severity": "low/medium/high",
    "analysis": "detailed explanation of what's likely happening",
    "remedy": "specific treatment steps with product names and dosages",
    "prevention_tips": ["actionable tip 1", "tip 2", "tip 3"],
    "immediate_action": "what to do RIGHT NOW",
    "follow_up": "monitoring and follow-up plan",
    "additional_questions": "what info would help confirm diagnosis"
}}

Ask yourself: What disease/pest/deficiency matches these symptoms?
Be SPECIFIC - avoid generic advice."""

        response = call_gemini(
            analysis_prompt,
            "You are an expert agricultural pathologist. Provide PRECISE diagnoses with SPECIFIC remedies. Include exact chemical names and dosages. Always respond with valid JSON only, no markdown.",
            temperature=0.4,
            max_tokens=1800
        )
        
        response_text = response.strip()
        
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
        raise


async def analyze_disease(image_data: str, caption: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Main disease analysis function with crop-based routing.
    Uses Gemini for all analysis.
    """
    try:
        user_crops = user_context.get("crops", []) if user_context else []
        crop_type = await identify_crop_type(user_crops, image_data)
        
        logger.info(f"Identified crop type: {crop_type}")
        
        if crop_type == "paddy":
            location = user_context.get("farm_location", "") if user_context else ""
            result = await analyze_paddy_disease(image_data or "", caption or "", location)
        else:
            result = await analyze_multimodal_disease(image_data, caption, user_context)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in main disease analysis: {e}", exc_info=True)
        raise
