#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.storage.database import AsyncSessionLocal

async def check_episode_table():
    async with AsyncSessionLocal() as session:
        try:
            # Check if episodes table exists
            result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'episodes'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("Episodes table columns:")
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
            
            # Check if table exists at all
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'episodes'
                )
            """))
            
            table_exists = result.scalar()
            print(f"\nTable exists: {table_exists}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_episode_table())
