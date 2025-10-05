import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid

from .models import TelegramUser, Item, Transaction, Review, UserRole, TransactionStatus, MerchantLevel

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(CHOOSING_ROLE, ADDING_ITEM_TITLE, ADDING_ITEM_DESC, ADDING_ITEM_PRICE, ADDING_ITEM_CATEGORY,
 CONFIRM_PAYMENT, CONFIRM_DELIVERY, LEAVE_REVIEW_RATING, LEAVE_REVIEW_COMMENT) = range(9)

# Клавиатуры
def get_main_keyboard(role):
    """Главная клавиатура в зависимости от роли"""
    if role == UserRole.CLIENT:
        keyboard = [
            [KeyboardButton("🛍 Каталог товаров"), KeyboardButton("👤 Мой профиль")],
            [KeyboardButton("📦 Мои покупки"), KeyboardButton("🏆 Рейтинг продавцов")],
            [KeyboardButton("💼 Стать продавцом"), KeyboardButton("ℹ️ Помощь")]
        ]
    elif role == UserRole.MERCHANT:
        keyboard = [
            [KeyboardButton("➕ Добавить товар"), KeyboardButton("📋 Мои товары")],
            [KeyboardButton("💰 Мои продажи"), KeyboardButton("👤 Мой профиль")],
            [KeyboardButton("🏆 Рейтинг продавцов"), KeyboardButton("ℹ️ Помощь")]
        ]
    elif role == UserRole.ADMIN:
        keyboard = [
            [KeyboardButton("✅ Одобрить товары"), KeyboardButton("📊 Транзакции")],
            [KeyboardButton("👥 Пользователи"), KeyboardButton("📈 Статистика")],
            [KeyboardButton("ℹ️ Помощь")]
        ]
    else:
        keyboard = [[KeyboardButton("🔄 Начать")]]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    return ReplyKeyboardMarkup([[KeyboardButton("◀️ Назад")]], resize_keyboard=True)

# Получение или создание пользователя
@sync_to_async
def get_or_create_user(telegram_user):
    """Получить или создать пользователя"""
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_user.id,
        defaults={
            'username': telegram_user.username,
            'first_name': telegram_user.first_name,
            'last_name': telegram_user.last_name,
        }
    )
    if not created:
        # Обновляем информацию
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        user.save()
    return user, created

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user, created = await get_or_create_user(update.effective_user)
    
    welcome_text = f"""
🎮 **Добро пожаловать в Minecraft Marketplace!**

Привет, {update.effective_user.first_name}! 👋

Это безопасная площадка для покупки и продажи предметов Minecraft.

**Как это работает:**

🔹 **Для покупателей:**
1. Выберите товар из каталога
2. Оплатите на карту: `{settings.PAYMENT_CARD_NUMBER}`
3. Подтвердите оплату в боте
4. Получите контакт продавца
5. Получите товар и подтвердите
6. Оставьте отзыв

🔹 **Для продавцов:**
1. Добавьте товар (до 5 шт.)
2. Дождитесь одобрения администратора
3. Получите уведомление о покупке
4. Свяжитесь с покупателем
5. Передайте товар
6. Получите деньги после подтверждения

💰 **Комиссия сервиса: {settings.TRANSACTION_FEE_PERCENT}%**

🛡️ **Гарантия безопасности:**
- Деньги передаются только после подтверждения получения товара
- Все транзакции контролируются администратором
- Система рейтингов и отзывов

Выберите действие из меню ниже! 👇
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user.role)
    )

# Помощь
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по боту"""
    help_text = """
📚 **Справка по использованию бота**

**Основные команды:**
/start - Начать работу
/help - Показать справку
/profile - Мой профиль

**Для покупателей:**
• Каталог товаров - просмотр всех товаров
• Мои покупки - история покупок
• Рейтинг продавцов - топ продавцов

**Для продавцов:**
• Добавить товар - разместить новый товар
• Мои товары - управление товарами
• Мои продажи - история продаж

**Система уровней продавцов:**
🥉 Бронза: 0-1999 XP
🥈 Серебро: 2000-4999 XP
🥇 Золото: 5000-9999 XP
💎 Платина: 10000+ XP

За каждую продажу: +100 XP

**Поддержка:** @atauq
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Профиль пользователя
@sync_to_async
def get_user_profile_text(telegram_id):
    """Получить текст профиля пользователя"""
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        
        profile_text = f"""
