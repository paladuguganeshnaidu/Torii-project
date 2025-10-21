# 🔐 Admin Panel Setup Guide

## ✅ What's Been Added

Your site now has a **secure, password-protected admin panel** where you can view all registered users.

**Security Features:**
- 🔒 Password-protected login
- ✅ Session-based authentication
- ✅ Protected against SQL injection
- ✅ Hashed passwords (not stored in plain text)
- ✅ Logout functionality
- ⚠️ Warning message for unauthorized access

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Set Your Admin Password in Render

1. **Go to Render Dashboard**: https://render.com/dashboard
2. **Click on your service**: `torii-project`
3. **Go to "Environment" tab**
4. **Click "+ Add Environment Variable"**
5. **Add this (recommended - hashed):**
   - **Key**: `ADMIN_PASSWORD`
   - **Value**: `scrypt:32768:8:1$xgInVDOssyMWNUsh$161cba3e03e41893ab4c85979d6d146d599a793972152731eed1b28108a08553429604eb00e6c979914b0d211198ef75d774924d298e2d156c754d69345b9e90`

   Or set plaintext (easiest for first run):
   - **Key**: `ADMIN_PASSWORD`
   - **Value**: `admin123`

6. **Click "Save Changes"**

### Step 2: Redeploy on Render

1. **Click "Manual Deploy"** (top right)
2. **Select "Deploy latest commit"**
3. **Wait 2-3 minutes** for deployment

### Step 3: Access Admin Panel

1. **Go to**: https://torii-project.onrender.com/admin/login
2. **Enter password**: `admin123`
3. **Click "Login"**
4. **You'll see all registered users!** 🎉

---

## 🔐 IMPORTANT: Change Default Password!

The default password `admin123` is **WEAK**. Change it immediately:

### Generate Your Own Secure Password Hash (recommended):

```powershell
# On your laptop, run:
py -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourStrongPassword123!'))"
```

**Copy the output** and update `ADMIN_PASSWORD` in Render's Environment tab.
If you prefer, you can also set `ADMIN_PASSWORD` to your plaintext value, and the app will hash it at startup.

---

## 📊 Admin Panel Features

### Login Page (`/admin/login`)
- 🔒 Password-protected
- ⚠️ Warning for unauthorized users
- ✅ Secure session management

### Users Dashboard (`/admin/users`)
- 👥 View all registered users
- 📧 See emails
- 📱 See mobile numbers
- 🕒 See registration timestamps
- 📊 Total user count
- 🚪 Logout button

---

## 🌐 URLs

| Page | URL |
|------|-----|
| **Admin Login** | https://torii-project.onrender.com/admin/login |
| **View Users** | https://torii-project.onrender.com/admin/users |
| **Logout** | https://torii-project.onrender.com/admin/logout |

---

## 🛡️ Security Notes

✅ **SQL Injection Protected**: All queries are parameterized  
✅ **Session-Based**: Must login to access  
✅ **Hashed Passwords**: Never stored in plain text  
✅ **HTTPS**: All traffic encrypted  
❌ **No Public Access**: Only you know the admin URL  

### Best Practices:
- ✅ Use a strong password (12+ characters, mixed case, numbers, symbols)
- ✅ Never share your admin password
- ✅ Change default password immediately
- ✅ Logout when done viewing users
- ❌ Don't share the admin URL publicly

---

## 🎯 How to Use

### View Your Friend's Registration:

1. Open: https://torii-project.onrender.com/admin/login
2. Enter password: `admin123`
3. Click "Login"
4. You'll see a table with:
   - ID
   - Email (your friend's email)
   - Mobile (your friend's mobile)
   - Registration date/time

### Logout:
- Click the red "Logout" button (top right)
- Or visit: https://torii-project.onrender.com/admin/logout

---

## ⚡ Quick Actions

```powershell
# Generate new admin password hash
py -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NewPassword123'))"

# Push updates to production
git add .
git commit -m "Update admin settings"
git push origin main
```

---

## 🐛 Troubleshooting

### "Invalid admin password"
- Make sure you set `ADMIN_PASSWORD` in Render Environment
- If you used a hash, verify it's complete (no spaces/line breaks)
- If unsure, set `ADMIN_PASSWORD` to `admin123` (plaintext) temporarily and redeploy
- Default password is: `admin123`

### "Please login as admin first"
- You need to login at `/admin/login` first
- Session expires after browser close

### Can't see users
- Make sure users have registered first
- Check Render logs for database errors

---

## 📝 Summary

✅ Secure admin panel deployed  
✅ Password: `admin123` (change immediately!)  
✅ Access: https://torii-project.onrender.com/admin/login  
✅ View your friend's registration details  
✅ Protected against SQL injection  

**Go to Render now and add the `ADMIN_PASSWORD` environment variable, then redeploy!** 🚀
