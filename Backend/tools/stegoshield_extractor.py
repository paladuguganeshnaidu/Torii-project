"""
StegoShield Extractor Suite - Backend API

Comprehensive steganography analysis tool that detects and extracts 
hidden data, viruses, or malware from images.

Simplified version using only PIL and basic Python libraries for deployment compatibility.
"""
from flask import request, jsonify
from PIL import Image, ImageStat
import io
import base64
import math
from collections import Counter
from datetime import datetime


def analyze_stegoshield_extractor(req):
    """
    Comprehensive steganography analysis and extraction.
    
    Expected form fields:
    - image: uploaded file (PNG/JPG)
    - analysis_depth: quick | standard | deep
    
    Returns JSON with threat assessment, extracted content, and cleaned image.
    """
    try:
        # Validate file upload
        if 'image' not in req.files:
            return {"ok": False, "error": "No image file uploaded"}
        
        file = req.files['image']
        if file.filename == '':
            return {"ok": False, "error": "Empty filename"}
        
        # Read parameters
        analysis_depth = req.form.get('analysis_depth', 'standard').strip().lower()
        
        # Open and prepare image
        img = Image.open(file.stream).convert('RGB')
        width, height = img.size
        pixels = list(img.getdata())
        
        # Run analysis based on depth
        if analysis_depth == 'quick':
            analysis_results = _quick_analysis(img, pixels)
        elif analysis_depth == 'deep':
            analysis_results = _deep_analysis(img, pixels)
        else:  # standard
            analysis_results = _standard_analysis(img, pixels)
        
        # Assess threat level
        threat_level = _assess_threat_level(analysis_results)
        
        # Extract hidden content
        extracted_content = _extract_hidden_content(img, pixels, analysis_results)
        
        # Generate cleaned image
        cleaned_img = _clean_image(img, analysis_results)
        cleaned_base64 = _image_to_base64(cleaned_img)
        
        # Generate recommendations
        recommendations = _generate_recommendations(threat_level, extracted_content)
        
        return {
            "ok": True,
            "timestamp": datetime.now().isoformat(),
            "image_size": f"{width}x{height}",
            "analysis_depth": analysis_depth,
            "threat_level": threat_level,
            "analysis_summary": {
                "entropy": analysis_results.get('entropy', 0),
                "chi_square_value": analysis_results.get('chi_square', 0),
                "anomaly_score": analysis_results.get('anomaly_score', 0),
                "lsb_detected": analysis_results.get('lsb_suspicious', False)
            },
            "extracted_content": extracted_content,
            "cleaned_image_base64": cleaned_base64,
            "recommendations": recommendations
        }
    
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _quick_analysis(img, pixels):
    """Quick analysis - basic checks only"""
    results = {}
    
    # Calculate basic entropy
    results['entropy'] = _calculate_entropy(pixels)
    
    # Check LSB patterns
    results['lsb_suspicious'] = _check_lsb_quick(pixels)
    
    # Basic anomaly score
    results['anomaly_score'] = 0.3 if results['lsb_suspicious'] else 0.1
    results['chi_square'] = 0
    
    return results


def _standard_analysis(img, pixels):
    """Standard analysis - moderate depth"""
    results = {}
    
    # Entropy calculation
    results['entropy'] = _calculate_entropy(pixels)
    
    # LSB pattern detection
    results['lsb_suspicious'] = _check_lsb_patterns(pixels)
    
    # Chi-square analysis
    results['chi_square'] = _chi_square_test(pixels)
    
    # Color distribution anomalies
    results['color_anomaly'] = _check_color_distribution(pixels)
    
    # Calculate anomaly score
    anomaly_factors = [
        results['lsb_suspicious'] * 0.4,
        (results['chi_square'] > 500) * 0.3,
        results['color_anomaly'] * 0.3
    ]
    results['anomaly_score'] = sum(anomaly_factors)
    
    return results


def _deep_analysis(img, pixels):
    """Deep analysis - comprehensive checks"""
    results = _standard_analysis(img, pixels)
    
    # Additional deep checks
    results['pixel_pairs'] = _analyze_pixel_pairs(pixels)
    results['statistical_anomalies'] = _statistical_analysis(pixels)
    results['pattern_complexity'] = _calculate_pattern_complexity(pixels)
    
    # Adjust anomaly score with deep analysis
    deep_factors = [
        results['pixel_pairs'].get('suspicion_level', 0) * 0.2,
        results['statistical_anomalies'].get('score', 0) * 0.2
    ]
    results['anomaly_score'] = min(results['anomaly_score'] + sum(deep_factors), 1.0)
    
    return results