👤 **Ваш профиль**

📱 Telegram ID: `{user.telegram_id}`
👤 Имя: {user.first_name or 'Не указано'}
🏷 Роль: {user.get_role_display()}
📅 Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}
"""
        
        if user.role == UserRole.MERCHANT:
            level_emoji = {
                MerchantLevel.BRONZE: '🥉',
                MerchantLevel.SILVER: '🥈',
                MerchantLevel.GOLD: '🥇',
                MerchantLevel.PLATINUM: '💎'
            }
            
            profile_text += f"""
**Статистика продавца:**
{level_emoji.get(user.merchant_level, '🥉')} Уровень: {user.get_merchant_level_display()}
⭐️ Рейтинг: {user.rating}/5.00
💰 Всего продаж: {user.total_sales} руб.
📦 Количество сделок: {user.total_transactions}
🎯 Опыт: {user.experience_points} XP
📋 Лимит товаров: {user.approved_items_count}
"""
        
        return profile_text
    except TelegramUser.DoesNotExist:
        return "❌ Профиль не найден. Используйте /start"

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль"""
    profile_text = await get_user_profile_text(update.effective_user.id)
    await update.message.reply_text(profile_text, parse_mode='Markdown')

# Каталог товаров
@sync_to_async
def get_items_list(offset=0, limit=10):
    """Получить список товаров"""
    items = Item.objects.filter(is_approved=True, is_active=True).select_related('merchant')[offset:offset+limit]
    return list(items)

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать каталог товаров"""
    items = await get_items_list()
    
    if not items:
        await update.message.reply_text(
            "📭 Каталог пуст. Товары появятся скоро!",
            reply_markup=get_back_keyboard()
        )
        return
    
    for item in items:
        item_text = f"""
🎮 **{item.title}**

📝 {item.description}

