from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
from telegram import Bot

class Command(BaseCommand):
    help = 'Установить webhook для Telegram бота'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='URL для webhook (например: https://your-app.railway.app/bot/webhook/)',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Удалить существующий webhook',
        )
        parser.add_argument(
            '--info',
            action='store_true',
            help='Показать информацию о webhook',
        )

    def handle(self, *args, **options):
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        if options['delete']:
            self.stdout.write('Удаление webhook...')
            asyncio.run(bot.delete_webhook())
            self.stdout.write(self.style.SUCCESS('✅ Webhook удален!'))
            return
        
        if options['info']:
            self.stdout.write('Получение информации о webhook...')
            info = asyncio.run(bot.get_webhook_info())
            self.stdout.write(f"\n📊 Информация о Webhook:")
            self.stdout.write(f"URL: {info.url or 'Не установлен'}")
            self.stdout.write(f"Pending updates: {info.pending_update_count}")
            if info.last_error_date:
                self.stdout.write(self.style.WARNING(f"Last error: {info.last_error_message}"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Ошибок нет"))
            return
        
        webhook_url = options['url']
        
        if not webhook_url:
            self.stdout.write(self.style.ERROR('❌ Укажите URL для webhook с помощью --url'))
            self.stdout.write('Пример: python manage.py setup_webhook --url https://your-app.railway.app/bot/webhook/')
            return
        
        self.stdout.write(f'Установка webhook: {webhook_url}')
        asyncio.run(bot.set_webhook(webhook_url))
        
        # Проверяем
        info = asyncio.run(bot.get_webhook_info())
        if info.url == webhook_url:
            self.stdout.write(self.style.SUCCESS(f'✅ Webhook установлен успешно!'))
            self.stdout.write(f'URL: {info.url}')
        else:
            self.stdout.write(self.style.ERROR('❌ Ошибка установки webhook'))
