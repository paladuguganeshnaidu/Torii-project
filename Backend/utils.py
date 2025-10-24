import time
import json


def log_alert(message: str, tool_name: str = 'system'):
    """Log an alert message.

    This is intentionally lightweight and robust:
    - Attempts to log via Flask's logger if available
    - Attempts to persist to `tool_logs` table if running inside app context
    - Always prints to stdout as a fallback
    """
    try:
        # Prefer Flask logger when available
        from flask import current_app
        current_app.logger.warning(f"[ALERT] [{tool_name}] {message}")
    except Exception:
        # No Flask app context; print to stdout
        try:
            print(f"[ALERT] [{tool_name}] {message}")
        except Exception:
            pass

    # Try to persist to database if possible (best-effort)
    try:
        from .database import get_db
        db = get_db()
        payload = json.dumps({'message': message, 'time': time.time()})
        try:
            db.execute('INSERT INTO tool_logs(tool_name, input, result) VALUES (?, ?, ?)', (tool_name, '', payload))
            db.commit()
        except Exception:
            # Might be Postgres; try generic execute
            try:
                cursor = db.cursor()
                cursor.execute('INSERT INTO tool_logs(tool_name, input, result) VALUES (%s, %s, %s)', (tool_name, '', payload))
                db.commit()
            except Exception:
                pass
    except Exception:
        # Not running in app context or DB unavailable - ignore
        pass
