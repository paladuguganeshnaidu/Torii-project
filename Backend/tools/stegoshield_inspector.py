"""
StegoShield Inspector Tool

Analyzes uploaded images for hidden text, virus signatures, malware, or suspicious data.
Features:
- Text embedding via LSB steganography (encode/decode)
- Prank qmode: generates HTML that shows fake error popup
- Manipulate mode: adds warning overlays
- Real virus detection placeholder
- Multiple output formats: PNG, JPG, HTML, PDF
"""
from flask import request, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os

try:
    import importlib
    _reportlab_pdfgen = importlib.import_module('reportlab.pdfgen')
    canvas = _reportlab_pdfgen.canvas
    _pagesizes = importlib.import_module('reportlab.lib.pagesizes')
    letter = getattr(_pagesizes, 'letter')
    _utils = importlib.import_module('reportlab.lib.utils')
    ImageReader = getattr(_utils, 'ImageReader')
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


def analyze_stegoshield_tool(req):
    """
    Process uploaded image with text overlay, steganography, or prank triggers.
    
    Expected form fields:
    - image: uploaded file (PNG/JPG)
    - inspect_type: txt | virus | malware | suspicious
    - custom_text: (optional) text to embed if inspect_type=txt
    - virus_type: prank | manipulate | real (if inspect_type in [virus, malware, suspicious])
    - stego_mode: encode | decode (for text steganography)
    
    Returns JSON with analysis result and base64-encoded processed image or HTML trigger.
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
        stego_mode = req.form.get('stego_mode', 'encode').strip().lower()
        output_format = req.form.get('output_format', 'png').strip().lower()
        
        if not inspect_type:
            return {"ok": False, "error": "inspect_type is required"}
        
        # Open image
        img = Image.open(file.stream).convert("RGB")
        
        # Handle different inspection types
        if inspect_type == "txt":
            if stego_mode == "encode" and custom_text:
                # Embed text using LSB steganography
                img_encoded = _encode_text_lsb(img, custom_text)
                
                if output_format == "pdf":
                    pdf_base64 = _generate_image_pdf(img_encoded, "TEXT HIDDEN VIA STEGANOGRAPHY")
                    return {
                        "ok": True,
                        "message": "Text hidden using LSB steganography (PDF)",
                        "inspect_type": inspect_type,
                        "stego_mode": "encode",
                        "output_format": "pdf",
                        "hidden_text_length": len(custom_text),
                        "pdf_base64": pdf_base64
                    }
                else:
                    img_base64 = _image_to_base64(img_encoded, output_format)
                    return {
                        "ok": True,
                        "message": "Text hidden using LSB steganography",
                        "inspect_type": inspect_type,
                        "stego_mode": "encode",
                        "output_format": output_format,
                        "hidden_text_length": len(custom_text),
                        "image_base64": img_base64
                    }
            elif stego_mode == "decode":
                # Extract hidden text from image
                hidden_text = _decode_text_lsb(img)
                # Also add visual overlay
                draw = ImageDraw.Draw(img)
                font = _get_font()
                draw.text((10, 30), f"Decoded: {hidden_text[:50]}...", fill="lime", font=font)
                
                if output_format == "pdf":
                    pdf_base64 = _generate_image_pdf(img, f"DECODED TEXT: {hidden_text[:100]}")
                    return {
                        "ok": True,
                        "message": "Text extracted from image (PDF)",
                        "inspect_type": inspect_type,
                        "stego_mode": "decode",
                        "output_format": "pdf",
                        "hidden_text": hidden_text,
                        "pdf_base64": pdf_base64
                    }
                else:
                    img_base64 = _image_to_base64(img, output_format)
                    return {
                        "ok": True,
                        "message": "Text extracted from image",
                        "inspect_type": inspect_type,
                        "stego_mode": "decode",
                        "output_format": output_format,
                        "hidden_text": hidden_text,
                        "image_base64": img_base64
                    }
            else:
                # Just overlay text visually
                draw = ImageDraw.Draw(img)
                font = _get_font()
                text = custom_text if custom_text else "(no text provided)"
                draw.text((10, 30), f"Text: {text}", fill="white", font=font)
                
                if output_format == "pdf":
                    pdf_base64 = _generate_image_pdf(img, "TEXT OVERLAY")
                    return {
                        "ok": True,
                        "message": "Text overlay PDF ready",
                        "inspect_type": inspect_type,
                        "output_format": "pdf",
                        "custom_text": custom_text,
                        "pdf_base64": pdf_base64
                    }
                else:
                    img_base64 = _image_to_base64(img, output_format)
                    return {
                        "ok": True,
                        "message": "Text overlay added",
                        "inspect_type": inspect_type,
                        "output_format": output_format,
                        "custom_text": custom_text,
                        "image_base64": img_base64
                    }
        
        elif inspect_type in ["virus", "malware", "suspicious"]:
            if virus_type == "prank":
                # Generate output based on format
                if output_format == "html":
                    # Generate prank HTML that triggers fake error popup
                    html_trigger = _generate_prank_html(img)
                    return {
                        "ok": True,
                        "message": "Prank HTML file ready! Send to your friend.",
                        "inspect_type": inspect_type,
                        "virus_type": "prank",
                        "output_format": "html",
                        "prank_html": html_trigger,
                        "instructions": "Send the downloaded HTML file. When opened, it shows a fake error popup."
                    }
                elif output_format == "pdf":
                    # Generate PDF with prank message
                    pdf_base64 = _generate_prank_pdf(img)
                    return {
                        "ok": True,
                        "message": "Prank PDF ready!",
                        "inspect_type": inspect_type,
                        "virus_type": "prank",
                        "output_format": "pdf",
                        "pdf_base64": pdf_base64
                    }
                else:
                    # For PNG/JPG: clean image without overlay (so it looks normal)
                    img_base64 = _image_to_base64(img, output_format)
                    return {
                        "ok": True,
                        "message": "Clean image ready (use HTML format for prank popup)",
                        "inspect_type": inspect_type,
                        "virus_type": "prank",
                        "output_format": output_format,
                        "image_base64": img_base64,
                        "note": "Image has no overlay. Switch to HTML format for prank popup."
                    }
            
            elif virus_type == "manipulate":
                # Add warning overlay
                draw = ImageDraw.Draw(img)
                font = _get_font()
                draw.text((10, 30), "⚠️ SUSPICIOUS CODE DETECTED", fill="orange", font=font)
                draw.text((10, 60), "Manipulative content found", fill="orange", font=font)
                
                if output_format == "pdf":
                    pdf_base64 = _generate_image_pdf(img, "MANIPULATIVE CONTENT WARNING")
                    return {
                        "ok": True,
                        "message": "Manipulative content warning PDF ready",
                        "inspect_type": inspect_type,
                        "virus_type": "manipulate",
                        "output_format": "pdf",
                        "pdf_base64": pdf_base64
                    }
                else:
                    img_base64 = _image_to_base64(img, output_format)
                    return {
                        "ok": True,
                        "message": "Manipulative content warning added",
                        "inspect_type": inspect_type,
                        "virus_type": "manipulate",
                        "output_format": output_format,
                        "image_base64": img_base64
                    }
            
            elif virus_type == "real":
                # Real virus detection placeholder
                draw = ImageDraw.Draw(img)
                font = _get_font()
                draw.text((10, 30), "🚨 REAL VIRUS DETECTED 🚨", fill="red", font=font)
                draw.text((10, 60), "Quarantine recommended", fill="red", font=font)
                
                if output_format == "pdf":
                    pdf_base64 = _generate_image_pdf(img, "REAL VIRUS DETECTED - QUARANTINE")
                    return {
                        "ok": True,
                        "message": "Real virus signature PDF ready",
                        "inspect_type": inspect_type,
                        "virus_type": "real",
                        "output_format": "pdf",
                        "pdf_base64": pdf_base64
                    }
                else:
                    img_base64 = _image_to_base64(img, output_format)
                    return {
                        "ok": True,
                        "message": "Real virus signature detected (simulated)",
                        "inspect_type": inspect_type,
                        "virus_type": "real",
                        "output_format": output_format,
                        "image_base64": img_base64
                    }
        
        return {"ok": False, "error": f"Unknown configuration"}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _get_font():
    """Get a font for drawing text."""
    try:
        return ImageFont.truetype("arial.ttf", 20)
    except:
        return ImageFont.load_default()


def _image_to_base64(img, output_format='png'):
    """Convert PIL Image to base64 string."""
    buffer = io.BytesIO()
    fmt = 'JPEG' if output_format == 'jpg' else 'PNG'
    img.save(buffer, format=fmt)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def _encode_text_lsb(img, text):
    """
    Hide text in image using LSB (Least Significant Bit) steganography.
    Embeds text in the least significant bits of RGB pixel values.
    """
    # Add delimiter to mark end of message
    text_with_delim = text + "<<<END>>>"
    binary_text = ''.join(format(ord(char), '08b') for char in text_with_delim)
    
    pixels = list(img.getdata())
    new_pixels = []
    text_index = 0
    
    for pixel in pixels:
        if text_index < len(binary_text):
            # Modify RGB values
            r, g, b = pixel
            if text_index < len(binary_text):
                r = (r & ~1) | int(binary_text[text_index])
                text_index += 1
            if text_index < len(binary_text):
                g = (g & ~1) | int(binary_text[text_index])
                text_index += 1
            if text_index < len(binary_text):
                b = (b & ~1) | int(binary_text[text_index])
                text_index += 1
            new_pixels.append((r, g, b))
        else:
            new_pixels.append(pixel)
    
    new_img = Image.new(img.mode, img.size)
    new_img.putdata(new_pixels)
    return new_img


def _decode_text_lsb(img):
    """
    Extract hidden text from image using LSB steganography.
    """
    pixels = list(img.getdata())
    binary_text = ""
    
    for pixel in pixels:
        r, g, b = pixel
        binary_text += str(r & 1)
        binary_text += str(g & 1)
        binary_text += str(b & 1)
    
    # Convert binary to text
    text = ""
    for i in range(0, len(binary_text), 8):
        byte = binary_text[i:i+8]
        if len(byte) == 8:
            char = chr(int(byte, 2))
            text += char
            # Check for delimiter
            if text.endswith("<<<END>>>"):
                return text[:-9]  # Remove delimiter
    
    return text if text else "(no hidden text found)"


def _generate_prank_html(img):
    """
    Generate HTML file that shows the image and triggers a fake error popup.
    When your friend opens this HTML, they'll see the error message.
    """
    img_base64 = _image_to_base64(img)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Image</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: Arial, sans-serif;
        }}
        img {{
            max-width: 90%;
            height: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .error-popup {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border: 3px solid #d32f2f;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.7);
            z-index: 9999;
            min-width: 400px;
            animation: shake 0.5s;
        }}
        @keyframes shake {{
            0%, 100% {{ transform: translate(-50%, -50%) rotate(0deg); }}
            25% {{ transform: translate(-50%, -50%) rotate(-2deg); }}
            75% {{ transform: translate(-50%, -50%) rotate(2deg); }}
        }}
        .error-icon {{
            font-size: 48px;
            color: #d32f2f;
            text-align: center;
            margin-bottom: 10px;
        }}
        .error-title {{
            font-size: 24px;
            font-weight: bold;
            color: #d32f2f;
            text-align: center;
            margin-bottom: 15px;
        }}
        .error-message {{
            font-size: 16px;
            color: #333;
            text-align: center;
            margin-bottom: 20px;
            line-height: 1.6;
        }}
        .error-code {{
            font-family: monospace;
            background: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
            color: #666;
            margin-bottom: 20px;
        }}
        .error-button {{
            display: block;
            width: 100%;
            padding: 12px;
            background: #d32f2f;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }}
        .error-button:hover {{
            background: #b71c1c;
        }}
        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 9998;
        }}
    </style>
</head>
<body>
    <img src="data:image/png;base64,{img_base64}" alt="Image" />
    
    <div class="overlay" id="overlay"></div>
    <div class="error-popup" id="errorPopup">
        <div class="error-icon">⚠️</div>
        <div class="error-title">ERROR TRANSFERRING DATA</div>
        <div class="error-message">
            Unable to complete the data transfer operation.<br>
            The connection was interrupted or the file may be corrupted.
        </div>
        <div class="error-code">
            Error Code: 0x80070057<br>
            Status: TRANSFER_FAILED
        </div>
        <button class="error-button" onclick="closeError()">OK</button>
    </div>

    <script>
        // Show popup after a short delay for dramatic effect
        setTimeout(function() {{
            document.getElementById('errorPopup').style.display = 'block';
            document.getElementById('overlay').style.display = 'block';
            
            // Play system error sound (if browser allows)
            try {{
                var audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZQA4RV7Dn7bJgGQc/l9nz0YAyBiZ9zu/cjzoIHG/A7+CXRwwTY7Tn6rNdGAhBmNny0n0wBSh+zu7ekjgII3G/7uCVRAwSZrXm6rNcGAdAmNny03wwBSh+zu7ejDoHInG/7uCURQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoHInG/7uCUQQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoHInG/7uCUQQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoHInG/7uCUQQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoHInG/7uCUQQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoHInG/7uCUQQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoHInG/7uCUQQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoHInG/7uCUQQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoHInG/7uCUQQsTZrXm6rJcGAc/mNny03wwBSh9zu7djjoH');
                audio.play();
            }} catch(e) {{}}
        }}, 1000);
        
        function closeError() {{
            document.getElementById('errorPopup').style.display = 'none';
            document.getElementById('overlay').style.display = 'none';
        }}
        
        // Easter egg: clicking image multiple times shows another message
        var clickCount = 0;
        document.querySelector('img').addEventListener('click', function() {{
            clickCount++;
            if(clickCount === 5) {{
                alert('Just kidding! This is a harmless prank 😄\\n\\nNo data was transferred or lost.\\nYour friend got pranked! 🎉');
                clickCount = 0;
            }}
        }});
    </script>
</body>
</html>"""
    
    return html_content


