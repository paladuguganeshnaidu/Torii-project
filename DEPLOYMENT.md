# Deployment Guide - Torii Project

## ⚠️ CRITICAL: Database Persistence on Render

**IMPORTANT:** If deploying to Render, you **MUST** use PostgreSQL to prevent data loss!

### Why SQLite Loses Data on Render:
- ❌ SQLite files are stored in the container's filesystem
- ❌ Render **wipes all files** on every deployment or restart
- ❌ **All user data gets deleted** when you redeploy your code
- ❌ Not suitable for production!

### Solution: Use PostgreSQL
- ✅ **PostgreSQL stores data externally** (separate from your app container)
- ✅ **Data persists** across deployments and restarts
- ✅ **800 MB free tier** available on Render
- ✅ Production-ready and scalable

---

## Database Setup

Your app now uses a **smart database adapter** with priority:
1. ✅ **PostgreSQL** (recommended for Render) - Set `DATABASE_URL` environment variable
2. ✅ **MySQL** (good for local development) - Set `MYSQL_HOST` environment variables
3. ✅ **SQLite** (fallback only) - No setup needed, but **NOT for production**

---

## Local Development (Your Laptop)

### Option A: Use MySQL Workbench

1. **Create database in MySQL Workbench:**
```sql
CREATE DATABASE torii CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'torii_user'@'localhost' IDENTIFIED BY 'YourPassword123!';
GRANT ALL PRIVILEGES ON torii.* TO 'torii_user'@'localhost';
FLUSH PRIVILEGES;
```

2. **Create `.env` file:**
```powershell
Copy-Item .env.example .env
notepad .env
```

3. **Edit `.env` with your MySQL credentials:**
```
SECRET_KEY=dev-secret-key-change-in-production
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=torii_user
MYSQL_PASSWORD=YourPassword123!
MYSQL_DB=torii
MYSQL_USE_SSL=false
```

4. **Run the app:**
```powershell
.\start.ps1
```

5. **Test registration:**
- Open: http://127.0.0.1:5000/auth/register
- Register a user
- Check in MySQL Workbench:
```sql
SELECT * FROM users ORDER BY id DESC LIMIT 5;
```

### Option B: Use SQLite (even simpler)

1. **Create `.env` file with just SECRET_KEY:**
```
SECRET_KEY=dev-secret-key-change-in-production
```

2. **Run the app:**
```powershell
.\start.ps1
```

3. **Database auto-created at:** `database/app.db`

---

## Cloud Deployment (Render) - WITH POSTGRESQL ✅

### 🚨 CRITICAL SETUP: PostgreSQL Database (DO THIS FIRST!)

Without PostgreSQL, **all user data will be deleted** on every deployment!

#### Step 1: Create PostgreSQL Database

1. **Go to Render Dashboard:** https://dashboard.render.com/
2. **Click "New +"** (top right) → Select **"PostgreSQL"**
3. **Fill in the form:**
   - **Name:** `torii-database` (or any name you like)
   - **Database:** `torii` (or leave default)
   - **User:** Leave default (auto-generated)
   - **Region:** **SAME as your web service region** (important!)
   - **PostgreSQL Version:** Leave default (16)
   - **Datadog API Key:** Leave blank
   - **Plan:** Select **"Free"** (800 MB storage, perfect for 1,500-2,000 users)
4. **Click "Create Database"**
5. **Wait 2-3 minutes** for database to provision

#### Step 2: Copy Database URL

1. **On the database page**, scroll down to **"Connections"** section
2. **Find "Internal Database URL"** (looks like: `postgres://user:pass@dpg-xxxxx/dbname`)
3. **Click the copy icon** to copy the full URL
4. **IMPORTANT:** Keep this URL safe - it contains your database password!

#### Step 3: Connect Web Service to PostgreSQL

