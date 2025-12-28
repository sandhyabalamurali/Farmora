"""
Disease Classification Service - Farmora
Direct multimodal AI analysis for crop disease detection
"""

import logging
import base64
from typing import Dict, Any, Optional
from farmora_backend.app.config import settings
import google.genai as genai
from google.genai import types

logger = logging.getLogger(__name__)
client = genai.Client(api_key=settings.GEMINI_API_KEY)


def analyze_with_gemini(prompt: str, image_data: Optional[str] = None) -> str:
    """Send prompt (with optional image) to Gemini and get response."""
    
    if image_data:
        # Clean base64 if has data URI prefix
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        # Detect mime type
        mime = "image/jpeg"
        if image_data.startswith("iVBORw"):
            mime = "image/png"
        elif image_data.startswith("UklGR"):
            mime = "image/webp"
        
        contents = [
            prompt,
            types.Part.from_bytes(data=base64.b64decode(image_data), mime_type=mime)
        ]
    else:
        contents = prompt
    
    response = client.models.generate_content(
        model=settings.GEMINI_MULTI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=2500)
    )
    return response.text


async def analyze_disease(
    image_data: Optional[str],
    caption: str,
    user_context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Main disease analysis - sends image directly to multimodal AI.
    Returns structured diagnosis with remedies.
    """
    
    location = user_context.get("farm_location", "India") if user_context else "India"
    crops = user_context.get("crops", []) if user_context else []
    crops_str = ", ".join(crops) if crops else "crops"
    
    if image_data:
        prompt = f"""You are an expert agricultural pathologist. Analyze this crop image.

Farmer info: Location: {location}, Crops: {crops_str}
Farmer says: "{caption or 'Please check my crop'}"

Analyze the image and provide:

1. **CROP TYPE**: What crop is this? (paddy/rice, wheat, maize, tomato, cotton, vegetable, other)

2. **DIAGNOSIS**: 
   - Disease/Condition name (be specific - e.g., "Rice Blast", "Bacterial Leaf Blight", "Nitrogen Deficiency")
   - If healthy, say "Healthy"

3. **CONFIDENCE**: Your confidence level (low/medium/high)

4. **SEVERITY**: If diseased (low/medium/high)

5. **SYMPTOMS**: What specific symptoms do you observe in this image?

6. **TREATMENT**:
   - Chemical: Specific product name with exact dosage (e.g., "Tricyclazole 75WP @ 0.6g/L")
   - Organic: Natural alternative treatment
   - Method: How to apply (spray/drench/foliar)

7. **PREVENTION**: 3 specific tips to prevent this in future

8. **URGENT ACTION**: What should farmer do RIGHT NOW?

Be specific and practical. Farmers need exact product names and dosages, not generic advice."""

    else:
        # Text-only analysis
        prompt = f"""You are an expert agricultural diagnostician.

Farmer info: Location: {location}, Crops: {crops_str}
Farmer describes: "{caption}"

Based on symptoms described, provide:

1. **LIKELY DIAGNOSIS**: Most probable disease/pest/deficiency

2. **CONFIDENCE**: How confident without seeing image (low/medium)

3. **SEVERITY**: Estimated severity (low/medium/high)

4. **TREATMENT**:
   - Chemical: Specific product with dosage
   - Organic: Natural alternative

5. **URGENT ACTION**: What to do immediately

6. **RECOMMENDATION**: Suggest sending a photo for accurate diagnosis

Be helpful but note uncertainty without image."""

    try:
        response = analyze_with_gemini(prompt, image_data)
        logger.info(f"Disease analysis completed. Response length: {len(response)}")
        
        # Parse the response into structured format
        return parse_analysis_response(response, image_data is not None)
        
    except Exception as e:
        logger.error(f"Disease analysis error: {e}")
        return {
            "label": "Analysis Error",
            "confidence": 0,
            "severity": "unknown",
            "symptoms": "",
            "remedy": f"Error occurred: {str(e)}. Please try again or consult local agricultural officer.",
            "prevention_tips": ["Try uploading a clearer image", "Describe symptoms in detail"],
            "immediate_action": "Consult local agricultural expert",
            "requires_intervention": True,
            "crop_type": "unknown",
            "analysis_method": "error"
        }


def parse_analysis_response(response: str, has_image: bool) -> Dict[str, Any]:
    """Parse AI response into structured format."""
    
    text = response.strip()
    
    # Extract sections from markdown-style response
    def extract_section(text: str, markers: list) -> str:
        for marker in markers:
            if marker in text:
                start = text.find(marker) + len(marker)
                # Find next section or end
                next_section = len(text)
                for m in ["**", "\n\n1.", "\n\n2.", "\n\n3.", "\n\n4.", "\n\n5.", "\n\n6.", "\n\n7.", "\n\n8."]:
                    idx = text.find(m, start + 5)
                    if idx > 0 and idx < next_section:
                        next_section = idx
                return text[start:next_section].strip().strip("*:").strip()
        return ""
    
    # Extract crop type
    crop_section = extract_section(text, ["**CROP TYPE**", "CROP TYPE:", "Crop Type:"])
    crop_type = "other"
    for crop in ["paddy", "rice", "wheat", "maize", "corn", "tomato", "cotton", "sugarcane", "vegetable"]:
        if crop in crop_section.lower():
            crop_type = "paddy" if crop in ["paddy", "rice"] else crop
            break
    
    # Extract diagnosis
    diagnosis = extract_section(text, ["**DIAGNOSIS**", "DIAGNOSIS:", "Diagnosis:"])
    if not diagnosis:
        diagnosis = extract_section(text, ["**LIKELY DIAGNOSIS**", "LIKELY DIAGNOSIS:"])
    
    # Determine if healthy
    is_healthy = "healthy" in diagnosis.lower() and "unhealthy" not in diagnosis.lower()
    
    # Extract confidence
    confidence_text = extract_section(text, ["**CONFIDENCE**", "CONFIDENCE:"])
    confidence = 85 if "high" in confidence_text.lower() else (70 if "medium" in confidence_text.lower() else 50)
    
    # Extract severity
    severity_text = extract_section(text, ["**SEVERITY**", "SEVERITY:"])
    severity = "low"
    if "high" in severity_text.lower():
        severity = "high"
    elif "medium" in severity_text.lower() or "moderate" in severity_text.lower():
        severity = "medium"
    
    # Extract symptoms
    symptoms = extract_section(text, ["**SYMPTOMS**", "SYMPTOMS:"])
    
    # Extract treatment
    treatment = extract_section(text, ["**TREATMENT**", "TREATMENT:"])
    
    # Extract prevention
    prevention = extract_section(text, ["**PREVENTION**", "PREVENTION:"])
    prevention_tips = [tip.strip().strip("-•").strip() for tip in prevention.split("\n") if tip.strip() and len(tip.strip()) > 5][:3]
    if not prevention_tips:
        prevention_tips = ["Monitor crop regularly", "Maintain proper irrigation", "Use disease-resistant varieties"]
    
    # Extract urgent action
    urgent = extract_section(text, ["**URGENT ACTION**", "URGENT ACTION:", "**IMMEDIATE ACTION**"])
    if not urgent:
        urgent = "Monitor crop closely and take action based on diagnosis"
    
    # Build remedy text
    remedy = treatment if treatment else "Consult local agricultural officer for specific treatment recommendations"
    
    return {
        "label": diagnosis.split("\n")[0][:100] if diagnosis else ("Healthy Crop" if is_healthy else "See Analysis"),
        "confidence": confidence,
        "severity": "none" if is_healthy else severity,
        "symptoms": symptoms[:500] if symptoms else "",
        "remedy": remedy[:1000],
        "prevention_tips": prevention_tips,
        "immediate_action": urgent[:300],
        "requires_intervention": not is_healthy and severity in ["medium", "high"],
        "crop_type": crop_type,
        "full_analysis": text,  # Include full response for frontend to display
        "analysis_method": "multimodal_ai" if has_image else "text_analysis"
    }
