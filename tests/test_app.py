"""
Tests for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities GET endpoint"""
    
    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_not_empty(self):
        """Test that there are activities in the database"""
        response = client.get("/activities")
        activities = response.json()
        assert len(activities) > 0


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup POST endpoint"""
    
    def test_signup_successful(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_signup_nonexistent_activity(self):
        """Test signup for nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
    
    def test_signup_duplicate_student(self):
        """Test that signing up twice returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup
        response1 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister POST endpoint"""
    
    def test_unregister_successful(self):
        """Test successful unregister from an activity"""
        email = "unregister_test@mergington.edu"
        activity = "Basketball Club"
        
        # First signup
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        data = unregister_response.json()
        assert "message" in data
    
    def test_unregister_nonexistent_activity(self):
        """Test unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonexistentActivity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
    
    def test_unregister_not_registered(self):
        """Test unregister when student is not registered returns 400"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removal_test@mergington.edu"
        activity = "Swimming Team"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check participant is there
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Check participant is gone
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]


class TestIntegration:
    """Integration tests for signup and unregister workflows"""
    
    def test_signup_and_unregister_workflow(self):
        """Test complete signup and unregister workflow"""
        email = "workflow@mergington.edu"
        activity = "Art Workshop"
        
        # Initial state - participant not in list
        activities = client.get("/activities").json()
        initial_count = len(activities[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count + 1
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == initial_count
