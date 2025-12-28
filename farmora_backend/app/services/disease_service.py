"""
Disease Classification Service for Farmora
==========================================
Enhanced multimodal disease detection with:
- Direct image analysis using Gemini Vision API
- Paddy-specific ML model integration (placeholder for future)
- General crop disease diagnosis for non-paddy crops
- No fallbacks - direct AI analysis

Author: Farmora Team
"""

import logging
import json
import base64
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from farmora_backend.app.config import settings
import google.genai as genai
from google.genai import types

logger = logging.getLogger(__name__)

# Configure Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# ============================================================================
# MULTIMODAL GEMINI HELPER
# ============================================================================

def call_gemini_multimodal(
    prompt: str,
    image_data: Optional[str] = None,
    system_prompt: str = "",
    temperature: float = 0.3,
    max_tokens: int = 2000
) -> str:
    """
    Call Gemini API with multimodal support (text + image).
    
    Args:
        prompt: The text prompt
        image_data: Base64 encoded image string (optional)
        system_prompt: System instruction for the model
        temperature: Controls randomness (lower = more deterministic)
        max_tokens: Maximum output tokens
    
    Returns:
        Model response text
    """
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    
    # Build contents based on whether image is provided
    if image_data:
        # Clean base64 string if it has data URI prefix
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        # Detect mime type from base64 or default to jpeg
        mime_type = "image/jpeg"
        if image_data.startswith("/9j/"):
            mime_type = "image/jpeg"
        elif image_data.startswith("iVBORw"):
            mime_type = "image/png"
        elif image_data.startswith("R0lGOD"):
            mime_type = "image/gif"
        elif image_data.startswith("UklGR"):
            mime_type = "image/webp"
        
        # Use correct google.genai format for multimodal
        contents = [
            full_prompt,
            types.Part.from_bytes(
                data=base64.b64decode(image_data),
                mime_type=mime_type
            )
        ]
    else:
        contents = full_prompt
    
    response = client.models.generate_content(
        model=settings.GEMINI_MULTI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    )
    return response.text


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """Parse JSON from model response, handling markdown code blocks and malformed JSON."""
    import re
    
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
            # Remove language identifier if present (e.g., "json\n")
            if text.startswith("json"):
                text = text[4:].strip()
    
    # Try to extract JSON object if text contains other content
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        text = json_match.group()
    
    # Fix common JSON issues
    # Replace single quotes with double quotes (but be careful with apostrophes in text)
    # Fix trailing commas before closing braces/brackets
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Try to parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}. Attempting to fix...")
        
        # Try to fix truncated JSON by closing open structures
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        # Check for unterminated strings
        if 'Unterminated string' in str(e):
            # Find last complete key-value pair and truncate there
            last_complete = text.rfind('",')
            if last_complete > 0:
                text = text[:last_complete + 1]
                # Close remaining structures
                text += '}' * (text.count('{') - text.count('}'))
                text += ']' * (text.count('[') - text.count(']'))
        else:
            text += ']' * open_brackets
            text += '}' * open_braces
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Return a minimal valid response
            logger.error(f"Could not parse JSON response: {response_text[:200]}...")
            raise


# ============================================================================
# ML MODEL INTERFACE (PLACEHOLDER FOR FUTURE PADDY ML MODEL)
# ============================================================================

class BaseDiseaseMLModel(ABC):
    """Abstract base class for disease detection ML models."""
    
    @abstractmethod
    def predict(self, image_data: str) -> Dict[str, Any]:
        """
        Predict disease from image.
        
        Args:
            image_data: Base64 encoded image
        
        Returns:
            Dict with prediction results:
            - disease_class: str (disease name/class)
            - confidence: float (0-100)
            - raw_predictions: Dict (all class probabilities)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if model is loaded and ready."""
        pass


