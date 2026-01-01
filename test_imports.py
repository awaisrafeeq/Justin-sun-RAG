#!/usr/bin/env python
"""Test imports to find startup issues."""

try:
    print("Testing imports...")
    
    # Test main app import
    print("1. Testing app.main...")
    from app.main import create_app
    print("   ✅ app.main imported successfully")
    
    # Test creating app
    print("2. Testing app creation...")
    app = create_app()
    print("   ✅ App created successfully")
    
    # Test chat router import
    print("3. Testing chat router...")
    from app.api.chat import router
    print("   ✅ Chat router imported successfully")
    
    # Test query handler service
    print("4. Testing query handler service...")
    from app.services.query_handler import QueryHandlerService
    service = QueryHandlerService()
    print("   ✅ Query handler service created successfully")
    
    print("\n🎉 All imports and basic initialization successful!")
    print("The server should be able to start without import errors.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
