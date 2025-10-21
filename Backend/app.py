import os
from flask import Flask, jsonify, render_template, request

from .config import Config
from .database import get_db, close_db, init_db
from .db_adapter import init_database, close_db_connection
from .auth import bp as auth_bp
from .tools.email_analyzer import analyze_email_tool
from .tools.url_scanner import scan_url_tool
from .tools.password_cracker import crack_hash_tool
from .tools.sms_spam_detector import test_sms_tool
from .tools.malware_analyzer import analyze_file_tool
from .tools.web_recon import recon_target_tool


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

    # Teardown
    app.teardown_appcontext(close_db)
    app.teardown_appcontext(close_db_connection)

    @app.route('/')
    def index():
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
