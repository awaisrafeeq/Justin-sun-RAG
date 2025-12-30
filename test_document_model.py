import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.storage.database import Base, engine, AsyncSessionLocal
from app.storage.models.document import Document

async def test_document_crud():
    try:
        print("🚀 Starting Document Model Test...")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Created database tables")

        # Test CRUD operations
        async with AsyncSessionLocal() as session:
            # Create
            doc = Document(
                filename="test.pdf",
                original_filename="original_test.pdf",
                file_hash="test_hash_12345",
                file_size=1024,
                mime_type="application/pdf",
                status="pending",
                page_count=5
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            print(f"✅ Created document: {doc.id}")

            # Read
            retrieved = await session.get(Document, doc.id)
            print(f"✅ Retrieved document: {retrieved.filename}")
            print(f"   - Status: {retrieved.status}")
            print(f"   - Pages: {retrieved.page_count}")

            # Update
            retrieved.status = "processed"
            retrieved.page_count = 10
            await session.commit()
            await session.refresh(retrieved)
            print(f"✅ Updated document: {retrieved.status}, {retrieved.page_count} pages")

            # Clean up
            await session.delete(retrieved)
            await session.commit()
            print("✅ Deleted test document")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_document_crud())
