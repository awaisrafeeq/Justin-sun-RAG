#!/usr/bin/env python
"""Celery worker startup script that loads environment variables."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Construct DATABASE_URL if not provided
if not os.getenv('DATABASE_URL'):
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'rag_chatbot')
    db_user = os.getenv('POSTGRES_USER', 'rag_user')
    db_pass = os.getenv('POSTGRES_PASSWORD', 'rag_pass')
    
    os.environ['DATABASE_URL'] = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    print(f"Constructed DATABASE_URL: postgresql+asyncpg://{db_user}:***@{db_host}:{db_port}/{db_name}")

# Verify critical environment variables
required_vars = ['OPENAI_API_KEY', 'DATABASE_URL']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"ERROR: Missing environment variables: {missing_vars}")
    exit(1)

print("Environment variables loaded successfully")
print(f"OPENAI_API_KEY: {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")
print(f"DATABASE_URL: {'✓' if os.getenv('DATABASE_URL') else '✗'}")

# Start Celery worker
import subprocess
import sys

cmd = [
    sys.executable, '-m', 'celery',
    '-A', 'workers.celery_app:celery_app',
    'worker',
    '-l', 'INFO',
    '-Q', 'ingestion,processing',
    '-P', 'solo',
    '--concurrency=1'
]

print(f"Starting Celery with: {' '.join(cmd)}")
subprocess.run(cmd)
