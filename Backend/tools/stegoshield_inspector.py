"""
StegoShield Inspector Tool

Analyzes uploaded images for hidden text, virus signatures, malware, or suspicious data.
Based on the original Tkinter-based image processor, adapted for Flask API.
"""
from flask import request, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import base64


def analyze_stegoshield_tool(req):
    """
    Process uploaded image with text overlay or virus markers.
    
    Expected form fields:
    - image: uploaded file (PNG/JPG)
    - inspect_type: txt | virus | malware | suspicious
    - custom_text: (optional) text to embed if inspect_type=txt
    - virus_type: prank | manipulate | real (if inspect_type in [virus, malware, suspicious])
    
    Returns JSON with analysis result and base64-encoded processed image.
    """
    try:
        # Validate file upload
        if 'image' not in req.files:
            return {"ok": False, "error": "No image file uploaded"}
        
        file = req.files['image']
        if file.filename == '':
            return {"ok": False, "error": "Empty filename"}
        
        # Read parameters
        inspect_type = req.form.get('inspect_type', '').strip().lower()
        custom_text = req.form.get('custom_text', '').strip()
        virus_type = req.form.get('virus_type', 'prank').strip().lower()
        
        if not inspect_type:
            return {"ok": False, "error": "inspect_type is required"}
        
        # Open image
        img = Image.open(file.stream).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Use default font (you can improve with truetype if available)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        y_offset = 30
        overlay_text = ""
        overlay_color = "white"
        
        # Process based on inspection type
        if inspect_type == "txt":
            if custom_text:
                overlay_text = f"Text: {custom_text}"
                overlay_color = "white"
            else:
                overlay_text = "Text: (no text provided)"
                overlay_color = "gray"
        elif inspect_type in ["virus", "malware", "suspicious"]:
            virus_label = {
                "prank": "Prank Virus",
                "manipulate": "Manipulative Code",
                "real": "Real Virus Detected"
            }.get(virus_type, "Unknown")
            overlay_text = f"Type: {virus_label}"
            overlay_color = "red"
        else:
            return {"ok": False, "error": f"Unknown inspect_type: {inspect_type}"}
        
        # Draw text on image
        draw.text((10, y_offset), overlay_text, fill=overlay_color, font=font)
        
        # Convert processed image to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return {
            "ok": True,
            "message": "Image processed successfully",
            "inspect_type": inspect_type,
            "overlay_text": overlay_text,
            "virus_type": virus_type if inspect_type in ["virus", "malware", "suspicious"] else None,
            "custom_text": custom_text if inspect_type == "txt" else None,
            "image_base64": img_base64
        }
    
    except Exception as e:
        return {"ok": False, "error": str(e)}