💰 Цена: **{item.price} руб.**
📂 Категория: {item.category}
👤 Продавец: @{item.merchant.username or 'Анонимный'}
⭐️ Рейтинг продавца: {item.merchant.rating}/5.00
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Купить", callback_data=f"buy_{item.id}")]
        ])
        
        await update.message.reply_text(
            item_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

# Покупка товара
@sync_to_async
def create_transaction(item_id, client_telegram_id):
    """Создать транзакцию"""
    try:
        item = Item.objects.select_related('merchant').get(id=item_id, is_approved=True, is_active=True)
        client = TelegramUser.objects.get(telegram_id=client_telegram_id)
        
        if client.telegram_id == item.merchant.telegram_id:
            return None, "Вы не можете купить свой собственный товар!"
        
        transaction_id = str(uuid.uuid4())[:8].upper()
        
        transaction = Transaction.objects.create(
            transaction_id=transaction_id,
            client=client,
            merchant=item.merchant,
            item=item,
            amount=item.price
        )
        
        return transaction, None
    except Item.DoesNotExist:
        return None, "Товар не найден или недоступен"
    except TelegramUser.DoesNotExist:
        return None, "Пользователь не найден"

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка покупки товара"""
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split('_')[1])
    transaction, error = await create_transaction(item_id, update.effective_user.id)
    
    if error:
        await query.message.reply_text(f"❌ {error}")
        return
    
    payment_text = f"""
💳 **Оплата заказа**

📦 Товар: {transaction.item.title}
💰 Сумма: **{transaction.amount} руб.**
🆔 ID транзакции: `{transaction.transaction_id}`

**Инструкция по оплате:**

1️⃣ Переведите **{transaction.amount} руб.** на карту:
`{settings.PAYMENT_CARD_NUMBER}`

2️⃣ После перевода нажмите кнопку "✅ Я оплатил"

3️⃣ Администратор проверит платеж и вы получите контакт продавца

⚠️ **Важно:** Указывайте в комментарии к переводу ID транзакции: `{transaction.transaction_id}`
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid_{transaction.id}")],
        [InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{transaction.id}")]
    ])
    
    await query.message.reply_text(
        payment_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# Подтверждение оплаты
@sync_to_async
def confirm_payment(transaction_id, user_telegram_id):
    """Подтвердить оплату"""
    try:
        transaction = Transaction.objects.select_related('client', 'merchant', 'item').get(
            id=transaction_id,
            client__telegram_id=user_telegram_id,
            status=TransactionStatus.PENDING_PAYMENT
        )
        
        transaction.status = TransactionStatus.PAYMENT_CONFIRMED
        transaction.payment_confirmed_at = timezone.now()
        transaction.save()
        
        return transaction, None
    except Transaction.DoesNotExist:
        return None, "Транзакция не найдена"

@sync_to_async
def get_admin_ids():
    """Получить ID всех администраторов"""
    admins = TelegramUser.objects.filter(role=UserRole.ADMIN, is_active=True)
    return [admin.telegram_id for admin in admins]

async def payment_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения оплаты"""
    query = update.callback_query
    await query.answer()
    
    transaction_id = int(query.data.split('_')[1])
    transaction, error = await confirm_payment(transaction_id, update.effective_user.id)
    
    if error:
        await query.message.reply_text(f"❌ {error}")
        return
    
    # Уведомление клиента
    client_text = f"""
✅ **Оплата подтверждена!**

Ваша оплата отправлена на проверку администратору.

📦 Товар: {transaction.item.title}
💰 Сумма: {transaction.amount} руб.
🆔 ID: `{transaction.transaction_id}`

После проверки вы получите контакт продавца.
"""
    await query.message.reply_text(client_text, parse_mode='Markdown')
    
    # Уведомление продавца
    merchant_text = f"""
🔔 **Новая покупка!**

📦 Товар: {transaction.item.title}
💰 Сумма: {transaction.amount} руб.
🆔 ID: `{transaction.transaction_id}`

Покупатель подтвердил оплату. Ожидайте проверки администратором.
"""
    try:
        await context.bot.send_message(
            chat_id=transaction.merchant.telegram_id,
            text=merchant_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление продавцу: {e}")
    
    # Уведомление администраторов
    admin_ids = await get_admin_ids()
    admin_text = f"""
🔔 **Новая транзакция требует проверки!**

🆔 ID: `{transaction.transaction_id}`
📦 Товар: {transaction.item.title}
💰 Сумма: {transaction.amount} руб.
💵 Комиссия: {transaction.fee_amount} руб.
👤 Покупатель: @{transaction.client.username or 'Анонимный'}
👤 Продавец: @{transaction.merchant.username or 'Анонимный'}

Проверьте платеж и одобрите транзакцию.
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_payment_{transaction.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_payment_{transaction.id}")]
    ])
    
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

# Одобрение платежа администратором
@sync_to_async
def approve_payment_by_admin(transaction_id):
    """Одобрить платеж администратором"""
    try:
        transaction = Transaction.objects.select_related('client', 'merchant', 'item').get(
            id=transaction_id,
            status=TransactionStatus.PAYMENT_CONFIRMED
        )
        
        # Сохраняем контакты для связи
        transaction.client_contact = f"@{transaction.client.username}" if transaction.client.username else f"ID: {transaction.client.telegram_id}"
        transaction.merchant_contact = f"@{transaction.merchant.username}" if transaction.merchant.username else f"ID: {transaction.merchant.telegram_id}"
        transaction.save()
        
        return transaction, None
    except Transaction.DoesNotExist:
        return None, "Транзакция не найдена"

async def admin_approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Администратор одобряет платеж"""
    query = update.callback_query
    await query.answer()
    
    transaction_id = int(query.data.split('_')[2])
    transaction, error = await approve_payment_by_admin(transaction_id)
    
    if error:
        await query.message.reply_text(f"❌ {error}")
        return
    
    await query.message.edit_text(
        f"✅ Платеж одобрен! Контакты отправлены покупателю и продавцу.",
        parse_mode='Markdown'
    )
    
    # Отправка контактов покупателю
    client_text = f"""
✅ **Платеж одобрен администратором!**

📦 Товар: {transaction.item.title}
🆔 ID: `{transaction.transaction_id}`

**Контакт продавца:** {transaction.merchant_contact}

