import socket
import ssl
import requests
from urllib.parse import urlparse
from flask import request

def recon_target_tool(flask_request):
    """
    Perform basic web reconnaissance on a target
    """
    data = flask_request.get_json()
    target_url = data.get('url')
    
    if not target_url:
        return {'error': 'URL is required'}
    
    # Parse URL
    parsed = urlparse(target_url)
    domain = parsed.netloc.replace('www.', '') if parsed.netloc else target_url.replace('www.', '')
    protocol = parsed.scheme or 'http'
    full_url = f"{protocol}://{domain}" if not parsed.scheme else target_url
    
    # Gather intelligence
    results = {
        'target': full_url,
        'domain': domain,
        'ip_address': None,
        'ssl_info': None,
        'server_headers': None
    }
    
    # Get IP address
    try:
        ip = socket.gethostbyname(domain)
        results['ip_address'] = ip
    except Exception as e:
        results['ip_error'] = str(e)
    
    # Get SSL information if HTTPS
    if protocol == 'https':
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    results['ssl_info'] = {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'not_after': cert['notAfter']
                    }
        except Exception as e:
            results['ssl_error'] = str(e)
    
    # Get server headers
    try:
        response = requests.head(full_url, timeout=5)
        results['server_headers'] = dict(response.headers)
    except:
        try:
            response = requests.get(full_url, timeout=5)
            results['server_headers'] = dict(response.headers)
        except Exception as e:
            results['headers_error'] = str(e)
    
    return results