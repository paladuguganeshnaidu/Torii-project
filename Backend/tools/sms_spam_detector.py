import re
from flask import request

def test_sms_tool(flask_request):
    """
    Analyze SMS content for spam indicators
    """
    data = flask_request.get_json()
    phone_number = data.get('phone', '')
    message = data.get('message', '')
    
    if not message:
        return {'error': 'Message content required'}
    
    # Common spam patterns
    spam_patterns = [
        (r'\b\d{4,}\b', 'Long number sequences'),
        (r'(free|win|won|cash|prize)', 'Prize-related keywords'),
        (r'\$\$', 'Multiple dollar signs'),
        (r'[!]{3,}', 'Multiple exclamation marks'),
        (r'\b(click|call|text)\s+now\b', 'Urgent action requests'),
        (r'\b(hurry|limited|offer)\b', 'Scarcity tactics')
    ]
    
    spam_indicators = []
    spam_score = 0
    
    for pattern, description in spam_patterns:
        matches = re.findall(pattern, message.lower())
        if matches:
            spam_indicators.append({
                'pattern': description,
                'matches': matches
            })
            spam_score += len(matches)
    
    # Normalize score
    normalized_score = min(spam_score / 5, 1.0)
    
    return {
        'phone_number': phone_number,
        'message_length': len(message),
        'spam_score': round(normalized_score, 2),
        'indicators': spam_indicators,
        'is_spam': normalized_score > 0.6
    }