Свяжитесь с продавцом для получения товара.
После получения товара нажмите кнопку ниже.
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Я получил товар", callback_data=f"received_{transaction.id}")]
    ])
    
    try:
        await context.bot.send_message(
            chat_id=transaction.client.telegram_id,
            text=client_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Не удалось отправить контакт покупателю: {e}")
    
    # Отправка контактов продавцу
    merchant_text = f"""
✅ **Платеж одобрен администратором!**

📦 Товар: {transaction.item.title}
🆔 ID: `{transaction.transaction_id}`

**Контакт покупателя:** {transaction.client_contact}

Свяжитесь с покупателем и передайте товар.
"""
    
    try:
        await context.bot.send_message(
            chat_id=transaction.merchant.telegram_id,
            text=merchant_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Не удалось отправить контакт продавцу: {e}")

# Подтверждение получения товара
@sync_to_async
def confirm_item_received(transaction_id, user_telegram_id):
    """Подтвердить получение товара"""
    try:
        transaction = Transaction.objects.select_related('client', 'merchant', 'item').get(
            id=transaction_id,
            client__telegram_id=user_telegram_id,
            status=TransactionStatus.PAYMENT_CONFIRMED
        )
        
        transaction.status = TransactionStatus.ITEM_DELIVERED
        transaction.item_delivered_at = timezone.now()
        transaction.save()
        
        return transaction, None
    except Transaction.DoesNotExist:
        return None, "Транзакция не найдена"

async def item_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения получения товара"""
    query = update.callback_query
    await query.answer()
    
    transaction_id = int(query.data.split('_')[1])
    transaction, error = await confirm_item_received(transaction_id, update.effective_user.id)
    
    if error:
        await query.message.reply_text(f"❌ {error}")
        return
    
    client_text = f"""
✅ **Товар получен!**

Спасибо за подтверждение!
Теперь оставьте отзыв о продавце.
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐️ Оставить отзыв", callback_data=f"review_{transaction.id}")]
    ])
    
    await query.message.reply_text(client_text, parse_mode='Markdown', reply_markup=keyboard)
    
    # Уведомление администраторов
    admin_ids = await get_admin_ids()
    admin_text = f"""
🔔 **Товар получен покупателем!**

🆔 ID: `{transaction.transaction_id}`
📦 Товар: {transaction.item.title}
💰 Сумма: {transaction.amount} руб.
💵 Комиссия: {transaction.fee_amount} руб.
💸 К выплате продавцу: {transaction.merchant_amount} руб.

Переведите деньги продавцу и завершите транзакцию.
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Деньги отправлены", callback_data=f"complete_{transaction.id}")]
    ])
    
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление администратору: {e}")

# Завершение транзакции
@sync_to_async
def complete_transaction(transaction_id):
    """Завершить транзакцию"""
    try:
        transaction = Transaction.objects.select_related('client', 'merchant', 'item').get(
            id=transaction_id,
            status=TransactionStatus.ITEM_DELIVERED
        )
        
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = timezone.now()
        transaction.save()
        
        # Обновление статистики продавца
        merchant = transaction.merchant
        merchant.total_sales += transaction.amount
        merchant.total_transactions += 1
        merchant.experience_points += 100
        merchant.update_merchant_level()
        merchant.save()
        
        return transaction, None
    except Transaction.DoesNotExist:
        return None, "Транзакция не найдена"

async def admin_complete_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Администратор завершает транзакцию"""
    query = update.callback_query
    await query.answer()
    
    transaction_id = int(query.data.split('_')[1])
    transaction, error = await complete_transaction(transaction_id)
    
    if error:
        await query.message.reply_text(f"❌ {error}")
        return
    
    await query.message.edit_text(
        f"✅ Транзакция `{transaction.transaction_id}` завершена!",
        parse_mode='Markdown'
    )
    
    # Уведомление продавца
    merchant_text = f"""
💰 **Деньги получены!**

Транзакция `{transaction.transaction_id}` завершена.

📦 Товар: {transaction.item.title}
💸 Вы получили: {transaction.merchant_amount} руб.
🎯 +100 XP

Спасибо за работу!
"""
    
    try:
        await context.bot.send_message(
            chat_id=transaction.merchant.telegram_id,
            text=merchant_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление продавцу: {e}")

# Добавление товара
async def start_add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление товара"""
    user, _ = await get_or_create_user(update.effective_user)
    
    if user.role != UserRole.MERCHANT:
        await update.message.reply_text(
            "❌ Только продавцы могут добавлять товары. Станьте продавцом через меню!",
            reply_markup=get_main_keyboard(user.role)
        )
        return ConversationHandler.END
    
    # Проверка лимита товаров
    active_items_count = await sync_to_async(
        lambda: Item.objects.filter(merchant__telegram_id=update.effective_user.id, is_active=True).count()
    )()
    
    if active_items_count >= user.approved_items_count:
        await update.message.reply_text(
            f"❌ Вы достигли лимита активных товаров ({user.approved_items_count} шт.).\n"
            "Дождитесь одобрения администратора для увеличения лимита.",
            reply_markup=get_main_keyboard(user.role)
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 Введите название товара:",
        reply_markup=get_back_keyboard()
    )
    return ADDING_ITEM_TITLE

async def add_item_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить название товара"""
    context.user_data['item_title'] = update.message.text
    await update.message.reply_text("📝 Введите описание товара:")
    return ADDING_ITEM_DESC

async def add_item_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить описание товара"""
    context.user_data['item_description'] = update.message.text
    await update.message.reply_text("💰 Введите цену товара (в рублях):")
    return ADDING_ITEM_PRICE

async def add_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить цену товара"""
    try:
        price = Decimal(update.message.text)
        if price <= 0:
            raise ValueError
        context.user_data['item_price'] = price
        await update.message.reply_text("📂 Введите категорию товара (например: Оружие, Броня, Ресурсы):")
        return ADDING_ITEM_CATEGORY
    except (ValueError, Exception):
        await update.message.reply_text("❌ Неверная цена. Введите число больше 0:")
        return ADDING_ITEM_PRICE

@sync_to_async
def create_item(telegram_id, title, description, price, category):
    """Создать товар"""
    try:
        merchant = TelegramUser.objects.get(telegram_id=telegram_id, role=UserRole.MERCHANT)
        item = Item.objects.create(
            merchant=merchant,
            title=title,
            description=description,
            price=price,
            category=category
        )
        return item, None
    except TelegramUser.DoesNotExist:
        return None, "Продавец не найден"

async def add_item_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить категорию и создать товар"""
    category = update.message.text
    
    item, error = await create_item(
        update.effective_user.id,
        context.user_data['item_title'],
        context.user_data['item_description'],
        context.user_data['item_price'],
        category
    )
    
    if error:
        await update.message.reply_text(f"❌ {error}")
        return ConversationHandler.END
    
    user, _ = await get_or_create_user(update.effective_user)
    
    await update.message.reply_text(
        f"✅ Товар добавлен!\n\n"
        f"📦 {item.title}\n"
        f"💰 {item.price} руб.\n\n"
        f"Товар отправлен на модерацию администратору.",
        reply_markup=get_main_keyboard(user.role)
    )
    
    # Уведомление администраторов
    admin_ids = await get_admin_ids()
    admin_text = f"""
🔔 **Новый товар на модерацию!**

📦 Название: {item.title}
📝 Описание: {item.description}
💰 Цена: {item.price} руб.
📂 Категория: {item.category}
👤 Продавец: @{user.username or 'Анонимный'}
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_item_{item.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_item_{item.id}")]
    ])
    
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление администратору: {e}")
    
    context.user_data.clear()
    return ConversationHandler.END

