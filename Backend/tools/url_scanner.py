import re

def scan_url_tool(request):
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    is_http = url.startswith('http://')
    suspicious = bool(re.search(r'(\.|//)ip|\d+\.\d+\.\d+\.\d+', url))
    return {
        'tool': 'url-scanner',
        'url': url,
        'uses_https': url.startswith('https://'),
        'is_http': is_http,
        'suspicious': suspicious,
        'note': 'Stub scanner: pattern-based only.'
    }
