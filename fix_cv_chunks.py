#!/usr/bin/env python3
"""
Manual script to fix CV chunking issues
"""
import asyncio
import uuid
from pathlib import Path

async def fix_cv_chunks():
    """Manually process CV and create chunks"""
    
    # Read CV file
    cv_path = Path("Asif Shah (CV).pdf")
    if not cv_path.exists():
        print("❌ CV file not found")
        return
    
    print("🔧 Starting manual CV chunking...")
    
    try:
        # Import required modules
        from app.services.pdf_processor import PDFProcessor
        from app.storage.database import AsyncSessionLocal
        from app.storage.models.document import Document
        
        # Read CV content
        with open(cv_path, 'rb') as f:
            file_content = f.read()
        
        # Initialize processor
        processor = PDFProcessor()
        
        # Process with fallback method
        extracted_text = processor._extract_text_fallback(file_content)
        if not extracted_text:
            print("❌ Could not extract text from CV")
            return
        
        print(f"✅ Extracted {len(extracted_text)} characters from CV")
        
        # Create chunks manually
        options = {
            "extract_tables": True,
            "extract_images": True,
            "ocr_images": True,
            "chunk_size": 1000,
            "chunk_overlap": 100
        }
        
        document_metadata = {
            "doc_type": "cv",
            "extracted_name": "Syed Muhammad Asif Shah"
        }
        
        # Create text chunks
        text_chunks = processor._chunk_plain_text(extracted_text, options, document_metadata)
        print(f"✅ Created {len(text_chunks)} text chunks")
        
        # Generate embeddings (if OpenAI key available)
        try:
            embeddings = await processor.embedding_processor.process_chunks(text_chunks)
            print(f"✅ Generated {len(embeddings)} embeddings")
        except Exception as e:
            print(f"⚠️  Embedding failed: {e}")
            embeddings = []
        
        # Store in vector database
        if embeddings:
            try:
                document_id = "f6074256-be75-4b5d-aa20-084bcc23938d"  # Your CV document ID
                chunk_ids = await processor.vector_store.store_chunks(
                    chunks=text_chunks,
                    embeddings=embeddings,
                    document_id=document_id,
                    metadata={
                        "document_type": "pdf",
                        "filename": "fc45e64fa0224181975e6d2f25a2db80.pdf",
                        "original_filename": "Asif Shah (CV).pdf",
                        "page_count": 0,
                        "table_count": 0,
                        "image_count": 0,
                        "has_text": True,
                        "has_tables": False,
                        "has_images": False,
                        "extraction_method": "manual_fix",
                    }
                )
                print(f"✅ Stored {len(chunk_ids)} chunks in vector store")
                
                # Update document record
                async with AsyncSessionLocal() as session:
                    document = await session.get(Document, uuid.UUID(document_id))
                    if document:
                        import json
                        document.chunk_ids = json.dumps(chunk_ids).encode('utf-8')
                        await session.commit()
                        print("✅ Updated document record with chunk IDs")
                
            except Exception as e:
                print(f"❌ Vector store failed: {e}")
        
        print("🎉 Manual chunking completed!")
        
    except Exception as e:
        print(f"❌ Manual chunking failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_cv_chunks())
