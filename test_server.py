#!/usr/bin/env python
"""Test if Day 12 server is running."""

import requests

def test_server_health():
    """Test if server is running."""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("Server is running!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Server returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("Server is not running or not accessible")
        return False
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return False

def test_chat_health():
    """Test chat health endpoint."""
    try:
        response = requests.get("http://127.0.0.1:8000/chat/health", timeout=5)
        if response.status_code == 200:
            print("Chat health endpoint working!")
            print(f"Chat services: {response.json()}")
            return True
        else:
            print(f"Chat health returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Chat health error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Day 12 Server...")
    
    if test_server_health():
        test_chat_health()
    else:
        print("Please start the server with:")
        print("python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
