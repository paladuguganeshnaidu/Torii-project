# Torii-Project

A minimal full-stack starter for a security tools hub. It includes:
- Flask backend with API endpoints for 6 tools
- Simple auth blueprint (register/login/logout) skeleton using Flask sessions
- Jinja templates for a server-rendered dashboard
- Static frontend mock pages

## Structure

- Backend: Flask app, tools, templates, requirements
- frontend: static HTML/CSS demo pages
- database: schema and SQLite DB created on first run

## Quick start (Windows / PowerShell)

Option A: One-liner start script

```powershell
./start.ps1
```

Option B: Manual steps

1) Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
py -m pip install -r Backend/requirements.txt
```

3) Run the app

```powershell
py run.py
```

The Flask dev server will start on http://127.0.0.1:5000. Visit the dashboard at `/`.

Auth pages:
- /auth/register
- /auth/login

API endpoints (POST):
- /api/email-analyzer
- /api/url-scanner
- /api/password-cracker
- /api/sms-spam-tester
- /api/malware-analyzer
- /api/web-recon

## Notes
- Registration now stores users in MySQL with hashed passwords. Configure the following environment variables before running to enable MySQL:
	- `MYSQL_HOST`
	- `MYSQL_PORT` (optional, default 3306)
	- `MYSQL_USER`
	- `MYSQL_PASSWORD`
	- `MYSQL_DB`
	If MySQL is not configured or PyMySQL not installed, registration will be disabled.
- The tools are stub implementations returning placeholder analysis. Replace with real logic as needed.
- The SQLite database file will be created on first run under `database/app.db`.

## Development
- Edit templates in `Backend/templates/`
- Add/extend tools in `Backend/tools/`
- Update configuration in `Backend/config.py`

### VS Code
- Run task: "Run Torii (PowerShell)" from the command palette or Terminal > Run Task
- Debug: Use the "Debug Torii (run.py)" launch configuration
