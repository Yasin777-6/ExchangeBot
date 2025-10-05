"""
Скрипт для автоматической настройки описания и команд бота
Запустите: python setup_bot_info.py
"""

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot, BotCommand

load_dotenv()

async def setup_bot_info():
    """Настроить информацию о боте"""
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    bot = Bot(token=token)
    
    print("🤖 Настройка бота...")
    
    try:
        # 1. Установить команды
        commands = [
            BotCommand('start', '🚀 Начать работу с ботом'),
            BotCommand('help', 'ℹ️ Справка по использованию'),
            BotCommand('profile', '👤 Мой профиль'),
        ]
        
        await bot.set_my_commands(commands)
        print("✅ Команды установлены")
        
        # 2. Установить описание (description - показывается перед стартом)
        description = """🎮 Minecraft Holy World Marketplace - безопасная торговая площадка

🛍 Покупайте предметы Minecraft Holy World у проверенных продавцов
💰 Продавайте свои предметы с гарантией оплаты
🛡 Все сделки защищены администрацией

Особенности:
• Система эскроу (деньги в безопасности)
• Рейтинги и отзывы продавцов
• Уровни продавцов (Бронза → Платина)
• Комиссия всего 5.5%

Нажмите START чтобы начать торговлю! 👇"""
        
        await bot.set_my_description(description)
        print("✅ Описание установлено")
        
        # 3. Установить короткое описание (about - показывается в профиле бота)
        short_description = "🎮 Безопасный маркетплейс для Minecraft. Покупайте и продавайте предметы с гарантией! Система эскроу, рейтинги, защита сделок."
        
        await bot.set_my_short_description(short_description)
        print("✅ Короткое описание установлено")
        
        # 4. Получить информацию о боте
        me = await bot.get_me()
        print(f"\n✅ Бот успешно настроен!")
        print(f"📱 Имя: {me.first_name}")
        print(f"🔗 Username: @{me.username}")
        print(f"🆔 ID: {me.id}")
        print(f"\n🔗 Ссылка на бота: https://t.me/{me.username}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("🎮 Minecraft Marketplace - Настройка бота")
    print("=" * 50)
    print()
    
    asyncio.run(setup_bot_info())
    
    print("\n" + "=" * 50)
    print("✅ Готово! Проверьте бота в Telegram")
    print("=" * 50)
