import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.storage.database import AsyncSessionLocal

async def check_document_columns():
    """Check what columns actually exist in the documents table."""
    print("🔍 Checking actual database schema...")
    
    async with AsyncSessionLocal() as session:
        # Get actual column names from database
        result = await session.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'documents' 
            ORDER BY ordinal_position
        """)
        
        columns = result.fetchall()
        print(f"\n📋 Actual columns in 'documents' table:")
        for col_name, data_type, is_nullable in columns:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"   - {col_name}: {data_type} ({nullable})")
        
        print(f"\n📊 Total columns: {len(columns)}")
        
        # Check if table exists
        table_check = await session.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'documents'
            )
        """)
        table_exists = table_check.scalar()
        print(f"📁 Table exists: {table_exists}")

if __name__ == "__main__":
    asyncio.run(check_document_columns())