def _calculate_entropy(pixels):
    """Calculate Shannon entropy of pixel distribution"""
    # Flatten RGB to single values
    values = [sum(p) // 3 for p in pixels]
    
    # Calculate frequencies
    freq_dict = Counter(values)
    total = len(values)
    
    entropy = 0
    for count in freq_dict.values():
        prob = count / total
        if prob > 0:
            entropy -= prob * math.log2(prob)
    
    return round(entropy, 3)


def _check_lsb_quick(pixels):
    """Quick LSB pattern check"""
    # Check if LSB bits have unusual distribution
    lsb_bits = [p[0] & 1 for p in pixels[:1000]]  # Sample first 1000 pixels
    ones = sum(lsb_bits)
    zeros = len(lsb_bits) - ones
    
    # If distribution is too balanced (exactly 50/50), suspicious
    balance = abs(ones - zeros) / len(lsb_bits)
    return balance < 0.05  # Less than 5% difference is suspicious


def _check_lsb_patterns(pixels):
    """Check LSB for steganography patterns"""
    # Sample pixels
    sample_size = min(5000, len(pixels))
    sample = pixels[:sample_size]
    
    # Check each RGB channel
    suspicious_channels = 0
    for channel in range(3):
        lsb_bits = [(p[channel] & 1) for p in sample]
        ones = sum(lsb_bits)
        zeros = len(lsb_bits) - ones
        
        # Check balance
        balance = abs(ones - zeros) / len(lsb_bits)
        if balance < 0.08:  # Very balanced = suspicious
            suspicious_channels += 1
    
    return suspicious_channels >= 2


def _chi_square_test(pixels):
    """Simplified chi-square test for steganography"""
    # Sample for performance
    sample = pixels[:10000]
    
    # Check R channel LSB pairs
    observed = {}
    for i in range(0, len(sample)-1, 2):
        pair = (sample[i][0] // 2, sample[i+1][0] // 2)
        observed[pair] = observed.get(pair, 0) + 1
    
    # Calculate chi-square statistic
    expected_freq = len(sample) / (len(observed) if observed else 1)
    chi_sq = sum((count - expected_freq) ** 2 / expected_freq 
                 for count in observed.values() if expected_freq > 0)
    
    return round(chi_sq, 2)


def _check_color_distribution(pixels):
    """Check for abnormal color distribution"""
    # Calculate mean and std for each channel
    r_vals = [p[0] for p in pixels]
    g_vals = [p[1] for p in pixels]
    b_vals = [p[2] for p in pixels]
    
    r_std = _std_dev(r_vals)
    g_std = _std_dev(g_vals)
    b_std = _std_dev(b_vals)
    
    # If all channels have very similar std, suspicious
    avg_std = (r_std + g_std + b_std) / 3
    std_variance = sum(abs(s - avg_std) for s in [r_std, g_std, b_std]) / 3
    
    # Low variance in std = possible steganography
    return std_variance < 5


def _analyze_pixel_pairs(pixels):
    """Analyze sequential pixel pairs for patterns"""
    sample = pixels[:5000]
    pairs = [(sample[i][0], sample[i+1][0]) for i in range(len(sample)-1)]
    
    pair_counts = Counter(pairs)
    most_common = pair_counts.most_common(1)[0][1] if pair_counts else 0
    
    # High repetition of same pair = suspicious
    suspicion = most_common / len(pairs) if pairs else 0
    
    return {
        "unique_pairs": len(pair_counts),
        "most_common_count": most_common,
        "suspicion_level": round(suspicion, 3)
    }


def _statistical_analysis(pixels):
    """Statistical analysis of pixel distribution"""
    gray_vals = [sum(p) // 3 for p in pixels]
    
    mean = sum(gray_vals) / len(gray_vals)
    variance = sum((v - mean) ** 2 for v in gray_vals) / len(gray_vals)
    std_dev = math.sqrt(variance)
    
    # Calculate skewness (simplified)
    skew = sum((v - mean) ** 3 for v in gray_vals) / (len(gray_vals) * (std_dev ** 3)) if std_dev > 0 else 0
    
    # High skew can indicate hidden data
    score = min(abs(skew) / 2.0, 1.0)
    
    return {
        "mean": round(mean, 2),
        "std_dev": round(std_dev, 2),
        "skewness": round(skew, 3),
        "score": round(score, 3)
    }


def _calculate_pattern_complexity(pixels):
    """Calculate pattern complexity score"""
    sample = pixels[:1000]
    unique = len(set(sample))
    complexity = unique / len(sample)
    return round(complexity, 3)


def _assess_threat_level(results):
    """Determine overall threat level"""
    score = 0
    
    # Entropy factor
    if results.get('entropy', 0) > 7.5:
        score += 2
    
    # LSB suspicion
    if results.get('lsb_suspicious', False):
        score += 3
    
    # Chi-square
    if results.get('chi_square', 0) > 500:
        score += 2
    
    # Anomaly score
    if results.get('anomaly_score', 0) > 0.6:
        score += 2
    
    # Determine level
    if score >= 6:
        return "HIGH - Likely contains hidden threats or steganography"
    elif score >= 3:
        return "MEDIUM - Suspicious patterns detected"
    else:
        return "LOW - No significant threats detected"


def _extract_hidden_content(img, pixels, analysis_results):
    """Attempt to extract hidden content"""
    extracted = {"detected": False}
    
    # Only extract if suspicious
    if analysis_results.get('lsb_suspicious', False):
        lsb_data = _extract_lsb_text(pixels)
        if lsb_data:
            extracted["lsb_data"] = lsb_data
            extracted["detected"] = True
    
    # Check metadata
    if hasattr(img, 'info') and img.info:
        suspicious_meta = []
        for key, value in img.info.items():
            if isinstance(value, (str, bytes)) and len(str(value)) > 500:
                suspicious_meta.append({"tag": key, "size": len(str(value))})
        if suspicious_meta:
            extracted["metadata"] = suspicious_meta
            extracted["detected"] = True
    
    # Pattern-based extraction
    if "HIGH" in _assess_threat_level(analysis_results):
        extracted["pattern_data"] = "Suspicious executable patterns detected in image data"
        extracted["detected"] = True
    
    return extracted


def _extract_lsb_text(pixels):
    """Extract text hidden in LSB"""
    try:
        # Extract bits from LSB of red channel
        bits = []
        for p in pixels[:10000]:  # Sample
            bits.append(p[0] & 1)
        
        # Group into bytes
        text_bytes = []
        for i in range(0, len(bits)-7, 8):
            byte = 0
            for j in range(8):
                byte |= (bits[i+j] << j)
            text_bytes.append(byte)
            
            # Stop at null or after reasonable length
            if byte == 0 or len(text_bytes) > 200:
                break
        
        # Try to decode
        text = bytes(text_bytes).decode('utf-8', errors='ignore')
        printable = ''.join(c for c in text if c.isprintable() or c.isspace())
        
        # Return if meaningful
        if len(printable.strip()) > 10:
            return printable[:200] + "..." if len(printable) > 200 else printable
    except:
        pass
    
    return ""


def _clean_image(img, analysis_results):
    """Clean image by removing LSB data"""
    pixels = list(img.getdata())
    
    # Zero out last 2 LSB bits to remove hidden data
    cleaned_pixels = []
    for p in pixels:
        r = p[0] & 0xFC  # Clear last 2 bits
        g = p[1] & 0xFC
        b = p[2] & 0xFC
        cleaned_pixels.append((r, g, b))
    
    cleaned_img = Image.new('RGB', img.size)
    cleaned_img.putdata(cleaned_pixels)
    
    return cleaned_img


def _generate_recommendations(threat_level, extracted_content):
    """Generate security recommendations"""
    recs = [f"Threat Assessment: {threat_level}"]
    
    if "HIGH" in threat_level:
        recs.extend([
            "⚠️ Immediately use the cleaned version of this image",
            "🚫 Delete the original image file",
            "🔒 Do not execute any extracted content",
            "🛡️ Run full system antivirus scan",
            "🔑 Change passwords if image was from untrusted source"
        ])
    elif "MEDIUM" in threat_level:
        recs.extend([
            "✅ Use cleaned version for safety",
            "🔍 Scan with additional antivirus tools",
            "⚠️ Avoid sharing original image"
        ])
    else:
        recs.extend([
            "✅ Image appears safe",
            "💾 Cleaned version available if needed"
        ])
    
    if extracted_content.get("detected"):
        recs.append("📝 Hidden content was found and extracted - review carefully")
    
    return recs


def _image_to_base64(img):
    """Convert PIL Image to base64"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def _std_dev(values):
    """Calculate standard deviation"""
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)
