from flask import Blueprint, request, jsonify
from ..tools.web_vuln_scanner import WebVulnScanner
import threading
from functools import wraps
import time
from collections import deque

api_bp = Blueprint('api', __name__)

# Simple rate limit using per-IP deques
def rate_limit(max_requests=5, window=60):
    last_calls = {}
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr or 'anon'
            now = time.time()
            if ip not in last_calls:
                last_calls[ip] = deque()
            # Purge old
            while last_calls[ip] and now - last_calls[ip][0] > window:
                last_calls[ip].popleft()
            if len(last_calls[ip]) >= max_requests:
                return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
            last_calls[ip].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# In-memory active scans map: scan_id -> {status, target, started_at, results?}
active_scans = {}


@api_bp.route('/scan', methods=['POST'])
@rate_limit(max_requests=3, window=60)
def start_scan():
    data = request.get_json() or {}
    target = (data.get('url') or '').strip()
    if not target:
        return jsonify({"error": "URL is required"}), 400
    if not (target.startswith('http://') or target.startswith('https://')):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    def run_scan(tid: str, url: str):
        scanner = WebVulnScanner(url, timeout=15)
        try:
            results = scanner.run()
            active_scans[tid]["status"] = "complete"
            active_scans[tid]["results"] = results
        except Exception as e:
            active_scans[tid]["status"] = "error"
            active_scans[tid]["error"] = str(e)

    scan_id = f"scan_{int(time.time())}_{(request.remote_addr or 'anon').replace('.', '_') }"
    active_scans[scan_id] = {"status": "running", "target": target, "started_at": time.time()}

    thread = threading.Thread(target=run_scan, args=(scan_id, target), daemon=True)
    thread.start()

    return jsonify({"scan_id": scan_id, "status": "started", "target": target})


@api_bp.route('/scan/<scan_id>', methods=['GET'])
def get_scan_status(scan_id: str):
    scan = active_scans.get(scan_id)
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    if scan.get('status') == 'complete':
        return jsonify({"status": "complete", "target": scan.get('target'), "results": scan.get('results', [])})
    if scan.get('status') == 'error':
        return jsonify({"status": "error", "error": scan.get('error')}), 200
    return jsonify({"status": "running", "target": scan.get('target')})