# Одобрение товара администратором
@sync_to_async
def approve_item(item_id):
    """Одобрить товар"""
    try:
        item = Item.objects.select_related('merchant').get(id=item_id)
        item.is_approved = True
        item.save()
        return item, None
    except Item.DoesNotExist:
        return None, "Товар не найден"

async def admin_approve_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Администратор одобряет товар"""
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split('_')[2])
    item, error = await approve_item(item_id)
    
    if error:
        await query.message.reply_text(f"❌ {error}")
        return
    
    await query.message.edit_text(
        f"✅ Товар '{item.title}' одобрен!",
        parse_mode='Markdown'
    )
    
    # Уведомление продавца
    merchant_text = f"""
✅ **Ваш товар одобрен!**

📦 {item.title}
💰 {item.price} руб.

Товар теперь доступен в каталоге!
"""
    
    try:
        await context.bot.send_message(
            chat_id=item.merchant.telegram_id,
            text=merchant_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление продавцу: {e}")

# Стать продавцом
@sync_to_async
def become_merchant(telegram_id):
    """Стать продавцом"""
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        if user.role == UserRole.MERCHANT:
            return None, "Вы уже продавец!"
        user.role = UserRole.MERCHANT
        user.merchant_level = MerchantLevel.BRONZE
        user.save()
        return user, None
    except TelegramUser.DoesNotExist:
        return None, "Пользователь не найден"

async def become_merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик становления продавцом"""
    user, error = await become_merchant(update.effective_user.id)
    
    if error:
        await update.message.reply_text(f"❌ {error}")
        return
    
    await update.message.reply_text(
        "🎉 Поздравляем! Теперь вы продавец!\n\n"
        "Вы можете добавить до 5 товаров.\n"
        "После одобрения администратором лимит может быть увеличен.",
        reply_markup=get_main_keyboard(user.role)
    )

