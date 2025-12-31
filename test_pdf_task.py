#!/usr/bin/env python
"""Test Day 10 with file content"""
from workers.tasks import process_pdf_task

# Read the PDF file
with open('langchain_lecture_1.pdf', 'rb') as f:
    file_content = f.read()

# Queue the task with all required parameters
result = process_pdf_task.delay(
    document_id='4f8ab15c-d01f-4deb-a477-8280ebf57665',
    file_content=file_content,  # This is the missing parameter!
    original_filename='langchain_lecture_1.pdf',
    mime_type='application/pdf'
)

print(f'Task queued: {result.id}')
print('Watch Celery terminal for processing...')
