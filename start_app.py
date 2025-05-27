import os
import sys

print("=== STARTUP DEBUG ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Environment variables:")

required_vars = ['OPENAI_API_KEY', 'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'SPOTIFY_REDIRECT_URI']
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"  ✅ {var}: {'*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '***'}")
    else:
        print(f"  ❌ {var}: NOT SET")

try:
    print("Testing imports...")
    import fastapi
    print("  ✅ FastAPI imported")
    
    import uvicorn
    print("  ✅ Uvicorn imported")
    
    from spotify_agent.config import AgentConfig
    print("  ✅ Config imported")
    
    print("Creating config...")
    config = AgentConfig()
    print("  ✅ Config created")
    
    print("Starting main application...")
    from main import main
    main()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