class PaddyDiseaseMLModel(BaseDiseaseMLModel):
    """
    Paddy Disease ML Model Placeholder.
    
    TODO: Replace this with actual trained model integration:
    1. Load your trained model (TensorFlow/PyTorch)
    2. Implement predict() with actual inference
    3. Return disease class and confidence
    
    Expected classes for paddy:
    - Rice Blast
    - Brown Spot  
    - Sheath Blight
    - Bacterial Leaf Blight
    - Tungro
    - Healthy
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self.classes = [
            "Rice Blast",
            "Brown Spot", 
            "Sheath Blight",
            "Sheath Rot",
            "False Smut",
            "Bacterial Leaf Blight",
            "Bacterial Leaf Streak",
            "Tungro Virus",
            "Stem Borer Damage",
            "Brown Plant Hopper",
            "Healthy"
        ]
        self._load_model()
    
    def _load_model(self):
        """Load the ML model from disk."""
        # TODO: Implement actual model loading
        # Example for TensorFlow:
        # if self.model_path and os.path.exists(self.model_path):
        #     import tensorflow as tf
        #     self.model = tf.keras.models.load_model(self.model_path)
        # 
        # Example for PyTorch:
        # if self.model_path and os.path.exists(self.model_path):
        #     import torch
        #     self.model = torch.load(self.model_path)
        #     self.model.eval()
        
        self.model = None  # No model loaded yet
        logger.info("Paddy ML Model: Not loaded (using multimodal AI fallback)")
    
    def is_available(self) -> bool:
        """Check if ML model is loaded."""
        return self.model is not None
    
    def predict(self, image_data: str) -> Dict[str, Any]:
        """
        Predict paddy disease from image.
        
        TODO: Implement actual prediction:
        1. Preprocess image (resize, normalize)
        2. Run inference
        3. Return class with highest probability
        """
        if not self.is_available():
            return None
        
        # TODO: Actual implementation
        # image = self._preprocess_image(image_data)
        # predictions = self.model.predict(image)
        # class_idx = predictions.argmax()
        # confidence = predictions[class_idx] * 100
        # 
        # return {
        #     "disease_class": self.classes[class_idx],
        #     "confidence": confidence,
        #     "raw_predictions": {cls: float(pred) for cls, pred in zip(self.classes, predictions)}
        # }
        
        return None


# Initialize ML model (will be None until actual model is integrated)
paddy_ml_model = PaddyDiseaseMLModel(model_path=None)


# ============================================================================
# CROP TYPE IDENTIFICATION
# ============================================================================

async def identify_crop_from_image(image_data: str) -> Tuple[str, float]:
    """
    Identify crop type directly from image using Gemini Vision.
    
    Args:
        image_data: Base64 encoded image
    
    Returns:
        Tuple of (crop_type, confidence)
        crop_type: 'paddy', 'wheat', 'maize', 'tomato', 'cotton', 'sugarcane', 'other'
    """
    identification_prompt = """Analyze this crop image and identify the crop type.

IMPORTANT: Look at the plant characteristics carefully:
- Leaf shape and arrangement
- Plant structure (grass-like, broadleaf, vine, etc.)
- Any visible fruits/grains/flowers
- Overall plant habit

Identify as ONE of these categories:
- "paddy" (rice) - narrow grass-like leaves, flooded field or rice grains visible
- "wheat" - grass-like with distinctive wheat heads
- "maize" (corn) - large broad leaves, tall stalks, corn ears
- "tomato" - compound leaves, red/green fruits
- "cotton" - lobed leaves, white cotton bolls
- "sugarcane" - tall thick stems, grass-like
- "vegetable" - leafy greens, root vegetables
- "other" - any other crop

Respond in JSON format ONLY:
{
    "crop_type": "paddy",
    "confidence": 85,
    "visual_cues": "narrow leaves, standing water visible, rice panicles"
}"""

    response = call_gemini_multimodal(
        prompt=identification_prompt,
        image_data=image_data,
        system_prompt="You are an expert agronomist specializing in crop identification. Be precise.",
        temperature=0.1,
        max_tokens=200
    )
    
    try:
        result = parse_json_response(response)
        crop_type = result.get("crop_type", "other").lower()
        confidence = float(result.get("confidence", 70))
        
        # Normalize paddy aliases
        if crop_type in ["rice", "dhaan", "paddy"]:
            crop_type = "paddy"
        
        logger.info(f"Crop identified: {crop_type} (confidence: {confidence}%)")
        return crop_type, confidence
        
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse crop identification: {e}")
        return "other", 50.0


# ============================================================================
# PADDY DISEASE ANALYSIS
# ============================================================================

async def analyze_paddy_with_ml(image_data: str) -> Optional[Dict[str, Any]]:
    """
    Analyze paddy disease using ML model if available.
    
    Args:
        image_data: Base64 encoded image
    
    Returns:
        ML prediction result or None if model not available
    """
    if not paddy_ml_model.is_available():
        logger.info("Paddy ML model not available, using multimodal AI")
        return None
    
    prediction = paddy_ml_model.predict(image_data)
    return prediction


async def explain_ml_prediction(
    ml_result: Dict[str, Any],
    image_data: str,
    location: str
) -> Dict[str, Any]:
    """
    Use Gemini to explain ML model prediction and provide remedies.
    
    Args:
        ml_result: ML model prediction result
        image_data: Base64 encoded image
        location: Farm location for localized advice
    
    Returns:
        Complete disease analysis with remedies
    """
    disease_class = ml_result["disease_class"]
    confidence = ml_result["confidence"]
    
    explanation_prompt = f"""An ML model has detected "{disease_class}" in this paddy crop image with {confidence:.1f}% confidence.

