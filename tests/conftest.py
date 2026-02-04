"""Pytest configuration and fixtures for FastAPI tests."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def app_with_fresh_data():
    """Provide app with reset activities data for each test."""
    from app import activities
    
    # Store original data
    original_data = {
        key: {
            "description": value["description"],
            "schedule": value["schedule"],
            "max_participants": value["max_participants"],
            "participants": value["participants"].copy()
        }
        for key, value in activities.items()
    }
    
    yield app
    
    # Restore original data after test
    for key in list(activities.keys()):
        activities[key]["participants"] = original_data[key]["participants"].copy()