def _generate_prank_pdf(img):
    """
    Generate a PDF with the image and a fake virus warning message.
    Falls back to simple text if reportlab not available.
    """
    if not REPORTLAB_AVAILABLE:
        return None
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(0.8, 0, 0)
    c.drawCentredString(width/2, height - 100, "⚠️ SYSTEM ALERT")
    
    # Message
    c.setFont("Helvetica", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, height - 140, "Error transferring data. File may be corrupted.")
    c.drawCentredString(width/2, height - 165, "Error Code: 0x80070057")
    
    # Add image
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_reader = ImageReader(img_buffer)
    
    # Calculate image dimensions to fit on page
    img_width, img_height = img.size
    max_width = width - 100
    max_height = height - 300
    scale = min(max_width / img_width, max_height / img_height)
    new_width = img_width * scale
    new_height = img_height * scale
    
    x = (width - new_width) / 2
    y = height - 250 - new_height
    
    c.drawImage(img_reader, x, y, width=new_width, height=new_height)
    
    c.save()
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def _generate_image_pdf(img, title):
    """
    Generate a PDF with an image and custom title.
    """
    if not REPORTLAB_AVAILABLE:
        return None
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0.8, 0, 0)
    c.drawCentredString(width/2, height - 80, title)
    
    # Add image
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_reader = ImageReader(img_buffer)
    
    # Calculate image dimensions
    img_width, img_height = img.size
    max_width = width - 100
    max_height = height - 200
    scale = min(max_width / img_width, max_height / img_height)
    new_width = img_width * scale
    new_height = img_height * scale
    
    x = (width - new_width) / 2
    y = height - 150 - new_height
    
    c.drawImage(img_reader, x, y, width=new_width, height=new_height)
    
    c.save()
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')
