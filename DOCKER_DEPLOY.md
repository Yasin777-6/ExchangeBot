# 🐳 Docker Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker installed (https://www.docker.com/get-started)
- Docker Compose installed (usually comes with Docker Desktop)

---

## 🚀 Local Development with Docker

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd exchange
```

### 2. Create .env file
```bash
# Copy the existing .env or create new one
TELEGRAM_BOT_TOKEN=8400316541:AAH6TWxxscPwulDlWJ1ZNDP5dCHBR4FwSXM
DATABASE=postgresql://postgres:postgres@db:5432/minecraft_marketplace
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SECRET_KEY=your-secret-key-here
```

### 3. Build and run
```bash
docker-compose up --build
```

This will:
- Create PostgreSQL database
- Build the application
- Run migrations
- Start web server (port 8000)
- Start Telegram bot

### 4. Create admin user

In a new terminal:
```bash
# Create Django superuser
docker-compose exec web python manage.py createsuperuser

# Create bot admin
docker-compose exec web python manage.py shell
```

Then in the shell:
```python
from bot.models import TelegramUser, UserRole

admin = TelegramUser.objects.create(
    telegram_id=YOUR_TELEGRAM_ID,  # Replace with your Telegram ID
    username='admin',
    first_name='Admin',
    role=UserRole.ADMIN
)
print(f"✅ Admin created: {admin}")
exit()
```

### 5. Access the application
- **Admin Panel**: http://localhost:8000/admin
- **Bot**: Open Telegram and start chatting with your bot

---

## 🌐 Production Deployment with Docker

### Option 1: Railway with Docker

1. **Create `railway.toml`**:
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "python manage.py migrate && python manage.py run_bot"
```

2. **Push to Railway**:
```bash
railway login
railway init
railway up
```

3. **Add PostgreSQL**:
- In Railway dashboard: New → Database → PostgreSQL
- Railway will automatically set DATABASE_URL

4. **Set environment variables** in Railway dashboard:
```
TELEGRAM_BOT_TOKEN=your-token
DEBUG=False
ALLOWED_HOSTS=*.railway.app
SECRET_KEY=your-secret-key
```

---

### Option 2: Heroku with Docker

1. **Install Heroku CLI and login**:
```bash
heroku login
heroku container:login
```

2. **Create Heroku app**:
```bash
heroku create your-app-name
```

3. **Add PostgreSQL**:
```bash
heroku addons:create heroku-postgresql:mini
```

4. **Set environment variables**:
```bash
heroku config:set TELEGRAM_BOT_TOKEN=your-token
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
```

5. **Create `heroku.yml`**:
```yaml
build:
  docker:
    web: Dockerfile
    bot: Dockerfile
run:
  web: gunicorn exchange.wsgi:application --bind 0.0.0.0:$PORT
  bot: python manage.py run_bot
```

6. **Deploy**:
```bash
heroku stack:set container
git push heroku main
```

7. **Scale dynos**:
```bash
heroku ps:scale web=1 bot=1
```

---

### Option 3: VPS with Docker

1. **Install Docker on VPS**:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Clone repository**:
```bash
git clone <your-repo-url>
cd exchange
```

3. **Create production .env**:
```bash
nano .env
```

Add:
```
TELEGRAM_BOT_TOKEN=your-token
DATABASE=postgresql://postgres:your-password@db:5432/minecraft_marketplace
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
SECRET_KEY=your-secret-key
```

4. **Update docker-compose.yml for production**:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=minecraft_marketplace
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your-secure-password
    restart: always

  web:
    build: .
    command: gunicorn exchange.wsgi:application --bind 0.0.0.0:8000 --workers 3
    volumes:
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    restart: always

  bot:
    build: .
    command: python manage.py run_bot
    env_file:
      - .env
    depends_on:
      - db
    restart: always

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  static_volume:
```

5. **Create nginx.conf**:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /static/ {
            alias /app/staticfiles/;
        }
    }
}
```

6. **Deploy**:
```bash
docker-compose up -d --build
```

7. **Run migrations**:
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

8. **Create bot admin**:
```bash
docker-compose exec web python manage.py shell
```

---

## 📋 Docker Commands Reference

### Basic Commands
```bash
# Build and start all services
docker-compose up --build

# Start in detached mode (background)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f bot
docker-compose logs -f web

# Restart a service
docker-compose restart bot

# Execute command in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell

# View running containers
docker-compose ps

# Remove all containers and volumes
docker-compose down -v
```

### Maintenance Commands
```bash
# Create database backup
docker-compose exec db pg_dump -U postgres minecraft_marketplace > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres minecraft_marketplace < backup.sql

# View database
docker-compose exec db psql -U postgres -d minecraft_marketplace

# Rebuild specific service
docker-compose up -d --build bot

# Scale services (if needed)
docker-compose up -d --scale bot=2
```

---

## 🔧 Troubleshooting

### Bot not starting
```bash
# Check logs
docker-compose logs bot

# Restart bot
docker-compose restart bot

# Rebuild bot
docker-compose up -d --build bot
```

### Database connection error
```bash
# Check if database is running
docker-compose ps

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Clear everything and start fresh
```bash
docker-compose down -v
docker-compose up --build
```

---

## 📊 Monitoring

### View resource usage
```bash
docker stats
```

### View container details
```bash
docker-compose ps
docker inspect <container-id>
```

### Access container shell
```bash
docker-compose exec web bash
docker-compose exec bot bash
docker-compose exec db bash
```

---

## 🎉 Success!

Your Minecraft Marketplace is now running in Docker!

**Services:**
- 🌐 Web (Admin Panel): http://localhost:8000/admin
- 🤖 Telegram Bot: Running in background
- 🗄️ PostgreSQL: Running on port 5432

**Next Steps:**
1. ✅ Create admin users
2. ✅ Test bot functionality
3. ✅ Monitor logs
4. ✅ Deploy to production

Good luck! 🎮💰
