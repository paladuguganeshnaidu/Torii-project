import os
from flask import Flask, jsonify, render_template, request, send_from_directory, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash

from .config import Config, PROJECT_ROOT
from .database import get_db, close_db, init_db
from .db_adapter import init_database, close_db_connection, get_user_by_id, get_user_by_email, update_user_password, update_user_entitlements
from .auth import bp as auth_bp
from .admin import admin_bp
from .tools.email_analyzer import analyze_email_tool
from .tools.url_scanner import scan_url_tool
from .tools.password_cracker import crack_hash_tool
from .tools.sms_spam_detector import test_sms_tool
from .tools.malware_analyzer import analyze_file_tool
from .tools.web_recon import recon_target_tool
from .tools.stegoshield_inspector import analyze_stegoshield_tool
from .tools.stegoshield_extractor import analyze_stegoshield_extractor
from .tools.web_vuln_scanner import WebVulnScanner
import time
from collections import deque
from functools import wraps
from .tools.dos_detector import DoSDetector
import threading


def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
    app.config.from_object(Config)

    # DoS detector instance attached to app for lifecycle management
    try:
        app.detector = DoSDetector()
    except Exception:
        # If tools aren't available in environment, attach a dummy
        app.detector = None
    app.detection_thread = None
    app.detection_active = False

    # Init DB on startup
    with app.app_context():
        try:
            init_db(app)
        except Exception as e:
            app.logger.warning(f"DB init skipped or failed: {e}")
        # Initialize unified database (MySQL or SQLite)
        try:
            init_database(app)
        except Exception as e:
            app.logger.warning(f"Database init skipped or failed: {e}")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Teardown
    app.teardown_appcontext(close_db)
    app.teardown_appcontext(close_db_connection)

    # Compute canonical frontend/static directories
    FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
    # Premium/restricted pages (filenames) - can be overridden via env var PREMIUM_PAGES
    _DEFAULT_PREMIUM_PAGES = {
        'tool7-stegoshield-inspector.html',
        'tool8-stegoshield-extractor.html',
    }
    _env_premium_pages = os.getenv('PREMIUM_PAGES', '')
    PREMIUM_PAGES = set([p.strip() for p in _env_premium_pages.split(',') if p.strip()]) or _DEFAULT_PREMIUM_PAGES

    # Serve the styled static homepage by default
    @app.route('/')
    def index():
        # Serve the static index.html from frontend folder
        return send_from_directory(FRONTEND_DIR, 'index.html')

    # Also serve /index.html explicitly (links may reference it)
    @app.route('/index.html')
    def static_index_file():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    # Serve assets used by the static pages (e.g., assets/css/main.css)
    @app.route('/assets/<path:filename>')
    def static_assets(filename):
        assets_dir = os.path.join(PROJECT_ROOT, 'assets')
        return send_from_directory(assets_dir, filename)

    # Expose the static tool pages for convenience
    _ALLOWED_STATIC_PAGES = {
        'tool1-email-analyzer.html',
        'tool2-url-scanner.html',
        'tool3-password-cracker.html',
        'tool4-sms-spam-tester.html',
        'tool5-malware-analyzer.html',
        'tool6-web-recon.html',
        'tool7-stegoshield-inspector.html',
        'tool8-stegoshield-extractor.html',
        'tool9-dos-detector.html',
        'directory.html',
        'profile.html',
        'settings.html',
    }

    @app.route('/<path:filename>')
    def serve_static_pages(filename):
        from werkzeug.exceptions import NotFound
        if filename in _ALLOWED_STATIC_PAGES:
            # Enforce premium access for restricted pages
            if filename in PREMIUM_PAGES:
                # Require login
                user_id = session.get('user_id')
                if not user_id:
                    return redirect(url_for('auth.login'))
                user = get_user_by_id(user_id)
                if not _user_can_access(user, filename):
                    return redirect('/')
            # Prefer files under frontend/, but fall back to project root for legacy pages
            try:
                return send_from_directory(FRONTEND_DIR, filename)
            except NotFound:
                try:
                    return send_from_directory(PROJECT_ROOT, filename)
                except NotFound:
                    return redirect('/')
        # Redirect to modern tile-based homepage for any unknown routes
        return redirect('/')

    # User session API
    @app.get('/api/user-session')
    def api_user_session():
        """Return current user session info for profile display."""
        if 'user' in session or 'user_id' in session:
            user = None
            try:
                uid = session.get('user_id')
                if uid:
                    user = get_user_by_id(uid)
            except Exception:
                user = None
            info = {
                'logged_in': True,
                'email': session.get('user', session.get('email', '')),
                'user_id': session.get('user_id'),
            }
            if user:
                info['is_premium'] = bool(user.get('is_premium') or False)
                info['allowed_tools'] = user.get('allowed_tools')
            return jsonify(info)
        return jsonify({'logged_in': False})

    # Profile API
    @app.get('/api/profile')
    def api_get_profile():
        """Get current user profile."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'ok': False, 'error': 'Not logged in'}), 401
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'ok': False, 'error': 'User not found'}), 404
        
        return jsonify({'ok': True, 'user': user})

    @app.post('/api/change-password')
    def api_change_password():
        """Change user password."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'ok': False, 'error': 'Not logged in'}), 401
        
        data = request.get_json(silent=True) or {}
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        if not current_password or not new_password:
            return jsonify({'ok': False, 'error': 'All fields are required'})
        
        if new_password != confirm_password:
            return jsonify({'ok': False, 'error': 'New passwords do not match'})
        
        if len(new_password) < 6:
            return jsonify({'ok': False, 'error': 'Password must be at least 6 characters'})
        
        # Get user and verify current password
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'ok': False, 'error': 'User not found'}), 404

        # Get full user record with password_hash (adapter returns dict)
        user_full = get_user_by_email(user['email'])
        if not user_full:
            return jsonify({'ok': False, 'error': 'User not found'}), 404
        
        # Extract password hash (dict by default; tuple fallback supported)
        if isinstance(user_full, dict):
            password_hash = user_full.get('password_hash')
        else:
            # Expected order when selected explicitly: id, email, password_hash, mobile, registered_at
            password_hash = user_full[2] if len(user_full) > 2 else None
        
        if not password_hash:
            return jsonify({'ok': False, 'error': 'Password verification failed'}), 500
        
        # Verify current password
        if not check_password_hash(password_hash, current_password):
            return jsonify({'ok': False, 'error': 'Current password is incorrect'})
        
        # Update password
        new_hash = generate_password_hash(new_password)
        success = update_user_password(user_id, new_hash)
        
        if success:
            return jsonify({'ok': True, 'message': 'Password changed successfully'})
        else:
            return jsonify({'ok': False, 'error': 'Failed to update password'}), 500

    # API endpoints
    @app.post('/api/email-analyzer')
    def api_email_analyzer():
        result = analyze_email_tool(request)
        _log_tool('email-analyzer', request, result)
        return jsonify(result)

    @app.post('/api/url-scanner')
    def api_url_scanner():
        result = scan_url_tool(request)
        _log_tool('url-scanner', request, result)
        return jsonify(result)

    @app.post('/api/password-cracker')
    def api_password_cracker():
        result = crack_hash_tool(request)
        _log_tool('password-cracker', request, result)
        return jsonify(result)

    @app.post('/api/sms-spam-tester')
    def api_sms_spam_tester():
        result = test_sms_tool(request)
        _log_tool('sms-spam-tester', request, result)
        return jsonify(result)

    @app.post('/api/malware-analyzer')
    def api_malware_analyzer():
        result = analyze_file_tool(request)
        _log_tool('malware-analyzer', request, result)
        return jsonify(result)

    @app.post('/api/web-recon')
    def api_web_recon():
        result = recon_target_tool(request)
        _log_tool('web-recon', request, result)
        return jsonify(result)

    @app.post('/api/stegoshield-inspector')
    def api_stegoshield_inspector():
        result = analyze_stegoshield_tool(request)
        _log_tool('stegoshield-inspector', request, result)
        return jsonify(result)

    @app.post('/api/stegoshield-extractor')
    def api_stegoshield_extractor():
        result = analyze_stegoshield_extractor(request)
        _log_tool('stegoshield-extractor', request, result)
        return jsonify(result)

    def _log_tool(tool_name, req, result):
        try:
            db = get_db()
            db.execute(
                'INSERT INTO tool_logs(tool_name, input, result) VALUES (?, ?, ?)',
                (
                    tool_name,
                    _safe_str(_extract_input(req)),
                    _safe_str(result),
                ),
            )
            db.commit()
        except Exception as e:
            app.logger.debug(f"Log failed: {e}")

    def _extract_input(req):
        if req.is_json:
            return req.get_json(silent=True) or {}
        if req.form:
            return dict(req.form)
        return {}

    def _safe_str(obj):
        try:
            import json
            return json.dumps(obj, ensure_ascii=False)
        except Exception:
            return str(obj)

    def _user_can_access(user: dict, filename: str) -> bool:
        """Evaluate if the user can access a restricted page."""
        if not user:
            return False
        # Premium flag grants all premium pages
        if user.get('is_premium'):
            return True
        # Otherwise check explicit allowed_tools list (stored as JSON or CSV)
        raw = user.get('allowed_tools') or ''
        try:
            import json
            tools = json.loads(raw) if raw and raw.strip().startswith('[') else [t.strip() for t in raw.split(',') if t.strip()]
        except Exception:
            tools = [t.strip() for t in str(raw).split(',') if t.strip()]
        return filename in set(tools)

    @app.post('/api/redeem-coupon')
    def api_redeem_coupon():
        """Redeem a single coupon code to unlock tools or premium access for the current user."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'ok': False, 'error': 'Not logged in'}), 401

        data = request.get_json(silent=True) or {}
        code = (data.get('code') or '').strip()
        if not code:
            return jsonify({'ok': False, 'error': 'Coupon code required'}), 400

        configured = os.getenv('COUPON_CODE', '')
        if not configured:
            return jsonify({'ok': False, 'error': 'Coupon not configured'}), 500

        if code != configured:
            return jsonify({'ok': False, 'error': 'Invalid coupon code'}), 400

        # Apply entitlements from env
        grant_premium = os.getenv('COUPON_GRANT_PREMIUM', 'false').lower() in ('1', 'true', 'yes')
        tools_env = os.getenv('PREMIUM_ALLOWED_TOOLS', '')
        tools = [t.strip() for t in tools_env.split(',') if t.strip()]

        success = update_user_entitlements(user_id, is_premium=grant_premium if grant_premium else None,
                                           allowed_tools=tools if tools else None)
        if not success:
            return jsonify({'ok': False, 'error': 'Failed to apply entitlements'}), 500

        user = get_user_by_id(user_id)
        return jsonify({'ok': True, 'message': 'Coupon applied', 'is_premium': bool(user.get('is_premium')), 'allowed_tools': user.get('allowed_tools')})

    # Web vulnerability scanner API (background scans)
    last_calls = {}
    def rate_limit(max_requests=5, window=60):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                ip = request.remote_addr
                now = time.time()
                if ip not in last_calls:
                    last_calls[ip] = deque()
                # Remove old calls
                while last_calls[ip] and now - last_calls[ip][0] > window:
                    last_calls[ip].popleft()
                if len(last_calls[ip]) >= max_requests:
                    return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
                last_calls[ip].append(now)
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    active_scans = {}

    @app.route('/api/scan', methods=['POST'])
    @rate_limit(max_requests=3, window=60)
    def start_scan():
        data = request.get_json(silent=True) or {}
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

        scan_id = f"scan_{int(time.time())}_{request.remote_addr.replace('.', '_')}"
        active_scans[scan_id] = {"status": "running", "target": target, "started_at": time.time()}
        thread = threading.Thread(target=run_scan, args=(scan_id, target), daemon=True)
        thread.start()
        return jsonify({"scan_id": scan_id, "status": "started", "target": target})

    @app.route('/api/scan/<scan_id>', methods=['GET'])
    def get_scan_status(scan_id: str):
        scan = active_scans.get(scan_id)
        if not scan:
            return jsonify({"error": "Scan not found"}), 404
        if scan.get('status') == 'complete':
            return jsonify({"status": "complete", "target": scan.get('target'), "results": scan.get('results')})
        if scan.get('status') == 'error':
            return jsonify({"status": "error", "error": scan.get('error')})
        return jsonify({"status": "running", "target": scan.get('target')})

    # DoS control endpoints
    @app.route('/api/start_dos', methods=['POST'])
    def start_dos():
        if app.detection_active:
            return jsonify({"status": "Already running"})

        data = request.get_json(silent=True) or {}
        mode = data.get('mode', 'pcap')
        log_path = data.get('log_path')

        def run_detector():
            try:
                if not app.detector:
                    return
                app.detector.start(mode=mode, log_path=log_path)
            except Exception as e:
                print(f"Detector error: {e}")

        app.detection_thread = threading.Thread(target=run_detector, daemon=True)
        app.detection_thread.start()
        app.detection_active = True
        return jsonify({"status": "DoS detection started"})

    @app.route('/api/stop_dos', methods=['POST'])
    def stop_dos():
        # Graceful stop: flip running flags on detector if available
        if app.detector and hasattr(app.detector, 'running'):
            try:
                app.detector.running = False
            except Exception:
                pass
        app.detection_active = False
        return jsonify({"status": "DoS detection stopped"})

    @app.route('/api/unblock', methods=['POST'])
    def unblock():
        data = request.get_json(silent=True) or {}
        ip = data.get('ip')
        try:
            import subprocess
            subprocess.run(['sudo', 'iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)
            # Try to remove from detector/mitigator state if available
            try:
                if app.detector and hasattr(app.detector, 'mitigator'):
                    app.detector.mitigator.blocked_ips.pop(ip, None)
            except Exception:
                pass
            return jsonify({"status": f"Unblocked {ip}"})
        except Exception:
            return jsonify({"status": f"Failed to unblock {ip}"})
    return app
