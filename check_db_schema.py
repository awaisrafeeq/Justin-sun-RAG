#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.storage.database import AsyncSessionLocal

async def check_rss_table():
    async with AsyncSessionLocal() as session:
        try:
            # Check if rss_feeds table exists
            result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'rss_feeds'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("RSS Feeds table columns:")
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
            
            # Check if table exists at all
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'rss_feeds'
                )
            """))
            
            table_exists = result.scalar()
            print(f"\nTable exists: {table_exists}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_rss_table())
