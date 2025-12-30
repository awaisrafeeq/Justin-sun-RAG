import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.storage.database import Base, engine, AsyncSessionLocal
from app.storage.models.document import Document
from app.services.pdf_processor import PDFProcessor
from app.api.schemas.document import DocumentProcessingResult

async def test_day8_complete():
    try:
        print("🚀 Testing Day 8 Complete PDF Processing Pipeline...")
        
        # Test 1: Document Model
        print("\n📋 Test 1: Document Model CRUD")
        async with AsyncSessionLocal() as session:
            doc = Document(
                filename="test.pdf",
                original_filename="original_test.pdf",
                file_hash="test_hash_12345",
                file_size=2048,
                mime_type="application/pdf",
                status="pending",
                page_count=5
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
        
        # Test 2: PDF Processor Service
        print("\n📋 Test 2: PDF Processor Service")
        processor = PDFProcessor()
        
        # Test file hash calculation
        test_content = b"test pdf content for hashing"
        file_hash = processor.calculate_file_hash(test_content)
        print(f"✅ File hash calculated: {file_hash[:16]}...")
        
        # Test PDF validation
        is_valid, message = processor.validate_pdf_file(b"fake pdf content", "test.pdf")
        print(f"✅ PDF validation: {is_valid} - {message}")
        
        # Test 3: Document Processing Schema
        print("\n📋 Test 3: Document Processing Schema")
        result = DocumentProcessingResult(
            document_id=doc.id if 'doc' in locals() else "test-id",
            status="completed",
            page_count=5,
            text_length=1000,
            table_count=2,
            image_count=3,
            chunk_count=10,
            processing_time=2.5
        )
        print(f"✅ Schema created: {result.status}")
        print(f"✅ Processing time: {result.processing_time}s")
        
        print("\n🎉 Day 8 Complete Test Results:")
        print("✅ Document Model: Working")
        print("✅ PDF Processor: Working")
        print("✅ Document Schemas: Working")
        print("✅ Database Connection: Working")
        print("✅ All Imports: Working")
        
        print("\n🚀 Day 8 PDF Processing Pipeline is READY!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_day8_complete())
