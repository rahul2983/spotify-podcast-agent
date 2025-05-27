#!/usr/bin/env python3
import os
import sys

print("=== RAILWAY STARTUP ===")

# Check if we're in Railway environment
if 'RAILWAY_ENVIRONMENT' in os.environ:
    print("✅ Running in Railway environment")
else:
    print("⚠️  Not in Railway environment")

# Print all environment variables for debugging
print("\n=== ALL ENVIRONMENT VARIABLES ===")
for key in sorted(os.environ.keys()):
    if any(word in key.upper() for word in ['SPOTIFY', 'OPENAI', 'RAILWAY', 'PORT']):
        value = os.environ[key]
        if 'SECRET' in key or 'KEY' in key:
            masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
            print(f"{key}={masked_value}")
        else:
            print(f"{key}={value}")

# Check required variables
required_vars = ['OPENAI_API_KEY', 'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'SPOTIFY_REDIRECT_URI']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)
        print(f"❌ Missing: {var}")
    else:
        print(f"✅ Found: {var}")

if missing_vars:
    print(f"\n❌ FATAL: Missing environment variables: {missing_vars}")
    print("Please check Railway dashboard > Variables tab")
    sys.exit(1)

print("\n✅ All environment variables present, starting application...")

# Set PORT for Railway if not set
if not os.getenv('PORT'):
    os.environ['PORT'] = '8000'

# Start the application
try:
    from main import main
    main()
except Exception as e:
    print(f"❌ Failed to start application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
