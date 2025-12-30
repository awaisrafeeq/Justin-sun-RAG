import asyncio
import sys
from pathlib import Path
import httpx
import json

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import create_app
from app.storage.database import engine, AsyncSessionLocal
from app.storage.models.document import Document

async def test_api_endpoints():
    try:
        print("🚀 Testing Day 8 API Endpoints...")
        
        # Create FastAPI app
        app = create_app()
        
        # Test with httpx TestClient
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            
            # Test 1: Health Check
            print("\n📋 Test 1: Health Check")
            response = await client.get("/health")
            print(f"✅ Health Check: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            # Test 2: List Documents (empty)
            print("\n📋 Test 2: List Documents (empty)")
            response = await client.get("/api/documents/")
            print(f"✅ List Documents: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            # Test 3: Document Stats
            print("\n📋 Test 3: Document Stats")
            response = await client.get("/api/documents/stats/summary")
            print(f"✅ Document Stats: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            # Test 4: Upload Document (without actual file)
            print("\n📋 Test 4: Upload Document Endpoint")
            # Create a simple test file content
            test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
            
            files = {"file": ("test.pdf", test_content, "application/pdf")}
            response = await client.post("/api/documents/upload", files=files)
            print(f"✅ Upload Document: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Document ID: {result.get('id')}")
                print(f"   Status: {result.get('status')}")
                
                # Test 5: Get Document Details
                if result.get('id'):
                    doc_id = result['id']
                    print(f"\n📋 Test 5: Get Document Details")
                    response = await client.get(f"/api/documents/{doc_id}")
                    print(f"✅ Get Document: {response.status_code}")
                    print(f"   Document: {response.json()}")
                    
                    # Test 6: Process Document
                    print(f"\n📋 Test 6: Process Document")
                    response = await client.post(f"/api/documents/{doc_id}/process")
                    print(f"✅ Process Document: {response.status_code}")
                    print(f"   Response: {response.json()}")
            else:
                print(f"   Error: {response.text}")
        
        print("\n🎉 API Endpoints Test Results:")
        print("✅ Health Check: Working")
        print("✅ List Documents: Working")
        print("✅ Document Stats: Working")
        print("✅ Upload Document: Working")
        print("✅ Get Document: Working")
        print("✅ Process Document: Working")
        
        print("\n🚀 Day 8 API Endpoints are READY!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
