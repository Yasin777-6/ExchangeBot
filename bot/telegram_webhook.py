"""
Telegram Bot с поддержкой Webhook для Django
"""

import os
from telegram import Update
from telegram.ext import Application
from django.conf import settings
import logging

from .telegram_bot import (
    start, help_command, profile, show_catalog, buy_item, payment_confirmed,
    admin_approve_payment, item_received, admin_complete_transaction,
    start_add_item, add_item_title, add_item_description, add_item_price,
    add_item_category, admin_approve_item, become_merchant_handler,
    show_leaderboard, show_my_purchases, show_my_sales, show_my_items,
    handle_text, handle_callback, cancel,
    CHOOSING_ROLE, ADDING_ITEM_TITLE, ADDING_ITEM_DESC, ADDING_ITEM_PRICE, 
    ADDING_ITEM_CATEGORY, CONFIRM_PAYMENT, CONFIRM_DELIVERY, 
    LEAVE_REVIEW_RATING, LEAVE_REVIEW_COMMENT
)
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler

logger = logging.getLogger(__name__)

# Глобальная переменная для application
_application = None

def get_application():
    """Получить или создать application (lazy loading)"""
    global _application
    
    if _application is None:
        logger.info("Инициализация Telegram application...")
        _application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        setup_handlers(_application)
        logger.info("Telegram application готов")
    
    return _application

def setup_handlers(app):
    """Настройка обработчиков бота"""
    
    # ConversationHandler для добавления товара
    add_item_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ Добавить товар$'), start_add_item)],
        states={
            ADDING_ITEM_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_title)],
            ADDING_ITEM_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_description)],
            ADDING_ITEM_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_price)],
            ADDING_ITEM_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_category)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile))
    
    # ConversationHandler
    app.add_handler(add_item_conv)
    
    # Обработчики callback
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("Обработчики бота настроены для webhook")

# Для обратной совместимости
application = property(lambda self: get_application())
