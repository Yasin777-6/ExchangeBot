from django.contrib import admin
from .models import TelegramUser, Item, Transaction, Review

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'username', 'role', 'merchant_level', 'total_sales', 'rating', 'created_at']
    list_filter = ['role', 'merchant_level', 'is_active']
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name']
    readonly_fields = ['created_at']

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'merchant', 'price', 'category', 'is_approved', 'is_active', 'created_at']
    list_filter = ['is_approved', 'is_active', 'category']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    actions = ['approve_items']
    
    def approve_items(self, request, queryset):
        queryset.update(is_approved=True)
    approve_items.short_description = "Одобрить выбранные товары"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'client', 'merchant', 'amount', 'fee_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['transaction_id', 'client__username', 'merchant__username']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'fee_amount', 'merchant_amount']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['merchant', 'client', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['merchant__username', 'client__username']
    readonly_fields = ['created_at']
