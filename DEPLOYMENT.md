# Deployment Guide - Torii Project

## Database Setup

Your app now uses a **smart database adapter** that:
- ✅ Uses **MySQL** when you have it configured (local development with MySQL Workbench)
- ✅ Falls back to **SQLite** when MySQL is not available (Render deployment)

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

## Cloud Deployment (Render)

### Step 1: Push code to GitHub

```powershell
cd C:\python\Torii-Project
git add .
git commit -m "Add MySQL/SQLite hybrid database support"
git push origin main
```

### Step 2: Deploy to Render

1. Go to: https://render.com/dashboard
2. Click **"New"** → **"Web Service"**
3. Connect your GitHub repository: `Torii-Project`
4. Render will auto-detect `render.yaml`
5. Click **"Create Web Service"**

### Step 3: Add SECRET_KEY

1. In Render dashboard → Your service → **"Environment"** tab
2. Click **"Add Environment Variable"**
3. Add:
   - **Name**: `SECRET_KEY`
   - **Value**: Generate with PowerShell:
     ```powershell
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
4. Click **"Save Changes"**

### Step 4: Wait for deployment

- Watch the build logs
- When you see **"Your service is live"**, copy the URL
- Example: `https://torii-project.onrender.com`

### Step 5: Test registration

1. Open: `https://your-url.onrender.com/auth/register`
2. Register a test user
3. Should see: "Registered successfully"

**Done! Your site is live using SQLite (free).**

---

## How It Works

```
┌─────────────────────────────────┐
│   YOUR LAPTOP                   │
│   - MySQL Workbench installed   │
│   - .env has MYSQL_HOST set     │
│   → App uses MySQL              │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│   RENDER (Cloud)                │
│   - No MySQL configured         │
│   - Only SECRET_KEY set         │
│   → App uses SQLite             │
└─────────────────────────────────┘
```

Both store the same data:
- Email
- Mobile
- Hashed password
- Registration timestamp

---

## Troubleshooting

### Local: "Registration failed"
- Check MySQL Workbench is running
- Verify `.env` has correct credentials
- Test connection in MySQL Workbench first

### Render: "Application Error"
- Check Render logs for errors
- Verify SECRET_KEY is set in Environment
- Make sure you pushed latest code to GitHub

### "Email is already registered"
- Delete from database:
```sql
-- MySQL
DELETE FROM users WHERE email = 'test@example.com';

-- SQLite (use DB Browser for SQLite)
DELETE FROM users WHERE email = 'test@example.com';
```

---

## Database File Locations

- **MySQL**: Managed by MySQL Workbench
- **SQLite**: `database/app.db` (gitignored, won't commit)

---

## Next Steps

- [ ] Test local registration with MySQL
- [ ] Push to GitHub
- [ ] Deploy to Render
- [ ] Test live registration with SQLite
- [ ] Share your live URL!

Need help? Check the build logs or ask for assistance.
