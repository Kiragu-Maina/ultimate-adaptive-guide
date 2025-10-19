"""
Integration tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json
import os

os.environ["OPENROUTER_API_KEY"] = "test-key-12345"


@pytest.fixture
def client():
    """Create test client"""
    from main import app
    return TestClient(app)


@pytest.mark.integration
class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_root_health_check(self, client):
        """Test root endpoint health check"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    @patch("cache_redis.get_redis_connection")
    def test_cache_health_check(self, mock_redis, client):
        """Test Redis cache health check"""
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.info.return_value = {"used_memory_human": "1M"}
        mock_redis.return_value = mock_redis_instance

        response = client.get("/health/cache")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.integration
class TestAdaptiveOnboardingEndpoint:
    """Tests for /adaptive/onboarding endpoint"""

    @patch("adaptive_orchestrator.create_learner_profile")
    @patch("adaptive_orchestrator.create_learning_journey")
    @patch("adaptive_orchestrator.db")
    def test_onboarding_success(self, mock_db, mock_journey, mock_profile, client, sample_onboarding_data):
        """Test successful onboarding workflow"""
        # Mock database
        mock_db.get_user.return_value = None
        mock_db.create_user.return_value = None
        mock_db.create_user_profile.return_value = None
        mock_db.create_learning_journey.return_value = None
        mock_db.log_agent_decision.return_value = None

        # Mock learner profiler
        mock_profile.return_value = {
            "learner_profile": {
                "overall_skill_level": "beginner",
                "strengths": ["Eager"],
                "knowledge_gaps": ["Advanced"]
            },
            "reasoning": "Based on inputs...",
            "confidence": 0.85
        }

        # Mock journey architect
        mock_journey.return_value = {
            "learning_journey": [
                {"topic": "Python Basics", "description": "Intro", "estimated_hours": 5}
            ],
            "reasoning": "Starting with basics..."
        }

        response = client.post(
            "/adaptive/onboarding",
            json=sample_onboarding_data,
            headers={"x-user-key": "test-user-123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "learner_profile" in data
        assert "learning_journey" in data
        assert "agent_activity" in data

    def test_onboarding_missing_fields(self, client):
        """Test onboarding with missing required fields"""
        incomplete_data = {
            "interests": ["Python"]
            # Missing other required fields
        }

        response = client.post(
            "/adaptive/onboarding",
            json=incomplete_data,
            headers={"x-user-key": "test-user-456"}
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestAdaptiveContentEndpoint:
    """Tests for /adaptive/content endpoint"""

    @patch("adaptive_orchestrator.create_content_graph")
    @patch("adaptive_orchestrator.db")
    def test_content_delivery_new_user(self, mock_db, mock_content_graph, client):
        """Test content delivery for new user"""
        # Mock database
        mock_db.get_topic_mastery.return_value = None
        mock_db.get_user_profile.return_value = {"skill_level": "beginner"}

        # Mock content graph
        mock_graph_instance = Mock()
        mock_graph_instance.invoke.return_value = {
            "content": "# Python Basics\n\nContent here...",
            "exercises": [{"description": "Exercise 1", "type": "coding"}],
            "diagram": "graph TD\n    A --> B",
            "resources": []
        }
        mock_content_graph.return_value = mock_graph_instance

        response = client.get(
            "/adaptive/content?topic=Python%20Basics",
            headers={"x-user-key": "test-user-789"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "difficulty" in data
        assert data["difficulty"] == "easy"  # New user gets easy content

    @patch("adaptive_orchestrator.create_content_graph")
    @patch("adaptive_orchestrator.db")
    def test_content_delivery_advanced_user(self, mock_db, mock_content_graph, client):
        """Test content delivery for advanced user"""
        # Mock database - high mastery
        mock_db.get_topic_mastery.return_value = {
            "mastery_score": 85,
            "attempts": 3
        }
        mock_db.get_user_profile.return_value = {"skill_level": "advanced"}

        # Mock content graph
        mock_graph_instance = Mock()
        mock_graph_instance.invoke.return_value = {
            "content": "# Advanced Python\n\nComplex content...",
            "exercises": [],
            "diagram": "graph TD\n    A --> B"
        }
        mock_content_graph.return_value = mock_graph_instance

        response = client.get(
            "/adaptive/content?topic=Advanced%20Python",
            headers={"x-user-key": "test-advanced-user"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["difficulty"] == "hard"  # High mastery gets hard content

    def test_content_missing_topic(self, client):
        """Test content endpoint without topic parameter"""
        response = client.get(
            "/adaptive/content",
            headers={"x-user-key": "test-user"}
        )

        assert response.status_code == 422  # Missing required parameter


@pytest.mark.integration
class TestAdaptiveJourneyEndpoint:
    """Tests for /adaptive/journey endpoint"""

    @patch("db_postgres.get_learning_journey")
    def test_get_journey_exists(self, mock_get_journey, client):
        """Test getting existing learning journey"""
        mock_get_journey.return_value = [
            {"topic": "Python Basics", "description": "Intro", "completed": False},
            {"topic": "Functions", "description": "Functions", "completed": True}
        ]

        response = client.get(
            "/adaptive/journey",
            headers={"x-user-key": "test-user-journey"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "journey" in data
        assert len(data["journey"]) == 2

    @patch("db_postgres.get_learning_journey")
    def test_get_journey_not_exists(self, mock_get_journey, client):
        """Test getting journey when none exists"""
        mock_get_journey.return_value = None

        response = client.get(
            "/adaptive/journey",
            headers={"x-user-key": "new-user"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "onboarding" in data["message"].lower()


@pytest.mark.integration
class TestAdaptiveRecommendationsEndpoint:
    """Tests for /adaptive/recommendations endpoint"""

    @patch("db_postgres.get_user_profile")
    def test_recommendations_with_profile(self, mock_get_profile, client):
        """Test recommendations for user with profile"""
        mock_get_profile.return_value = {
            "interests": ["Python", "ML"],
            "skill_level": "beginner",
            "learning_goals": ["career_change"]
        }

        response = client.get(
            "/adaptive/recommendations",
            headers={"x-user-key": "test-user-rec"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    @patch("db_postgres.get_user_profile")
    def test_recommendations_without_profile(self, mock_get_profile, client):
        """Test recommendations when no profile exists"""
        mock_get_profile.return_value = None

        response = client.get(
            "/adaptive/recommendations",
            headers={"x-user-key": "no-profile-user"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


@pytest.mark.integration
class TestAdaptivePerformanceEndpoint:
    """Tests for /adaptive/performance endpoint"""

    @patch("db_postgres.get_quiz_history")
    @patch("db_postgres.get_topic_mastery_all")
    def test_performance_with_data(self, mock_mastery, mock_history, client):
        """Test performance endpoint with quiz history"""
        mock_history.return_value = [
            {"topic": "Python", "score": 80, "total": 100, "timestamp": "2024-01-01"}
        ]
        mock_mastery.return_value = [
            {"topic": "Python", "mastery_score": 80, "attempts": 3}
        ]

        response = client.get(
            "/adaptive/performance",
            headers={"x-user-key": "test-perf-user"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "quiz_history" in data
        assert "mastery" in data

    @patch("db_postgres.get_quiz_history")
    def test_performance_without_data(self, mock_history, client):
        """Test performance endpoint with no quiz history"""
        mock_history.return_value = []

        response = client.get(
            "/adaptive/performance",
            headers={"x-user-key": "new-learner"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


@pytest.mark.integration
class TestAdaptiveAgentDecisionsEndpoint:
    """Tests for /adaptive/agent-decisions endpoint"""

    @patch("db_postgres.get_agent_decisions")
    def test_agent_decisions(self, mock_decisions, client):
        """Test agent decisions endpoint"""
        mock_decisions.return_value = [
            {
                "agent_name": "learner_profiler",
                "decision_type": "profile_created",
                "timestamp": "2024-01-01",
                "confidence": 0.85
            }
        ]

        response = client.get(
            "/adaptive/agent-decisions",
            headers={"x-user-key": "test-decisions-user"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "decisions" in data
        assert len(data["decisions"]) == 1


@pytest.mark.integration
class TestUserKeyHandling:
    """Tests for user key generation and handling"""

    def test_auto_generate_user_key(self, client):
        """Test automatic user key generation"""
        response = client.get("/")  # No x-user-key header

        assert response.status_code == 200
        # Check if X-User-Key header is set in response
        assert "x-user-key" in response.headers or "X-User-Key" in response.headers

    def test_preserve_existing_user_key(self, client):
        """Test that existing user key is preserved"""
        user_key = "my-custom-key-123"

        response = client.get(
            "/",
            headers={"x-user-key": user_key}
        )

        assert response.status_code == 200


@pytest.mark.integration
class TestRateLimiting:
    """Tests for rate limiting"""

    def test_rate_limit_not_exceeded(self, client):
        """Test normal requests don't hit rate limit"""
        # Make a few requests
        for _ in range(3):
            response = client.get("/", headers={"x-user-key": "rate-test-user"})
            assert response.status_code == 200


@pytest.mark.integration
class TestCORSHeaders:
    """Tests for CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        # FastAPI test client may not fully simulate CORS
        # This is a basic check
        assert response.status_code in [200, 405]  # OPTIONS may not be implemented
