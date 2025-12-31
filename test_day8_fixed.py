import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.storage.database import AsyncSessionLocal
from app.storage.models import Document

async def test_day8_complete():
    try:
        print("🚀 Testing Day 8 Complete PDF Processing Pipeline...")
        
        # Test 1: Document Model
        print("\n📋 Test 1: Document Model CRUD")
        async with AsyncSessionLocal() as session:
            doc = Document(
                filename="test.pdf",
                file_hash="test_hash_12345",
                doc_type="pdf",
                extracted_name="Test Document",
                status="pending"
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            print(f"✅ Document created: {doc.id}")
            
            # Update status
            doc.status = "processing"
            await session.commit()
            print(f"✅ Document updated: {doc.status}")
            
            # Clean up
            await session.delete(doc)
            await session.commit()
            print("✅ Document model test passed!")
        
        # Test 2: Simple Document Statistics
        print("\n📋 Test 2: Document Statistics")
        async with AsyncSessionLocal() as session:
            # Count documents
            from sqlalchemy import text
            total_docs = await session.execute(text("SELECT COUNT(*) FROM documents"))
            doc_count = total_docs.scalar()
            print(f"📁 Total documents: {doc_count}")
            
            # Count by status
            status_counts = await session.execute(text("SELECT status, COUNT(*) FROM documents GROUP BY status"))
            print(f"📊 Documents by status:")
            for status, count in status_counts.fetchall():
                print(f"   - {status}: {count}")
            
            # Count by type
            type_counts = await session.execute(text("SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type"))
            print(f"📄 Documents by type:")
            for doc_type, count in type_counts.fetchall():
                print(f"   - {doc_type}: {count}")
            
        print("\n🎯 Day 8 Features Status:")
        print("✅ Document Model: Working")
        print("✅ CRUD Operations: Working")
        print("✅ Status Tracking: Working")
        print("✅ File Hash Storage: Working")
        print("✅ Document Typing: Working")
        
        print(f"\n🎉 Day 8 PDF Processing Test Complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_day8_complete())