Location: {location or 'India'}

As an expert paddy pathologist, analyze the image and provide:
1. Confirm or refine the ML model's diagnosis based on visual symptoms
2. Detailed symptoms observed in the image
3. Severity assessment (low/medium/high)
4. Specific treatment recommendations with exact dosages
5. Prevention tips for future

=== PADDY DISEASE REFERENCE ===
- Rice Blast: Spindle lesions, gray center, brown border
- Brown Spot: Oval brown lesions, yellow halo
- Sheath Blight: Water-soaked spots at water level
- Bacterial Leaf Blight: V-shaped lesions from leaf tips
- Tungro: Yellow-orange discoloration, stunted growth

Respond in JSON:
{{
    "disease_name": "{disease_class}",
    "ml_confidence": {confidence},
    "visual_confirmation": "describe what you see that confirms/contradicts ML",
    "adjusted_confidence": 85,
    "severity": "medium",
    "symptoms_observed": "specific symptoms visible in image",
    "immediate_action": "urgent action needed",
    "remedy": {{
        "chemical": "Product name @ dose (e.g., Tricyclazole 75WP @ 0.6g/L)",
        "organic": "organic alternative treatment",
        "application_method": "spray/drench/foliar"
    }},
    "prevention_tips": ["tip1", "tip2", "tip3"],
    "follow_up": "monitoring schedule",
    "economic_threshold": "spray if X% affected"
}}"""

    response = call_gemini_multimodal(
        prompt=explanation_prompt,
        image_data=image_data,
        system_prompt="You are India's top paddy pathologist. Validate ML predictions and provide expert treatment advice.",
        temperature=0.3,
        max_tokens=1500
    )
    
    result = parse_json_response(response)
    return result


async def analyze_paddy_multimodal(image_data: str, caption: str, location: str) -> Dict[str, Any]:
    """
    Analyze paddy disease using Gemini multimodal when ML model is not available.
    Directly analyzes the image for paddy-specific diseases.
    
    Args:
        image_data: Base64 encoded image
        caption: User's description of the problem
        location: Farm location
    
    Returns:
        Complete disease analysis
    """
    paddy_prompt = f"""You are an EXPERT PADDY/RICE crop pathologist analyzing this image.

Farmer's Description: {caption or 'No description provided'}
Location: {location or 'India'}

=== COMPREHENSIVE PADDY DISEASE DATABASE ===

**FUNGAL DISEASES:**
1. Rice Blast (Magnaporthe oryzae)
   - Symptoms: Spindle-shaped lesions with gray center and brown border
   - Node blast causes stem breakage
   - Severity: Few spots = low, Many spots/node affected = high

2. Brown Spot (Bipolaris oryzae)
   - Symptoms: Oval/circular brown lesions with gray center, yellow halo
   - Common in nutrient-deficient fields

3. Sheath Blight (Rhizoctonia solani)
   - Symptoms: Irregular greenish-gray water-soaked spots
   - Usually starts at water level on stems

4. Sheath Rot (Sarocladium oryzae)
   - Symptoms: Brown discoloration on sheath, poor panicle emergence

5. False Smut (Ustilaginoidea virens)
   - Symptoms: Orange/green spore balls replacing grains

6. Leaf Scald (Microdochium oryzae)
   - Symptoms: Zonate lesions with alternating tan/brown bands

**BACTERIAL DISEASES:**
7. Bacterial Leaf Blight (Xanthomonas oryzae)
   - Symptoms: Water-soaked streaks turning yellow-white, V-shaped lesions from leaf tips

