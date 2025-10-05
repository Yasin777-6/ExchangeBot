#!/usr/bin/env python
"""
Test if Django can start
"""

import os
import sys
import django

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exchange.settings')

try:
    print("🔧 Setting up Django...")
    django.setup()
    print("✅ Django setup successful!")
    
    print("\n🔍 Checking database connection...")
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✅ Database connection successful!")
    
    print("\n📊 Checking models...")
    from bot.models import TelegramUser
    count = TelegramUser.objects.count()
    print(f"✅ Found {count} users in database")
    
    print("\n🎉 All checks passed! App should start fine.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
