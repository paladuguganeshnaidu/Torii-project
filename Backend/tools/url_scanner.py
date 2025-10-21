import requests
from urllib.parse import urlparse
from flask import request

def scan_url_tool(flask_request):
    """
    Scan URLs for security issues and gather information
    """
    data = flask_request.get_json()
    url = data.get('url')
    
    if not url:
        return {'error': 'URL is required'}
    
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    results = {
        'url': url,
        'domain': urlparse(url).netloc,
        'accessible': False,
        'redirects': False,
        'security_headers': {}
    }
    
    try:
        resp = requests.get(url, timeout=10, allow_redirects=True)
        results['accessible'] = True
        results['status_code'] = resp.status_code
        results['redirects'] = len(resp.history) > 0
        
        # Check for security headers
        headers = resp.headers
        security_headers = {
            'X-Frame-Options': headers.get('X-Frame-Options'),
            'X-XSS-Protection': headers.get('X-XSS-Protection'),
            'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
            'Strict-Transport-Security': headers.get('Strict-Transport-Security')
        }
        results['security_headers'] = security_headers
        
    except Exception as e:
        results['error'] = str(e)
    
    return results