@echo off
echo ================================
echo Minecraft Marketplace Bot
echo ================================
echo.

echo [1/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/4] Running migrations...
python manage.py makemigrations
python manage.py migrate

echo.
echo [3/4] Collecting static files...
python manage.py collectstatic --noinput

echo.
echo [4/4] Starting bot...
echo.
echo Bot is starting... Press Ctrl+C to stop
echo.
python manage.py run_bot

pause