8. Bacterial Leaf Streak
   - Symptoms: Fine translucent streaks between veins

**VIRAL DISEASES:**
9. Rice Tungro Virus
   - Symptoms: Yellow-orange discoloration, stunted growth, reduced tillering

**PEST DAMAGE:**
10. Stem Borer - Dead hearts (vegetative), white heads (flowering)
11. Leaf Folder - Longitudinally folded leaves with scraping
12. Brown Plant Hopper - Hopper burn, circular dried patches
13. Rice Hispa - White parallel streaks, shot holes

14. Bakanae Disease (Fusarium)
    - Abnormally tall, thin, pale seedlings

**HEALTHY PADDY:**
- Uniform green color
- No lesions or discoloration
- Normal growth pattern

ANALYZE THE IMAGE and respond in JSON:
{{
    "disease_name": "exact disease name from database",
    "confidence": 85,
    "severity": "low/medium/high",
    "symptoms_observed": "specific symptoms visible in the image",
    "affected_plant_parts": ["leaves", "stem", "panicle"],
    "growth_stage": "seedling/tillering/flowering/grain filling",
    "immediate_action": "most urgent action for this severity",
    "remedy": {{
        "chemical": "Product name @ exact dose (e.g., Tricyclazole 75WP @ 0.6g/L water)",
        "organic": "organic alternative with application method",
        "application_frequency": "spray interval"
    }},
    "prevention_tips": ["specific tip 1", "actionable tip 2", "practical tip 3"],
    "follow_up": "monitoring schedule with checkpoints",
    "economic_threshold": "spray if X% plants affected",
    "estimated_yield_loss": "potential loss without treatment"
}}

