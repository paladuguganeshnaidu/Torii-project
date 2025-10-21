import email
import hashlib
from flask import request
try:
    import yara  # optional; not required for basic analysis
except Exception:  # pragma: no cover
    yara = None

def analyze_email_tool(flask_request):
    """
    Analyze email files for malicious attachments and suspicious content
    """
    if 'email_file' not in flask_request.files:
        return {'error': 'No email file provided'}
        
    email_file = flask_request.files['email_file']
    msg = email.message_from_bytes(email_file.read())
    
    results = {
        'attachments': [],
        'sender': msg.get('From', ''),
        'subject': msg.get('Subject', ''),
        'has_attachments': False
    }
    
    # Check attachments
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            results['has_attachments'] = True
            filename = part.get_filename()
            payload = part.get_payload(decode=True)
            
            # Calculate hash
            file_hash = hashlib.sha256(payload).hexdigest()
            
            # Simple suspicious checks (in a real implementation, use more robust methods)
            is_suspicious = len(payload) > 10000 or b'exe' in payload[:20].lower()
            
            results['attachments'].append({
                'filename': filename,
                'sha256': file_hash,
                'size': len(payload),
                'suspicious': is_suspicious
            })
    
    return results