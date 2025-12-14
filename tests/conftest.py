import sys
from pathlib import Path

# Add project root to path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def chat_system(client):
    """Helper to call the chat endpoint"""
    def _chat(message: str) -> str:
        response = client.post("/chat", json={"message": message})
        if response.status_code == 200:
            return response.json().get("reply", "")
        return f"Error: {response.status_code}"
    return _chat
