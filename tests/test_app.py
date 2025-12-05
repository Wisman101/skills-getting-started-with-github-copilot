"""Tests for the Mergington High School API"""
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_fields(self):
        """Test that activities contain expected fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_contains_chess_club(self):
        """Test that Chess Club is in the activities list"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@example.com"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonexistentClub/signup?email=test@example.com"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student(self):
        """Test that duplicate signups are rejected"""
        email = "duplicate@example.com"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister@example.com"
        
        # First signup
        signup_response = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        unregister_response = client.delete(
            f"/activities/Programming%20Class/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        assert "Unregistered" in unregister_response.json()["message"]

    def test_unregister_invalid_activity(self):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/NonexistentClub/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_registered_student(self):
        """Test unregister when student is not registered"""
        response = client.delete(
            "/activities/Soccer%20Team/unregister?email=notregistered@example.com"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removal@example.com"
        activity = "Drama%20Club"
        
        # Signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Get participants before unregister
        response_before = client.get("/activities")
        activity_name = "Drama Club"
        participants_before = response_before.json()[activity_name]["participants"]
        assert email in participants_before
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Get participants after unregister
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        assert email not in participants_after


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_root_redirects_to_static(self):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_email_with_special_characters(self):
        """Test signup with email containing special characters"""
        email = "test+special@example.com"
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 200

    def test_activity_name_with_spaces(self):
        """Test that activity names with spaces are handled correctly"""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify activities with spaces exist
        space_activities = [name for name in activities if " " in name]
        assert len(space_activities) > 0
