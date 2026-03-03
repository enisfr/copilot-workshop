"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_activity():
    """Provide a sample activity name for testing"""
    return "Chess Club"


@pytest.fixture
def sample_email():
    """Provide a sample email for testing"""
    return "test@mergington.edu"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def should_return_all_activities_when_getting_activities(self, client):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data

    def should_contain_required_fields_in_each_activity(self, client):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def should_have_valid_email_format_for_all_participants(self, client):
        """Test that participants list contains valid email addresses"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert "@" in participant
                assert isinstance(participant, str)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def should_successfully_signup_for_activity(self, client, sample_email):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]

    def should_add_participant_to_activity_when_signing_up(self, client, sample_email):
        """Test that signup actually adds the participant to the activity list"""
        # Get initial participants count
        response = client.get("/activities")
        initial_participants = len(response.json()["Chess Club"]["participants"])
        
        # Sign up
        client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        new_participants = len(response.json()["Chess Club"]["participants"])
        assert new_participants == initial_participants + 1

    def should_return_404_when_signing_up_for_nonexistent_activity(self, client, sample_email):
        """Test that signup to a nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def should_return_400_when_already_signed_up(self, client):
        """Test that signing up with an already registered email returns 400"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def should_reject_empty_email_on_signup(self, client):
        """Test signup with empty email"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        # Should fail validation or be treated as invalid
        assert response.status_code != 200

    def should_preserve_existing_participants_when_adding_new_one(self, client, sample_email):
        """Test that signup preserves existing participants"""
        # Get existing participants
        response = client.get("/activities")
        existing_participants = set(response.json()["Chess Club"]["participants"])
        
        # Sign up new participant
        client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        
        # Verify existing participants are still there
        response = client.get("/activities")
        new_participants = set(response.json()["Chess Club"]["participants"])
        assert existing_participants.issubset(new_participants)


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def should_successfully_unregister_from_activity(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Existing participant in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def should_remove_participant_from_activity_when_unregistering(self, client):
        """Test that unregister actually removes the participant"""
        # First, sign up a new participant
        test_email = "unregister_test@mergington.edu"
        client.post(
            "/activities/Programming Class/signup",
            params={"email": test_email}
        )
        
        # Verify they're signed up
        response = client.get("/activities")
        assert test_email in response.json()["Programming Class"]["participants"]
        
        # Unregister
        client.delete(
            "/activities/Programming Class/unregister",
            params={"email": test_email}
        )
        
        # Verify they're removed
        response = client.get("/activities")
        assert test_email not in response.json()["Programming Class"]["participants"]

    def should_return_404_when_unregistering_from_nonexistent_activity(self, client):
        """Test that unregister from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def should_return_404_when_unregistering_nonexistent_participant(self, client):
        """Test that unregistering a non-participant returns 404"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "nonexistent@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def should_preserve_other_participants_when_unregistering_one(self, client):
        """Test that unregister preserves other participants in the activity"""
        initial_response = client.get("/activities")
        initial_participants = set(initial_response.json()["Chess Club"]["participants"])
        
        # Remove one participant
        participant_to_remove = list(initial_participants)[0]
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": participant_to_remove}
        )
        
        # Verify other participants are still there
        response = client.get("/activities")
        remaining_participants = set(response.json()["Chess Club"]["participants"])
        expected_participants = initial_participants - {participant_to_remove}
        assert remaining_participants == expected_participants

    def should_fail_when_unregistering_same_participant_twice(self, client):
        """Test that unregistering the same person twice fails"""
        test_email = "double_unregister@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Gym Class/signup",
            params={"email": test_email}
        )
        
        # First unregister should succeed
        response1 = client.delete(
            "/activities/Gym Class/unregister",
            params={"email": test_email}
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.delete(
            "/activities/Gym Class/unregister",
            params={"email": test_email}
        )
        assert response2.status_code == 404