1. **Go back to Render Dashboard**
2. **Click on your Torii web service**
3. **Go to "Environment" tab** (left sidebar)
4. **Click "Add Environment Variable"**
5. **Add the database URL:**
   - **Key:** `DATABASE_URL`
   - **Value:** Paste the Internal Database URL you copied
   - Example: `postgres://torii_user:abc123xyz@dpg-xxxxx-a.oregon-postgres.render.com/torii_db`
6. **Click "Save Changes"**

Your app will **automatically redeploy** and connect to PostgreSQL!

#### Step 4: Add SECRET_KEY (if not already set)

1. Still in **"Environment" tab**
2. **Click "Add Environment Variable"**
3. Add:
   - **Key:** `SECRET_KEY`
   - **Value:** Generate with PowerShell:
     ```powershell
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
4. **Click "Save Changes"**

#### Step 5: Verify PostgreSQL Connection

1. **Wait for deployment to complete** (watch the "Events" tab)
2. **Open your admin dashboard:** `https://your-app.onrender.com/admin/dashboard`
   - Default admin password: `admin123` (change this in production!)
3. **Check "Database Type" card:**
   - ✅ **Should show "POSTGRES"** (you're safe!)
   - ❌ **If shows "SQLITE"** → DATABASE_URL not set correctly, go back to Step 3

   ---

   ## Premium Tools & Coupon Setup (Optional)

   You can restrict some tools to selected users and unlock them via a coupon code.

   Set these environment variables in Render → Your Service → Environment:

   - `COUPON_CODE` – The coupon users must input (e.g., `TORII2025`)
   - `PREMIUM_PAGES` – Comma-separated filenames to restrict (e.g., `tool7-stegoshield-inspector.html,tool8-stegoshield-extractor.html`)
   - `COUPON_GRANT_PREMIUM` – Set to `true` to grant access to all premium pages on redeem
   - `PREMIUM_ALLOWED_TOOLS` – If not granting full premium, list exact filenames to unlock upon redeem

   Users must be logged in to redeem. Access is enforced server-side when requesting premium pages.

#### Step 6: Monitor Your Database

The admin dashboard shows:
- **Database Type:** POSTGRES/MYSQL/SQLITE
- **Total Users:** Current user count
- **Storage Used:** X MB / 800 MB (with percentage bar)
- **Recent Registrations:** Users added in last 7 days
- **Alerts:** Warnings if using SQLite or running low on storage

Dashboard auto-refreshes every 30 seconds.

---

## Cloud Deployment (Render) - Quick Deploy

### Step 1: Push code to GitHub

```powershell
cd C:\python\Torii-Project
git add .
git commit -m "Deploy with PostgreSQL support"
git push origin main
```

### Step 2: Deploy to Render

1. Go to: https://render.com/dashboard
2. Click **"New"** → **"Web Service"**
3. Connect your GitHub repository: `Torii-Project`
4. Render will auto-detect `render.yaml`
5. Click **"Create Web Service"**

### Step 7: Wait for deployment

- Watch the build logs in the "Events" tab
- When you see **"Your service is live"**, copy the URL
- Example: `https://torii-project.onrender.com`

### Step 8: Test registration (with PostgreSQL!)

1. Open: `https://your-url.onrender.com/auth/register`
2. Register a test user
3. Should see: "Registered successfully"
4. **Redeploy your app** (push a small change to GitHub)
5. **Check if user still exists** → Login with same email
6. ✅ **User persists!** Your data is safe with PostgreSQL

**Done! Your site is live with persistent PostgreSQL storage.** 🎉

---

## How It Works Now

```
┌──────────────────────────────────────────┐
│   YOUR LAPTOP (Development)              │
│   Option 1: MySQL Workbench              │
│   - .env has MYSQL_HOST set              │
│   → App uses MySQL                       │
│                                          │
│   Option 2: Simple development           │
│   - No database configured               │
│   → App uses SQLite (database/app.db)    │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│   RENDER (Production) ✅                 │
│   - DATABASE_URL environment variable    │
│   → App uses PostgreSQL                  │
│   → Data persists across deployments    │
│   → 800 MB free storage                  │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│   RENDER (Without PostgreSQL) ❌         │
│   - No DATABASE_URL set                  │
│   → App uses SQLite (DANGEROUS!)         │
│   → Data deleted on every deploy         │
│   → Users lost after restart             │
└──────────────────────────────────────────┘
```

**Database Priority:**
1. **PostgreSQL** (if DATABASE_URL is set) ← Production
2. **MySQL** (if MYSQL_HOST is set) ← Local development
3. **SQLite** (fallback) ← Development only, NOT for production!

---

## Troubleshooting

### Local Development Issues

#### "Registration failed"
- Check MySQL Workbench is running
- Verify `.env` has correct credentials
- Test connection in MySQL Workbench first

#### SQLite file locked
- Close any DB Browser for SQLite connections
- Restart the Flask app

### Render Deployment Issues

#### "Application Error"
- Check Render logs for errors
- Verify SECRET_KEY is set in Environment
- Make sure you pushed latest code to GitHub

#### ❌ Admin Dashboard shows "SQLITE" (CRITICAL!)
**Problem:** Your app is using SQLite on Render - data will be deleted on next deploy!

**Solution:**
1. Go to Render Dashboard → Create PostgreSQL database (see steps above)
2. Copy "Internal Database URL"
3. Add DATABASE_URL environment variable to your web service
4. Wait for auto-redeploy
5. Refresh admin dashboard → should now show "POSTGRES" ✅

#### Users disappeared after deployment
**Cause:** You were using SQLite before setting up PostgreSQL

**Why:** SQLite files get wiped on every Render deployment

**Solution:**
1. Set up PostgreSQL immediately (see steps above)
2. Users will need to re-register (old SQLite data is lost)
3. From now on, data will persist with PostgreSQL

#### "Connection to server closed"
- Check DATABASE_URL is correctly copied (no extra spaces)
- Verify PostgreSQL database is in **same region** as web service
- Check PostgreSQL database is running (green status in Render)

#### Storage usage > 80%
- Check admin dashboard for recommendations
- Delete old tool_logs: Access `/admin/debug-db` and run cleanup queries
- Consider upgrading to paid PostgreSQL plan for more storage

### Database Connection Errors

#### "psycopg2.OperationalError"
- DATABASE_URL is incorrect or PostgreSQL is down
- Check PostgreSQL database status in Render dashboard
- Verify URL starts with `postgres://` or `postgresql://`

#### "mysql.connector.errors.ProgrammingError"
- Check MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD in `.env`
- Verify MySQL Workbench is running
- Test connection in MySQL Workbench first

### Data Management

#### "Email is already registered"
Delete from database:

**PostgreSQL (Render):**
```sql
-- Access via Render dashboard → PostgreSQL → "Connect" → "PSQL Command"
DELETE FROM users WHERE email = 'test@example.com';
```

**MySQL (Local):**
```sql
-- In MySQL Workbench
DELETE FROM users WHERE email = 'test@example.com';
```

**SQLite (Local):**
```sql
-- Use DB Browser for SQLite
DELETE FROM users WHERE email = 'test@example.com';
```

---

## Database File Locations

- **PostgreSQL (Render):** Managed by Render, accessed via admin dashboard or PSQL
- **MySQL (Local):** Managed by MySQL Workbench
- **SQLite (Local):** `database/app.db` (gitignored, won't commit to GitHub)

---

## Storage Capacity (Render Free Tier)

**PostgreSQL Free Plan:** 800 MB storage

**Estimated Capacity:**
- Average user record: ~300 bytes
- Average tool log: ~2 KB
- **Conservative estimate:** 1,500-2,000 users with 50-100 scans each
- **Optimistic estimate:** 2,500-3,000 users if mostly inactive

**Monitor storage:**
- Check admin dashboard: `/admin/dashboard`
- Storage bar turns orange at 80% usage
- Red alert at 95% usage

**Cleanup recommendations:**
- Delete tool_logs older than 90 days
- Archive inactive users (not logged in for 6+ months)
- Upgrade to paid plan ($7/month for 10 GB) if needed

---

## Admin Dashboard Features

Access: `https://your-app.onrender.com/admin/dashboard`

**Login:** `admin` / `admin123` (change in production!)

**Dashboard shows:**
- ✅ Database type (POSTGRES/MYSQL/SQLITE)
- ✅ Total users count
- ✅ Total tool logs count
- ✅ Recent registrations (last 7 days)
- ✅ Storage usage (MB and percentage)
- ✅ Storage bar (green → orange → red)
- ✅ Cleanup recommendations
- ✅ Auto-refresh every 30 seconds

**Alerts:**
- 🚨 Red alert if using SQLite (data loss risk)
- ⚠️ Orange warning if storage > 80%
- 🚨 Red alert if storage > 95%

---

## Next Steps - Production Checklist

### Before Going Live:

- [ ] ✅ Set up PostgreSQL database on Render
- [ ] ✅ Add DATABASE_URL environment variable
- [ ] ✅ Verify admin dashboard shows "POSTGRES"
- [ ] ✅ Test user registration and login
- [ ] ✅ Redeploy and verify users persist
- [ ] ✅ Change admin password from default
- [ ] ✅ Generate strong SECRET_KEY (32+ characters)
- [ ] ✅ Test all 8 security tools
- [ ] ✅ Monitor storage usage weekly

### After Launch:

- [ ] Set up monitoring alerts for storage usage
- [ ] Schedule monthly database backups
- [ ] Plan cleanup strategy for old logs
- [ ] Monitor user growth vs storage capacity
- [ ] Consider upgrading to paid plan at 70% storage

### Security Hardening:

- [ ] Change admin password (edit `Backend/admin.py` hash)
- [ ] Use environment variable for admin password
- [ ] Enable HTTPS only (Render provides free SSL)
- [ ] Add rate limiting for API endpoints
- [ ] Set up error monitoring (Sentry, etc.)

---

## FAQ

### Why PostgreSQL instead of MySQL on Render?
- PostgreSQL is natively supported by Render with free tier
- MySQL requires paid plan ($7/month minimum)
- PostgreSQL is production-ready and scalable

### Can I use SQLite on Render?
- **NO!** SQLite data gets deleted on every deployment
- Only use SQLite for local development/testing
- Always use PostgreSQL for production on Render

### What happens to old SQLite data when I switch to PostgreSQL?
- Old SQLite data is NOT automatically migrated
- Users will need to re-register
- PostgreSQL starts with empty database
- This is a one-time migration, then data persists forever

### How do I backup my PostgreSQL database?
1. Go to Render Dashboard → Your PostgreSQL database
2. Click "Backups" tab
3. Render auto-backups daily (retained for 7 days on free tier)
4. Manual backup: Use PSQL command to export data

### Can I connect to PostgreSQL from my local machine?
Yes! Use the "External Database URL" from Render:
```powershell
# Install PostgreSQL client tools
# Then connect:
psql "postgres://user:pass@dpg-xxxxx-a.oregon-postgres.render.com/dbname"
```

### How do I upgrade storage beyond 800 MB?
1. Render Dashboard → PostgreSQL database
2. Click "Upgrade" → Select paid plan
3. Plans start at $7/month for 10 GB

---

## Need Help?

- **Admin Dashboard:** Shows real-time database status
- **Render Logs:** Check "Logs" tab in your web service
- **PostgreSQL Logs:** Check "Logs" tab in your database
- **GitHub Issues:** Report bugs or ask questions

---

**Remember:** Always use PostgreSQL on Render to prevent data loss! 🚨