# Рейтинг продавцов
@sync_to_async
def get_top_merchants(limit=10):
    """Получить топ продавцов"""
    merchants = TelegramUser.objects.filter(
        role=UserRole.MERCHANT,
        is_active=True
    ).order_by('-total_sales', '-rating')[:limit]
    return list(merchants)

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать рейтинг продавцов"""
    merchants = await get_top_merchants()
    
    if not merchants:
        await update.message.reply_text("📭 Рейтинг пуст.")
        return
    
    leaderboard_text = "🏆 **Топ-10 продавцов**\n\n"
    
    medals = ['🥇', '🥈', '🥉']
    level_emoji = {
        MerchantLevel.BRONZE: '🥉',
        MerchantLevel.SILVER: '🥈',
        MerchantLevel.GOLD: '🥇',
        MerchantLevel.PLATINUM: '💎'
    }
    
    for i, merchant in enumerate(merchants, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        level = level_emoji.get(merchant.merchant_level, '🥉')
        
        leaderboard_text += f"{medal} {level} @{merchant.username or 'Анонимный'}\n"
        leaderboard_text += f"   💰 {merchant.total_sales} руб. | ⭐️ {merchant.rating}/5 | 📦 {merchant.total_transactions} сделок\n\n"
    
    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

# Мои покупки
@sync_to_async
def get_user_purchases(telegram_id):
    """Получить покупки пользователя"""
    transactions = Transaction.objects.filter(
        client__telegram_id=telegram_id
    ).select_related('item', 'merchant').order_by('-created_at')[:10]
    return list(transactions)

async def show_my_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои покупки"""
    transactions = await get_user_purchases(update.effective_user.id)
    
    if not transactions:
        await update.message.reply_text("📭 У вас пока нет покупок.")
        return
    
    purchases_text = "📦 **Мои покупки**\n\n"
    
    status_emoji = {
        TransactionStatus.PENDING_PAYMENT: '⏳',
        TransactionStatus.PAYMENT_CONFIRMED: '✅',
        TransactionStatus.ITEM_DELIVERED: '📦',
        TransactionStatus.COMPLETED: '✔️',
        TransactionStatus.CANCELLED: '❌'
    }
    
    for t in transactions:
        emoji = status_emoji.get(t.status, '❓')
        purchases_text += f"{emoji} **{t.item.title}**\n"
        purchases_text += f"   💰 {t.amount} руб. | 🆔 `{t.transaction_id}`\n"
        purchases_text += f"   Статус: {t.get_status_display()}\n\n"
    
    await update.message.reply_text(purchases_text, parse_mode='Markdown')

# Мои продажи
@sync_to_async
def get_merchant_sales(telegram_id):
    """Получить продажи продавца"""
    transactions = Transaction.objects.filter(
        merchant__telegram_id=telegram_id
    ).select_related('item', 'client').order_by('-created_at')[:10]
    return list(transactions)

