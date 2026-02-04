"""Tests for the Mergington High School Activities API."""

import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test."""
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
    
    yield
    
    # Restore original data after test
    for key in list(activities.keys()):
        activities[key]["participants"] = original_data[key]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have the expected activities
        expected_activities = [
            "Basketball", "Tennis Club", "Debate Team", "Science Olympiad",
            "Drama Club", "Art Studio", "Chess Club", "Programming Class", "Gym Class"
        ]
        for activity in expected_activities:
            assert activity in data
    
    def test_get_activities_returns_activity_details(self, client):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "newtudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newtudent@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant."""
        email = "test@mergington.edu"
        
        # Check initial state
        response = client.get("/activities")
        initial_participants = response.json()["Basketball"]["participants"]
        
        # Sign up
        client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        
        # Check updated state
        response = client.get("/activities")
        updated_participants = response.json()["Basketball"]["participants"]
        
        assert len(updated_participants) == len(initial_participants) + 1
        assert email in updated_participants
    
    def test_signup_for_nonexistent_activity_returns_404(self, client):
        """Test that signup for non-existent activity returns 404."""
        response = client.post(
            "/activities/NonexistentActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_registered_returns_400(self, client):
        """Test that signup for already registered student returns 400."""
        # Try to sign up someone already in Basketball
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_students(self, client):
        """Test that multiple students can sign up for same activity."""
        students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for student in students:
            response = client.post(
                "/activities/Tennis Club/signup",
                params={"email": student}
            )
            assert response.status_code == 200
        
        # Verify all students are registered
        response = client.get("/activities")
        participants = response.json()["Tennis Club"]["participants"]
        for student in students:
            assert student in participants


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_from_activity_success(self, client):
        """Test successful unregister from an activity."""
        response = client.post(
            "/activities/Basketball/unregister",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "alex@mergington.edu" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant."""
        email = "alex@mergington.edu"
        
        # Verify participant exists before
        response = client.get("/activities")
        assert email in response.json()["Basketball"]["participants"]
        
        # Unregister
        client.post(
            "/activities/Basketball/unregister",
            params={"email": email}
        )
        
        # Verify participant is removed
        response = client.get("/activities")
        assert email not in response.json()["Basketball"]["participants"]
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test that unregister from non-existent activity returns 404."""
        response = client.post(
            "/activities/NonexistentActivity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered_returns_400(self, client):
        """Test that unregister of not-registered student returns 400."""
        response = client.post(
            "/activities/Basketball/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_then_signup_again(self, client):
        """Test that a student can sign up again after unregistering."""
        email = "student@mergington.edu"
        activity = "Tennis Club"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Sign up again
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200


class TestRootRedirect:
    """Tests for GET / endpoint."""
    
    def test_root_redirects_to_static_html(self, client):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegrationScenarios:
    """Integration tests for common activity management scenarios."""
    
    def test_full_signup_and_unregister_flow(self, client):
        """Test complete signup and unregister flow."""
        email = "integration_test@mergington.edu"
        activity = "Science Olympiad"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count
        assert email not in response.json()[activity]["participants"]
    
    def test_multiple_students_in_activity(self, client):
        """Test multiple students can be in the same activity."""
        activity = "Drama Club"
        new_students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Sign up new students
        for student in new_students:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": student}
            )
            assert response.status_code == 200
        
        # Verify all students including originals
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        
        for student in new_students:
            assert student in participants
        
        # Original participants should still be there
        assert "grace@mergington.edu" in participants
        assert "lucas@mergington.edu" in participants
