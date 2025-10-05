web: gunicorn exchange.wsgi --log-file -
release: python manage.py migrate && python manage.py setup_webhook --url https://exchangebot-production-8f2a.up.railway.app/bot/webhook/