async def show_my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои продажи"""
    transactions = await get_merchant_sales(update.effective_user.id)
    
    if not transactions:
        await update.message.reply_text("📭 У вас пока нет продаж.")
        return
    
    sales_text = "💰 **Мои продажи**\n\n"
    
    status_emoji = {
        TransactionStatus.PENDING_PAYMENT: '⏳',
        TransactionStatus.PAYMENT_CONFIRMED: '✅',
        TransactionStatus.ITEM_DELIVERED: '📦',
        TransactionStatus.COMPLETED: '✔️',
        TransactionStatus.CANCELLED: '❌'
    }
    
    for t in transactions:
        emoji = status_emoji.get(t.status, '❓')
        sales_text += f"{emoji} **{t.item.title}**\n"
        sales_text += f"   💰 {t.merchant_amount} руб. | 🆔 `{t.transaction_id}`\n"
        sales_text += f"   Статус: {t.get_status_display()}\n\n"
    
    await update.message.reply_text(sales_text, parse_mode='Markdown')

# Мои товары
@sync_to_async
def get_merchant_items(telegram_id):
    """Получить товары продавца"""
    items = Item.objects.filter(
        merchant__telegram_id=telegram_id,
        is_active=True
    ).order_by('-created_at')
    return list(items)

async def show_my_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои товары"""
    items = await get_merchant_items(update.effective_user.id)
    
    if not items:
        await update.message.reply_text("📭 У вас пока нет товаров.")
        return
    
    for item in items:
        status = "✅ Одобрен" if item.is_approved else "⏳ На модерации"
        item_text = f"""
📦 **{item.title}**

📝 {item.description}
💰 Цена: {item.price} руб.
📂 Категория: {item.category}
📊 Статус: {status}
👁 Просмотров: {item.views_count}
"""
        await update.message.reply_text(item_text, parse_mode='Markdown')

# Админские функции
@sync_to_async
def get_pending_items():
    """Получить товары на модерации"""
    items = Item.objects.filter(is_approved=False, is_active=True).select_related('merchant')[:20]
    return list(items)

async def show_pending_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать товары на модерации (для админов)"""
    items = await get_pending_items()
    
    if not items:
        await update.message.reply_text("✅ Нет товаров на модерации!")
        return
    
    await update.message.reply_text(f"📋 **Товары на модерации ({len(items)}):**\n", parse_mode='Markdown')
    
    for item in items:
        item_text = f"""
📦 **{item.title}**

📝 {item.description}
💰 Цена: {item.price} руб.
📂 Категория: {item.category}
👤 Продавец: @{item.merchant.username or 'Анонимный'}
🆔 ID товара: {item.id}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_item_{item.id}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_item_{item.id}")]
        ])
        
        await update.message.reply_text(item_text, parse_mode='Markdown', reply_markup=keyboard)

@sync_to_async
def get_recent_transactions(limit=10):
    """Получить последние транзакции"""
    transactions = Transaction.objects.select_related('client', 'merchant', 'item').order_by('-created_at')[:limit]
    return list(transactions)

async def show_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать транзакции (для админов)"""
    transactions = await get_recent_transactions()
    
    if not transactions:
        await update.message.reply_text("📭 Нет транзакций.")
        return
    
    trans_text = "📊 **Последние транзакции:**\n\n"
    
    status_emoji = {
        TransactionStatus.PENDING_PAYMENT: '⏳',
        TransactionStatus.PAYMENT_CONFIRMED: '✅',
        TransactionStatus.ITEM_DELIVERED: '📦',
        TransactionStatus.COMPLETED: '✔️',
        TransactionStatus.CANCELLED: '❌'
    }
    
    for t in transactions:
        emoji = status_emoji.get(t.status, '❓')
        trans_text += f"{emoji} **{t.item.title}**\n"
        trans_text += f"   💰 {t.amount} руб. | 🆔 `{t.transaction_id}`\n"
        trans_text += f"   👤 {t.client.username or 'Клиент'} → {t.merchant.username or 'Продавец'}\n"
        trans_text += f"   📅 {t.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await update.message.reply_text(trans_text, parse_mode='Markdown')

@sync_to_async
def get_users_stats():
    """Получить статистику пользователей"""
    from django.db.models import Count
    
    total_users = TelegramUser.objects.count()
    clients = TelegramUser.objects.filter(role=UserRole.CLIENT).count()
    merchants = TelegramUser.objects.filter(role=UserRole.MERCHANT).count()
    admins = TelegramUser.objects.filter(role=UserRole.ADMIN).count()
    
    return {
        'total': total_users,
        'clients': clients,
        'merchants': merchants,
        'admins': admins
    }

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать пользователей (для админов)"""
    stats = await get_users_stats()
    
    users_text = f"""
👥 **Статистика пользователей:**

📊 Всего: {stats['total']}
🛍 Клиентов: {stats['clients']}
💼 Продавцов: {stats['merchants']}
⚙️ Админов: {stats['admins']}
"""
    
    await update.message.reply_text(users_text, parse_mode='Markdown')