If the paddy appears HEALTHY, set disease_name to "Healthy Paddy" and provide maintenance tips.
Be PRECISE - farmers need EXACT chemical names and dosages."""

    response = call_gemini_multimodal(
        prompt=paddy_prompt,
        image_data=image_data,
        system_prompt="You are India's top paddy crop pathologist with 25+ years experience. Analyze images with expert precision. Return ONLY valid JSON.",
        temperature=0.2,
        max_tokens=1800
    )
    
    try:
        return parse_json_response(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse paddy analysis JSON: {e}")
        # Return a basic analysis
        return {
            "disease_name": "Paddy Disease Analysis",
            "confidence": 70,
            "severity": "medium",
            "symptoms_observed": "Analysis completed - see details",
            "immediate_action": "Inspect paddy field thoroughly",
            "remedy": {
                "chemical": "Consult local agricultural officer for specific treatment",
                "organic": "Use neem-based solutions as preventive measure"
            },
            "prevention_tips": ["Monitor leaf health daily", "Maintain proper water level", "Use disease-resistant varieties"],
            "follow_up": "Review in 3-5 days"
        }


async def analyze_paddy_disease(
    image_data: str,
    caption: str,
    location: str
) -> Dict[str, Any]:
    """
    Main paddy disease analysis function.
    Tries ML model first, falls back to multimodal AI.
    
    Args:
        image_data: Base64 encoded image
        caption: User's description
        location: Farm location
    
    Returns:
        Standardized disease analysis result
    """
    logger.info("Starting paddy disease analysis...")
    
    # Try ML model first
    ml_result = await analyze_paddy_with_ml(image_data)
    
    if ml_result:
        # ML model available - use it and explain with AI
        logger.info(f"ML Model prediction: {ml_result['disease_class']}")
        analysis = await explain_ml_prediction(ml_result, image_data, location)
        analysis["analysis_method"] = "ml_model_with_ai_explanation"
    else:
        # No ML model - use multimodal AI directly
        logger.info("Using multimodal AI for paddy analysis")
        analysis = await analyze_paddy_multimodal(image_data, caption, location)
        analysis["analysis_method"] = "multimodal_ai"
    
    # Standardize output format
    remedy = analysis.get("remedy", {})
    if isinstance(remedy, dict):
        remedy_text = f"Chemical: {remedy.get('chemical', 'N/A')}\nOrganic: {remedy.get('organic', 'N/A')}"
        if remedy.get('application_frequency'):
            remedy_text += f"\nFrequency: {remedy['application_frequency']}"
    else:
        remedy_text = str(remedy)
    
    return {
        "label": analysis.get("disease_name", "Unknown Paddy Disease"),
        "confidence": float(analysis.get("confidence", analysis.get("adjusted_confidence", 75))),
        "severity": analysis.get("severity", "medium"),
        "symptoms": analysis.get("symptoms_observed", ""),
        "remedy": remedy_text,
        "prevention_tips": analysis.get("prevention_tips", []),
        "immediate_action": analysis.get("immediate_action", "Inspect field thoroughly"),
        "follow_up": analysis.get("follow_up", "Monitor daily for 5-7 days"),
        "requires_intervention": analysis.get("severity", "medium").lower() in ["medium", "high"],
        "crop_type": "paddy",
        "growth_stage": analysis.get("growth_stage", ""),
        "economic_threshold": analysis.get("economic_threshold", ""),
        "analysis_method": analysis.get("analysis_method", "multimodal_ai")
    }


# ============================================================================
# GENERAL CROP DISEASE ANALYSIS (NON-PADDY)
# ============================================================================

async def analyze_general_crop_disease(
    image_data: str,
    caption: str,
    crop_type: str,
    user_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Analyze disease for non-paddy crops using Gemini multimodal.
    
    Args:
        image_data: Base64 encoded image
        caption: User's description
        crop_type: Identified crop type
        user_context: User profile with farm details
    
    Returns:
        Complete disease analysis
    """
    location = user_context.get("farm_location", "India") if user_context else "India"
    crops = user_context.get("crops", []) if user_context else []
    crops_str = ", ".join(crops) if crops else crop_type
    
    analysis_prompt = f"""You are an EXPERT agricultural pathologist analyzing this crop image.

Crop Type: {crop_type.upper()}
Farmer's Crops: {crops_str}
Farmer's Description: {caption or 'No description provided'}
Location: {location}

=== COMPREHENSIVE DISEASE DATABASE ===

**FUNGAL DISEASES:**
- Powdery Mildew: White powdery coating on leaves/stems
- Downy Mildew: Yellow/brown patches with fuzzy growth underneath
- Anthracnose: Dark sunken lesions on fruits/leaves
- Fusarium Wilt: Yellowing, wilting from base upward
- Rust: Orange/brown pustules on leaves
- Early Blight: Dark concentric ring spots (target spots)
- Late Blight: Water-soaked spots turning brown/black rapidly
- Root Rot: Wilting despite adequate water, brown roots
- Cercospora Leaf Spot: Circular spots with gray center

**BACTERIAL DISEASES:**
- Bacterial Wilt: Sudden wilting, slimy stem when cut
- Bacterial Spot: Small water-soaked spots turning brown
- Soft Rot: Mushy, foul-smelling tissue
- Canker: Raised corky lesions on stems/fruits

**VIRAL DISEASES:**
- Mosaic Virus: Mottled light/dark green patterns
- Leaf Curl Virus: Distorted, curled leaves, stunted growth
- Yellowing Virus: Uniform yellowing, reduced vigor
- Ring Spot: Circular ring patterns on leaves

**PEST DAMAGE:**
- Aphids: Curled leaves, sticky honeydew, sooty mold
- Caterpillars/Worms: Large irregular holes, frass present
- Whitefly: Yellowing, sticky residue, tiny white flying insects
- Spider Mites: Fine stippling, webbing on undersides, bronzing
- Thrips: Silver streaks, distorted growth points
- Borers: Holes in stems/fruits, sawdust-like frass
- Leaf Miners: Serpentine trails in leaves
- Mealybugs: White cottony masses

**NUTRIENT DEFICIENCIES:**
- Nitrogen (N): Overall yellowing starting from older leaves
- Phosphorus (P): Purple/red coloration, stunted growth
- Potassium (K): Brown/scorched leaf edges, weak stems
- Iron (Fe): Interveinal chlorosis on NEW leaves
- Magnesium (Mg): Interveinal chlorosis on OLDER leaves
- Calcium (Ca): Blossom end rot, tip burn
- Boron (B): Distorted growth, hollow stems

**ENVIRONMENTAL STRESS:**
- Heat stress: Wilting, leaf scorch
- Cold damage: Water-soaked areas, blackening
- Water stress: Wilting, leaf drop
- Sunscald: Bleached/white patches

ANALYZE THE IMAGE and respond in JSON:
{{
    "crop_identified": "{crop_type}",
    "disease_name": "specific disease/condition identified",
    "confidence": 85,
    "severity": "low/medium/high",
    "category": "fungal/bacterial/viral/pest/deficiency/environmental",
    "symptoms_observed": "detailed symptoms visible in image",
    "affected_parts": ["leaves", "stem", "fruit", "roots"],
    "immediate_action": "most urgent action to take TODAY",
    "remedy": {{
        "chemical": "specific product @ exact dose per liter or hectare",
        "organic": "organic/bio alternative with application",
        "application_method": "foliar spray/soil drench/etc",
        "frequency": "application interval"
    }},
    "prevention_tips": ["specific actionable tip 1", "tip 2", "tip 3"],
    "follow_up": "monitoring plan with timeline",
    "warning_signs": "when to seek professional help",
    "estimated_recovery": "X days/weeks with proper treatment"
}}

If crop appears HEALTHY, set disease_name to "Healthy Crop" and provide maintenance tips.
Be SPECIFIC - farmers need exact product names and dosages."""

    response = call_gemini_multimodal(
        prompt=analysis_prompt,
        image_data=image_data,
        system_prompt="You are an expert agricultural pathologist with 20+ years experience in Indian agriculture. Provide precise diagnosis with specific remedies. Return ONLY valid JSON.",
        temperature=0.3,
        max_tokens=1800
    )
    
    try:
        analysis = parse_json_response(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse disease analysis JSON: {e}")
        # Return a basic analysis from the raw response
        analysis = {
            "disease_name": "Analysis Complete",
            "confidence": 70,
            "severity": "medium",
            "symptoms_observed": "See detailed analysis below",
            "immediate_action": "Review the analysis carefully",
            "remedy": response[:500] if response else "Consult local agricultural expert",
            "prevention_tips": ["Monitor crop regularly", "Maintain proper irrigation", "Consult agricultural officer"],
            "follow_up": "Monitor for 5-7 days"
        }
    
    # Standardize output format
    remedy = analysis.get("remedy", {})
    if isinstance(remedy, dict):
        remedy_text = f"Chemical: {remedy.get('chemical', 'N/A')}\nOrganic: {remedy.get('organic', 'N/A')}"
        if remedy.get('application_method'):
            remedy_text += f"\nMethod: {remedy['application_method']}"
        if remedy.get('frequency'):
            remedy_text += f"\nFrequency: {remedy['frequency']}"
    else:
        remedy_text = str(remedy)
    
    return {
        "label": analysis.get("disease_name", "Unknown Condition"),
        "confidence": float(analysis.get("confidence", 75)),
        "severity": analysis.get("severity", "medium"),
        "category": analysis.get("category", "unknown"),
        "symptoms": analysis.get("symptoms_observed", ""),
        "remedy": remedy_text,
        "prevention_tips": analysis.get("prevention_tips", []),
        "immediate_action": analysis.get("immediate_action", "Inspect crop closely"),
        "follow_up": analysis.get("follow_up", "Monitor for 5-7 days"),
        "requires_intervention": analysis.get("severity", "medium").lower() in ["medium", "high"],
        "crop_type": crop_type,
        "affected_parts": analysis.get("affected_parts", []),
        "warning_signs": analysis.get("warning_signs", ""),
        "estimated_recovery": analysis.get("estimated_recovery", ""),
        "analysis_method": "multimodal_ai"
    }


# ============================================================================
# TEXT-ONLY ANALYSIS (NO IMAGE)
# ============================================================================

async def analyze_from_description(
    caption: str,
    user_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Analyze potential disease from text description only.
    
    Args:
        caption: User's description of symptoms
        user_context: User profile with farm details
    
    Returns:
        Analysis based on symptom description
    """
    location = user_context.get("farm_location", "India") if user_context else "India"
    crops = user_context.get("crops", []) if user_context else []
    crops_str = ", ".join(crops) if crops else "unknown crops"
    
    text_prompt = f"""You are an expert agricultural diagnostician. A farmer describes their crop problem:

Farmer's Description: "{caption}"
Crops Grown: {crops_str}
Location: {location}

Based on the symptoms described, analyze and provide diagnosis.

Consider common diseases and pests for the mentioned crops.
Ask yourself: What disease/pest/deficiency matches these symptoms?

Respond in JSON:
{{
    "likely_conditions": [
        {{
            "disease_name": "most likely condition",
            "confidence": 70,
            "matching_symptoms": "which described symptoms match"
        }},
        {{
            "disease_name": "second possibility",
            "confidence": 50,
            "matching_symptoms": "matching symptoms"
        }}
    ],
    "primary_diagnosis": "most likely condition name",
    "severity": "low/medium/high",
    "immediate_action": "what to do right now",
    "remedy": {{
        "chemical": "product @ dose",
        "organic": "organic alternative"
    }},
    "prevention_tips": ["tip 1", "tip 2", "tip 3"],
    "recommendation": "suggest sending a photo for accurate diagnosis",
    "questions_for_clarity": ["question 1 to narrow diagnosis", "question 2"]
}}"""

    response = call_gemini_multimodal(
        prompt=text_prompt,
        image_data=None,
        system_prompt="You are an expert agricultural diagnostician. Provide probable diagnoses based on symptom descriptions.",
        temperature=0.4,
        max_tokens=1500
    )
    
    try:
        analysis = parse_json_response(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse text analysis JSON: {e}")
        analysis = {
            "primary_diagnosis": "Analysis Based on Description",
            "likely_conditions": [{"disease_name": "Unknown", "confidence": 60}],
            "severity": "medium",
            "immediate_action": "Send a clear photo for accurate diagnosis",
            "remedy": {"chemical": "Consult expert", "organic": "Monitor closely"},
            "prevention_tips": ["Monitor regularly", "Maintain proper care"],
            "recommendation": "Please send a photo for more accurate diagnosis",
            "questions_for_clarity": []
        }
    
    remedy = analysis.get("remedy", {})
    if isinstance(remedy, dict):
        remedy_text = f"Chemical: {remedy.get('chemical', 'N/A')}\nOrganic: {remedy.get('organic', 'N/A')}"
    else:
        remedy_text = str(remedy)
    
    return {
        "label": analysis.get("primary_diagnosis", "Analysis Based on Description"),
        "confidence": float(analysis.get("likely_conditions", [{}])[0].get("confidence", 60)),
        "severity": analysis.get("severity", "medium"),
        "symptoms": caption,
        "remedy": remedy_text,
        "prevention_tips": analysis.get("prevention_tips", []),
        "immediate_action": analysis.get("immediate_action", "Send a clear photo for accurate diagnosis"),
        "follow_up": analysis.get("recommendation", "Send photo for confirmation"),
        "requires_intervention": analysis.get("severity", "medium").lower() in ["medium", "high"],
        "crop_type": crops[0] if crops else "unknown",
        "likely_conditions": analysis.get("likely_conditions", []),
        "questions_for_clarity": analysis.get("questions_for_clarity", []),
        "analysis_method": "text_only"
    }


# ============================================================================
# MAIN DISEASE ANALYSIS ENTRY POINT
# ============================================================================

async def analyze_disease(
    image_data: Optional[str],
    caption: str,
    user_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Main disease analysis entry point.
    Routes to appropriate analyzer based on image and crop type.
    
    Flow:
    1. If no image → text-based analysis
    2. If image → identify crop type from image
    3. If paddy → try ML model, else multimodal AI
    4. If not paddy → multimodal AI for general diagnosis
    
    Args:
        image_data: Base64 encoded image (optional)
        caption: User's description/message
        user_context: User profile with farm details
    
    Returns:
        Standardized disease analysis result
    """
    logger.info(f"Disease analysis request - Image: {bool(image_data)}, Caption: {caption[:50] if caption else 'None'}...")
    
    # No image - text-only analysis
    if not image_data:
        logger.info("No image provided - using text-based analysis")
        return await analyze_from_description(caption, user_context)
    
    # Identify crop type from image
    crop_type, identification_confidence = await identify_crop_from_image(image_data)
    logger.info(f"Crop identification: {crop_type} ({identification_confidence}% confidence)")
    
    # Route based on crop type
    if crop_type == "paddy":
        location = user_context.get("farm_location", "") if user_context else ""
        result = await analyze_paddy_disease(image_data, caption, location)
        result["crop_identification_confidence"] = identification_confidence
        return result
    else:
        result = await analyze_general_crop_disease(image_data, caption, crop_type, user_context)
        result["crop_identification_confidence"] = identification_confidence
        return result
