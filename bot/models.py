from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

# Роли пользователей
class UserRole(models.TextChoices):
    CLIENT = 'CLIENT', 'Клиент'
    MERCHANT = 'MERCHANT', 'Продавец'
    ADMIN = 'ADMIN', 'Администратор'

# Уровни продавцов
class MerchantLevel(models.TextChoices):
    BRONZE = 'BRONZE', 'Бронза'
    SILVER = 'SILVER', 'Серебро'
    GOLD = 'GOLD', 'Золото'
    PLATINUM = 'PLATINUM', 'Платина'

# Статусы транзакций
class TransactionStatus(models.TextChoices):
    PENDING_PAYMENT = 'PENDING_PAYMENT', 'Ожидает оплаты'
    PAYMENT_CONFIRMED = 'PAYMENT_CONFIRMED', 'Оплата подтверждена'
    ITEM_DELIVERED = 'ITEM_DELIVERED', 'Товар доставлен'
    COMPLETED = 'COMPLETED', 'Завершена'
    CANCELLED = 'CANCELLED', 'Отменена'

# Профиль пользователя Telegram
class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя пользователя')
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя')
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Фамилия')
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CLIENT, verbose_name='Роль')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    
    # Поля для продавцов
    merchant_level = models.CharField(max_length=20, choices=MerchantLevel.choices, default=MerchantLevel.BRONZE, blank=True, null=True, verbose_name='Уровень продавца')
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Общая сумма продаж')
    total_transactions = models.IntegerField(default=0, verbose_name='Количество сделок')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='Рейтинг')
    experience_points = models.IntegerField(default=0, verbose_name='Опыт')
    approved_items_count = models.IntegerField(default=5, verbose_name='Лимит товаров')
    
    class Meta:
        verbose_name = 'Пользователь Telegram'
        verbose_name_plural = 'Пользователи Telegram'
        
    def __str__(self):
        return f"{self.username or self.telegram_id} ({self.get_role_display()})"
    
    def update_merchant_level(self):
        """Обновление уровня продавца на основе опыта"""
        if self.role == UserRole.MERCHANT:
            if self.experience_points >= 10000:
                self.merchant_level = MerchantLevel.PLATINUM
            elif self.experience_points >= 5000:
                self.merchant_level = MerchantLevel.GOLD
            elif self.experience_points >= 2000:
                self.merchant_level = MerchantLevel.SILVER
            else:
                self.merchant_level = MerchantLevel.BRONZE
            self.save()

# Товары Minecraft
class Item(models.Model):
    merchant = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='items', verbose_name='Продавец')
    title = models.CharField(max_length=255, verbose_name='Название товара')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    category = models.CharField(max_length=100, verbose_name='Категория')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрено администратором')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    views_count = models.IntegerField(default=0, verbose_name='Количество просмотров')
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.price} руб."

# Транзакции
class Transaction(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True, verbose_name='ID транзакции')
    client = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='purchases', verbose_name='Покупатель')
    merchant = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='sales', verbose_name='Продавец')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name='Товар')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Комиссия')
    merchant_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма продавцу')
    
    status = models.CharField(max_length=30, choices=TransactionStatus.choices, default=TransactionStatus.PENDING_PAYMENT, verbose_name='Статус')
    
    payment_confirmed_at = models.DateTimeField(blank=True, null=True, verbose_name='Оплата подтверждена')
    item_delivered_at = models.DateTimeField(blank=True, null=True, verbose_name='Товар доставлен')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='Завершена')
    
    client_contact = models.CharField(max_length=255, blank=True, null=True, verbose_name='Контакт клиента')
    merchant_contact = models.CharField(max_length=255, blank=True, null=True, verbose_name='Контакт продавца')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Транзакция {self.transaction_id} - {self.amount} руб."
    
    def calculate_amounts(self):
        """Расчет комиссии и суммы продавцу"""
        self.fee_amount = self.amount * Decimal(str(5.5)) / Decimal('100')
        self.merchant_amount = self.amount - self.fee_amount
        
    def save(self, *args, **kwargs):
        if not self.fee_amount or not self.merchant_amount:
            self.calculate_amounts()
        super().save(*args, **kwargs)

# Отзывы
class Review(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, verbose_name='Транзакция')
    merchant = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='reviews', verbose_name='Продавец')
    client = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='given_reviews', verbose_name='Покупатель')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='Оценка')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        
    def __str__(self):
        return f"Отзыв на {self.merchant.username} - {self.rating}/5"
