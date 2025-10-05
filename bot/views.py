from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import logging
import asyncio
from telegram import Update, Bot
from .telegram_webhook import get_application

logger = logging.getLogger(__name__)

def run_async(coro):
    """Запустить async функцию в синхронном контексте"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

@csrf_exempt
def telegram_webhook(request):
    """Обработка webhook от Telegram"""
    if request.method == 'POST':
        try:
            # Получаем данные от Telegram
            update_data = json.loads(request.body.decode('utf-8'))
            
            # Получаем application
            app = get_application()
            
            # Создаем объект Update
            update = Update.de_json(update_data, app.bot)
            
            # Обрабатываем update асинхронно
            run_async(app.process_update(update))
            
            return JsonResponse({'ok': True})
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)
    
    return HttpResponse('Bot webhook endpoint', status=200)

@csrf_exempt
def set_webhook(request):
    """Установить webhook URL"""
    try:
        webhook_url = f"https://{request.get_host()}/bot/webhook/"
        
        app = get_application()
        run_async(app.bot.set_webhook(webhook_url))
        
        return JsonResponse({
            'ok': True,
            'webhook_url': webhook_url,
            'message': 'Webhook установлен успешно!'
        })
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}", exc_info=True)
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@csrf_exempt
def delete_webhook(request):
    """Удалить webhook"""
    try:
        app = get_application()
        run_async(app.bot.delete_webhook())
        return JsonResponse({
            'ok': True,
            'message': 'Webhook удален успешно!'
        })
    except Exception as e:
        logger.error(f"Ошибка удаления webhook: {e}", exc_info=True)
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@csrf_exempt
def webhook_info(request):
    """Получить информацию о webhook"""
    try:
        app = get_application()
        info = run_async(app.bot.get_webhook_info())
        return JsonResponse({
            'ok': True,
            'url': info.url,
            'has_custom_certificate': info.has_custom_certificate,
            'pending_update_count': info.pending_update_count,
            'last_error_date': info.last_error_date,
            'last_error_message': info.last_error_message,
            'max_connections': info.max_connections,
            'allowed_updates': info.allowed_updates
        })
    except Exception as e:
        logger.error(f"Ошибка получения информации webhook: {e}", exc_info=True)
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
