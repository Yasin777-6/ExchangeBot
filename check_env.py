#!/usr/bin/env python
"""
Check environment variables
Run this on Railway to diagnose issues
"""

import os
import sys

print("=" * 50)
print("ENVIRONMENT VARIABLES CHECK")
print("=" * 50)

required_vars = [
    'TELEGRAM_BOT_TOKEN',
    'DATABASE_URL',
    'SECRET_KEY',
]

optional_vars = [
    'DEBUG',
    'ALLOWED_HOSTS',
    'CSRF_TRUSTED_ORIGINS',
    'PORT',
]

print("\n✅ REQUIRED Variables:")
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Show only first 20 chars for security
        masked = value[:20] + '...' if len(value) > 20 else value
        print(f"  {var}: {masked}")
    else:
        print(f"  ❌ {var}: NOT SET!")

print("\n⚙️ OPTIONAL Variables:")
for var in optional_vars:
    value = os.getenv(var)
    if value:
        print(f"  {var}: {value}")
    else:
        print(f"  {var}: not set (using default)")

print("\n" + "=" * 50)

# Check if critical vars are missing
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f"\n❌ ERROR: Missing required variables: {', '.join(missing)}")
    print("\nSet these in Railway dashboard:")
    print("  1. Go to your service")
    print("  2. Click 'Variables' tab")
    print("  3. Add missing variables")
    sys.exit(1)
else:
    print("\n✅ All required variables are set!")
    sys.exit(0)
