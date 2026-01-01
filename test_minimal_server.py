#!/usr/bin/env python
"""Minimal server test."""

if __name__ == "__main__":
    try:
        print("Starting minimal server test...")
        
        # Import and create app
        from app.main import create_app
        app = create_app()
        
        print("App created successfully!")
        print("Available routes:")
        for route in app.routes:
            print(f"  {route.methods} {route.path}")
        
        print("\nStarting server on http://127.0.0.1:8001")
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
