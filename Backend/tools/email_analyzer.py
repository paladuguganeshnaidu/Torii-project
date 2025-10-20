def analyze_email_tool(request):
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    result = {
        'tool': 'email-analyzer',
        'length': len(text),
        'contains_links': 'http' in text or 'www.' in text,
        'keywords': [k for k in ['urgent', 'verify', 'password', 'invoice'] if k in text.lower()],
        'summary': 'Stub analysis: no real parsing performed.'
    }
    return result