@sync_to_async
def get_general_stats():
    """Получить общую статистику"""
    from django.db.models import Sum, Count
    
    total_items = Item.objects.filter(is_active=True).count()
    approved_items = Item.objects.filter(is_approved=True, is_active=True).count()
    pending_items = Item.objects.filter(is_approved=False, is_active=True).count()
    
    total_transactions = Transaction.objects.count()
    completed_transactions = Transaction.objects.filter(status=TransactionStatus.COMPLETED).count()
    
    total_revenue = Transaction.objects.filter(status=TransactionStatus.COMPLETED).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_fees = Transaction.objects.filter(status=TransactionStatus.COMPLETED).aggregate(
        total=Sum('fee_amount')
    )['total'] or 0
    
    return {
        'total_items': total_items,
        'approved_items': approved_items,
        'pending_items': pending_items,
        'total_transactions': total_transactions,
        'completed_transactions': completed_transactions,
        'total_revenue': total_revenue,
        'total_fees': total_fees
    }

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику (для админов)"""
    stats = await get_general_stats()
    
    stats_text = f"""
📈 **Общая статистика:**

**Товары:**
📦 Всего: {stats['total_items']}
✅ Одобрено: {stats['approved_items']}
⏳ На модерации: {stats['pending_items']}

**Транзакции:**
📊 Всего: {stats['total_transactions']}
✔️ Завершено: {stats['completed_transactions']}

**Финансы:**
💰 Оборот: {stats['total_revenue']:.2f} руб.
💵 Комиссии: {stats['total_fees']:.2f} руб.
"""
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# Обработчик текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    user, _ = await get_or_create_user(update.effective_user)
    
    if text == "🛍 Каталог товаров":
        await show_catalog(update, context)
    elif text == "👤 Мой профиль":
        await profile(update, context)
    elif text == "📦 Мои покупки":
        await show_my_purchases(update, context)
    elif text == "🏆 Рейтинг продавцов":
        await show_leaderboard(update, context)
    elif text == "💼 Стать продавцом":
        await become_merchant_handler(update, context)
    elif text == "➕ Добавить товар":
        await start_add_item(update, context)
    elif text == "📋 Мои товары":
        await show_my_items(update, context)
    elif text == "💰 Мои продажи":
        await show_my_sales(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    elif text == "✅ Одобрить товары":
        await show_pending_items(update, context)
    elif text == "📊 Транзакции":
        await show_transactions(update, context)
    elif text == "👥 Пользователи":
        await show_users(update, context)
    elif text == "📈 Статистика":
        await show_statistics(update, context)
    elif text == "◀️ Назад":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_keyboard(user.role)
        )
    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации.",
            reply_markup=get_main_keyboard(user.role)
        )

# Обработчик callback запросов
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    data = query.data
    
    if data.startswith('buy_'):
        await buy_item(update, context)
    elif data.startswith('paid_'):
        await payment_confirmed(update, context)
    elif data.startswith('approve_payment_'):
        await admin_approve_payment(update, context)
    elif data.startswith('received_'):
        await item_received(update, context)
    elif data.startswith('complete_'):
        await admin_complete_transaction(update, context)
    elif data.startswith('approve_item_'):
        await admin_approve_item(update, context)

# Отмена операции
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущей операции"""
    user, _ = await get_or_create_user(update.effective_user)
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=get_main_keyboard(user.role)
    )
    return ConversationHandler.END

# Главная функция запуска бота
def main():
    """Запуск бота"""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
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
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile))
    
    # ConversationHandler
    application.add_handler(add_item_conv)
    
    # Обработчики callback
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запуск бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
