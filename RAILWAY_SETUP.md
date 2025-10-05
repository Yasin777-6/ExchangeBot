# 🚂 Railway Setup Guide

## ⚠️ Important: Environment Variables

Railway **DOES NOT** use your local `.env` file. You must set environment variables in Railway's dashboard!

---

## 📋 Step-by-Step Setup

### 1. Add PostgreSQL Database

1. Go to your Railway project
2. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically create `DATABASE_URL` variable

### 2. Set Environment Variables

Go to your service → **Variables** tab and add:

```
TELEGRAM_BOT_TOKEN=8400316541:AAH6TWxxscPwulDlWJ1ZNDP5dCHBR4FwSXM
DEBUG=False
ALLOWED_HOSTS=*.railway.app,*.up.railway.app
SECRET_KEY=your-random-secret-key-here
CSRF_TRUSTED_ORIGINS=https://exchangebot-production-8f2a.up.railway.app
```

**Important Notes:**
- `DATABASE_URL` is automatically provided by Railway's PostgreSQL
- If you don't see `DATABASE_URL`, make sure PostgreSQL is added
- `SECRET_KEY` should be a long random string

### 3. Generate SECRET_KEY

Run this locally to generate a secret key:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and set it as `SECRET_KEY` in Railway.

---

## 🔍 Check Railway Logs

1. Go to your Railway service
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. View **"Deploy Logs"** and **"Build Logs"**

Look for errors like:
- `ModuleNotFoundError` - missing dependency
- `django.db.utils.*` - database issues
- `FATAL: password authentication failed` - wrong DATABASE_URL

---

## 🐛 Common Issues

### Issue: 502 Bad Gateway

**Cause:** App failed to start

**Solutions:**
1. Check Railway logs for error messages
2. Verify all environment variables are set
3. Ensure `DATABASE_URL` exists (add PostgreSQL if missing)
4. Check that `PORT` is not hardcoded (Railway provides it)

### Issue: Database Connection Error

**Cause:** Missing or wrong DATABASE_URL

**Solutions:**
1. Make sure PostgreSQL service is added
2. Check `DATABASE_URL` format: `postgresql://user:pass@host:port/db`
3. Try reconnecting the database in Railway

### Issue: Static Files Not Loading

**Cause:** `collectstatic` not running

**Solutions:**
1. Check build logs - should see "Collecting static files..."
2. Verify `railway_start.sh` is executable
3. Run manually: `python manage.py collectstatic --noinput`

---

## ✅ Verify Deployment

After deployment, check:

1. **Home Page** (should return JSON):
   ```
   https://exchangebot-production-8f2a.up.railway.app/
   ```

2. **Health Check**:
   ```
   https://exchangebot-production-8f2a.up.railway.app/health/
   ```

3. **Admin Panel**:
   ```
   https://exchangebot-production-8f2a.up.railway.app/admin/
   ```

4. **Set Webhook**:
   ```
   https://exchangebot-production-8f2a.up.railway.app/bot/set-webhook/
   ```

---

## 🔧 Manual Deployment Steps

If automatic deployment fails:

### 1. Connect to Railway Shell

In Railway dashboard, click **"Shell"** or use CLI:
```bash
railway shell
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Setup Webhook
```bash
python manage.py setup_webhook --url https://exchangebot-production-8f2a.up.railway.app/bot/webhook/
```

---

## 📊 Environment Variables Reference

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | `postgresql://...` | Auto-provided by Railway PostgreSQL |
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | `123456:ABC-DEF...` | From @BotFather |
| `SECRET_KEY` | ✅ Yes | Random string | Django secret key |
| `DEBUG` | ⚠️ Production | `False` | Debug mode (False for production) |
| `ALLOWED_HOSTS` | ⚠️ Production | `*.railway.app` | Allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | ⚠️ Production | `https://your-app.railway.app` | CSRF trusted domains |
| `PORT` | ❌ No | Auto-provided | Railway provides this automatically |

---

## 🚀 Redeploy

After changing environment variables or code:

1. **Automatic:** Push to GitHub
   ```bash
   git add .
   git commit -m "Update"
   git push
   ```

2. **Manual:** In Railway dashboard
   - Click **"Deploy"** → **"Redeploy"**

---

## 📝 Quick Checklist

Before asking for help, verify:

- [ ] PostgreSQL database is added to Railway project
- [ ] `DATABASE_URL` exists in variables (auto-created with PostgreSQL)
- [ ] `TELEGRAM_BOT_TOKEN` is set correctly
- [ ] `SECRET_KEY` is set (not empty)
- [ ] `DEBUG=False` for production
- [ ] `ALLOWED_HOSTS` includes your Railway domain
- [ ] Deployment logs show no errors
- [ ] Home page (`/`) returns JSON response
- [ ] Health check (`/health/`) returns "OK"

---

## 🎯 Next Steps After Successful Deployment

1. ✅ Create Django superuser (via Railway shell)
2. ✅ Create bot admin user (via Django shell)
3. ✅ Set webhook: Visit `/bot/set-webhook/`
4. ✅ Test bot in Telegram with `/start`
5. ✅ Monitor logs for any issues

Good luck! 🚀
