# 🚀 Deployment Guide - Minecraft Marketplace

## Deployment Options

This project can be deployed on various platforms. Below are instructions for the most popular ones.

---

## 🔵 Railway Deployment (Recommended)

Railway is perfect for this project as it supports both web and worker processes.

### Prerequisites
- Railway account (https://railway.app)
- GitHub account (optional, for automatic deployments)

### Steps:

1. **Install Railway CLI** (optional)
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Create New Project**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo" or "Empty Project"

3. **Add PostgreSQL Database**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically create a database

4. **Configure Environment Variables**
   
   In Railway dashboard, add these variables:
   ```
   TELEGRAM_BOT_TOKEN=8400316541:AAH6TWxxscPwulDlWJ1ZNDP5dCHBR4FwSXM
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   DEBUG=False
   ALLOWED_HOSTS=*.railway.app,*.up.railway.app
   SECRET_KEY=your-secret-key-here
   ```

5. **Deploy**
   - Push your code to GitHub
   - Connect Railway to your GitHub repo
   - Railway will automatically detect Django and deploy

6. **Run Migrations**
   
   In Railway dashboard, open the service and run:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. **Start the Bot**
   
   The Procfile has two processes:
   - `web`: Django web server (for admin panel)
   - `bot`: Telegram bot
   
   Railway will start both automatically.

---

## 🟣 Heroku Deployment

### Prerequisites
- Heroku account (https://heroku.com)
- Heroku CLI installed

### Steps:

1. **Login to Heroku**
   ```bash
   heroku login
   ```

2. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

3. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN=8400316541:AAH6TWxxscPwulDlWJ1ZNDP5dCHBR4FwSXM
   heroku config:set DEBUG=False
   heroku config:set SECRET_KEY=your-secret-key-here
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

6. **Run Migrations**
   ```bash
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

7. **Scale Dynos**
   ```bash
   heroku ps:scale web=1 bot=1
   ```

---

## 🟢 Render Deployment

### Prerequisites
- Render account (https://render.com)

### Steps:

1. **Create New Web Service**
   - Go to Render dashboard
   - Click "New" → "Web Service"
   - Connect your GitHub repo

2. **Configure Build Settings**
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - Start Command: `gunicorn exchange.wsgi`

3. **Add PostgreSQL Database**
   - Click "New" → "PostgreSQL"
   - Copy the Internal Database URL

4. **Set Environment Variables**
   ```
   TELEGRAM_BOT_TOKEN=8400316541:AAH6TWxxscPwulDlWJ1ZNDP5dCHBR4FwSXM
   DATABASE_URL=<your-postgres-url>
   DEBUG=False
   ALLOWED_HOSTS=*.onrender.com
   SECRET_KEY=your-secret-key-here
   ```

5. **Create Background Worker for Bot**
   - Click "New" → "Background Worker"
   - Start Command: `python manage.py run_bot`

---

## 🔴 VPS Deployment (Ubuntu/Debian)

### Prerequisites
- VPS with Ubuntu/Debian
- SSH access
- Domain name (optional)

### Steps:

1. **Update System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Dependencies**
   ```bash
   sudo apt install python3 python3-pip python3-venv postgresql nginx -y
   ```

3. **Create Database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE minecraft_marketplace;
   CREATE USER dbuser WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE minecraft_marketplace TO dbuser;
   \q
   ```

4. **Clone Project**
   ```bash
   cd /var/www
   git clone <your-repo-url> minecraft_marketplace
   cd minecraft_marketplace
   ```

5. **Setup Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Configure Environment**
   ```bash
   nano .env
   ```
   
   Add:
   ```
   TELEGRAM_BOT_TOKEN=8400316541:AAH6TWxxscPwulDlWJ1ZNDP5dCHBR4FwSXM
   DATABASE=postgresql://dbuser:your-password@localhost/minecraft_marketplace
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   SECRET_KEY=your-secret-key-here
   ```

7. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic
   ```

8. **Setup Systemd Services**
   
   Create `/etc/systemd/system/minecraft-web.service`:
   ```ini
   [Unit]
   Description=Minecraft Marketplace Web
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/minecraft_marketplace
   Environment="PATH=/var/www/minecraft_marketplace/venv/bin"
   ExecStart=/var/www/minecraft_marketplace/venv/bin/gunicorn exchange.wsgi:application --bind 0.0.0.0:8000

   [Install]
   WantedBy=multi-user.target
   ```
   
   Create `/etc/systemd/system/minecraft-bot.service`:
   ```ini
   [Unit]
   Description=Minecraft Marketplace Bot
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/minecraft_marketplace
   Environment="PATH=/var/www/minecraft_marketplace/venv/bin"
   ExecStart=/var/www/minecraft_marketplace/venv/bin/python manage.py run_bot

   [Install]
   WantedBy=multi-user.target
   ```

9. **Start Services**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable minecraft-web minecraft-bot
   sudo systemctl start minecraft-web minecraft-bot
   ```

10. **Configure Nginx**
    
    Create `/etc/nginx/sites-available/minecraft_marketplace`:
    ```nginx
    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /static/ {
            alias /var/www/minecraft_marketplace/staticfiles/;
        }
    }
    ```
    
    Enable site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/minecraft_marketplace /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

---

## 📋 Post-Deployment Checklist

After deploying, make sure to:

- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Create admin user in bot (via Django shell):
  ```python
  from bot.models import TelegramUser, UserRole
  admin = TelegramUser.objects.create(
      telegram_id=YOUR_TELEGRAM_ID,
      username='admin',
      role=UserRole.ADMIN
  )
  ```
- [ ] Test bot with `/start` command
- [ ] Verify admin panel access
- [ ] Test complete purchase flow
- [ ] Monitor logs for errors

---

## 🔧 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456:ABC-DEF...` |
| `DATABASE` or `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `DEBUG` | Debug mode (False in production) | `False` |
| `ALLOWED_HOSTS` | Allowed hostnames | `example.com,*.railway.app` |
| `SECRET_KEY` | Django secret key | Random string |

---

## 📊 Monitoring

### Check Bot Status
```bash
# Railway/Heroku
railway logs
heroku logs --tail

# VPS
sudo systemctl status minecraft-bot
sudo journalctl -u minecraft-bot -f
```

### Check Web Status
```bash
# Railway/Heroku
railway logs
heroku logs --tail

# VPS
sudo systemctl status minecraft-web
sudo journalctl -u minecraft-web -f
```

---

## 🆘 Troubleshooting

### Bot Not Responding
1. Check if bot process is running
2. Verify `TELEGRAM_BOT_TOKEN` is correct
3. Check logs for errors
4. Ensure database is accessible

### Database Connection Error
1. Verify `DATABASE_URL` is correct
2. Check if PostgreSQL is running
3. Run migrations again

### Static Files Not Loading
1. Run `python manage.py collectstatic`
2. Check `STATIC_ROOT` and `STATIC_URL` settings
3. Verify Nginx/web server configuration

---

## 🎉 Success!

Your Minecraft Marketplace is now deployed and ready to use!

**Next Steps:**
1. Share bot link with users
2. Monitor transactions
3. Moderate items
4. Collect feedback

Good luck! 🎮💰
