import os
from flask import Flask, jsonify, render_template, request, send_from_directory, redirect, url_for

from .config import Config, PROJECT_ROOT
from .database import get_db, close_db, init_db
from .db_adapter import init_database, close_db_connection
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


def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
    app.config.from_object(Config)

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

    # Serve the styled static homepage by default
    @app.route('/')
    def index():
        # Serve the static index.html from the project root to match GitHub Pages styling
        return send_from_directory(PROJECT_ROOT, 'index.html')

    # Also serve /index.html explicitly (links may reference it)
    @app.route('/index.html')
    def static_index_file():
        return send_from_directory(PROJECT_ROOT, 'index.html')

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
        'directory.html',
    }

    @app.route('/<path:filename>')
    def serve_static_pages(filename):
        if filename in _ALLOWED_STATIC_PAGES:
            return send_from_directory(PROJECT_ROOT, filename)
        # Fall through to 404 for unknown static files to avoid exposing the repo
        return render_template('index.html')

    # Simple server-rendered tool routes (optional)
    @app.route('/tool/<name>')
    def tool_page(name):
        return render_template('index.html', active_tool=name)

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

    return app
