# Testing Premium Coupon Feature Locally

## ✅ App is Running
The Flask development server is running at: http://127.0.0.1:5000

## 🔧 Environment Variables Set (in .env)
```
COUPON_CODE=TORIITOOLS25
COUPON_GRANT_PREMIUM=true
PREMIUM_PAGES=tool7-stegoshield-inspector.html,tool8-stegoshield-extractor.html
```

## 📝 Test Steps

### 1. Register a New User
1. Go to: http://127.0.0.1:5000/auth/register
2. Fill in:
   - Email: test@example.com
   - Mobile: (optional)
   - Password: test123
   - Confirm Password: test123
3. Click "Register"
4. You should be redirected to the homepage

### 2. Verify Login Works
1. If logged out, go to: http://127.0.0.1:5000/auth/login
2. Enter:
   - Email: test@example.com
   - Password: test123
3. Click "Login"
4. You should see your email in the top-right corner

### 3. Check Premium Tools (Before Coupon)
- On the homepage, you should see only 6 tools
- Tool 7 (StegoShield Inspector) and Tool 8 (StegoShield Extractor) should be **hidden**

### 4. Redeem Coupon Code
1. While logged in on the homepage, look for the coupon input field
2. Enter: **TORIITOOLS25**
3. Click "Redeem"
4. You should see "Coupon applied!" message

### 5. Verify Premium Access
- Refresh the page or check immediately
- Tool 7 and Tool 8 should now be **visible**
- Click on them to verify you can access the pages

### 6. Test Persistence
1. Logout: http://127.0.0.1:5000/auth/logout
2. Login again with the same credentials
3. Premium tools should still be visible (entitlements persisted in database)

## 🔍 Troubleshooting Login Issues

### If login doesn't work:

1. **Check database**:
```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('database/app.db'); cur = conn.cursor(); cur.execute('SELECT email, is_premium FROM users'); print(cur.fetchall())"
```

2. **Check password hash**:
- The password is hashed with Werkzeug's `generate_password_hash`
- Login uses `check_password_hash` to verify
- Common issue: email case sensitivity (handled with LOWER())

3. **Check Flask logs**:
- Look at the terminal running `run.py`
- Login attempts print debug messages:
  - `[LOGIN] Success: email@example.com` (successful)
  - `[LOGIN] User not found: email@example.com` (no user)
  - `[LOGIN] Invalid password for: email@example.com` (wrong password)

4. **Reset database** (if needed):
```powershell
Remove-Item database\app.db
.\.venv\Scripts\python.exe run.py
# Then register a new user
```

## 🚀 Deploy to Render

Once local testing works, set these environment variables on Render:

```
COUPON_CODE=TORIITOOLS25
COUPON_GRANT_PREMIUM=true
PREMIUM_PAGES=tool7-stegoshield-inspector.html,tool8-stegoshield-extractor.html
PREMIUM_ALLOWED_TOOLS=tool7-stegoshield-inspector.html,tool8-stegoshield-extractor.html
```

Go to: Render Dashboard → Your Service → Environment → Add Environment Variables

## 📊 Expected Behavior

| Action | Result |
|--------|--------|
| Visit homepage (logged out) | Only 6 tools visible, no coupon input |
| Register/Login | Coupon input appears, still only 6 tools |
| Redeem coupon | Success message, 8 tools now visible |
| Direct access to tool7 | Allowed after coupon redemption |
| Direct access (no coupon) | Redirected to homepage or login |
| Logout and login again | Premium access persists |

## 🐛 Current Status

- ✅ Database schema updated with `is_premium` and `allowed_tools` columns
- ✅ API endpoint `/api/redeem-coupon` working
- ✅ Frontend UI shows/hides premium tools based on entitlements
- ✅ Server-side access control enforces premium pages
- ✅ Environment variables configured in `.env`
- 🔄 Local testing in progress (app running on port 5000)

---

**Next**: Test the complete flow above, then push to GitHub to trigger Render deployment.
