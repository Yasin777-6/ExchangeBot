"""
URL configuration for exchange project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from bot import views as bot_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Telegram Bot Webhook
    path('bot/webhook/', bot_views.telegram_webhook, name='telegram_webhook'),
    path('bot/set-webhook/', bot_views.set_webhook, name='set_webhook'),
    path('bot/delete-webhook/', bot_views.delete_webhook, name='delete_webhook'),
    path('bot/webhook-info/', bot_views.webhook_info, name='webhook_info'),
]
