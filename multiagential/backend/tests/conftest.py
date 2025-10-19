"""
Pytest fixtures for backend testing
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# Add parent directory to Python path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set test environment variables before importing app
os.environ["OPENROUTER_API_KEY"] = "test-key-12345"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379"


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls"""
    with patch("openai.OpenAI") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance

        # Mock completion response
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Mocked response"
        mock_instance.chat.completions.create.return_value = mock_completion

        yield mock_instance


@pytest.fixture
def sample_onboarding_data():
    """Sample onboarding data for testing"""
    return {
        "interests": ["Python Programming", "Machine Learning"],
        "learning_goals": ["career_change"],
        "time_commitment": 10,
        "learning_style": "interactive",
        "skill_level": "beginner",
        "background": "Some programming experience"
    }


@pytest.fixture
def sample_learner_profile():
    """Sample learner profile for testing"""
    return {
        "overall_skill_level": "beginner",
        "interests": ["Python Programming", "Machine Learning"],
        "learning_goals": ["career_change"],
        "time_commitment": 10,
        "learning_style": "interactive",
        "strengths": ["Eager to learn", "Good foundation"],
        "knowledge_gaps": ["Advanced concepts", "Best practices"]
    }


@pytest.fixture
def sample_learning_journey():
    """Sample learning journey for testing"""
    return [
        {
            "topic": "Python Basics",
            "description": "Variables, data types, control flow",
            "estimated_hours": 5,
            "prerequisites": []
        },
        {
            "topic": "Functions and Modules",
            "description": "Function definition, modules, packages",
            "estimated_hours": 4,
            "prerequisites": ["Python Basics"]
        },
        {
            "topic": "Data Structures",
            "description": "Lists, dictionaries, sets, tuples",
            "estimated_hours": 6,
            "prerequisites": ["Python Basics"]
        }
    ]


@pytest.fixture
def sample_quiz_questions():
    """Sample quiz questions for testing"""
    return [
        {
            "question": "What is a variable in Python?",
            "options": [
                "A container for storing data",
                "A function",
                "A loop",
                "A class"
            ],
            "answer": "A container for storing data",
            "explanation": "Variables store data values in memory"
        },
        {
            "question": "Which data type is mutable?",
            "options": ["Tuple", "String", "List", "Integer"],
            "answer": "List",
            "explanation": "Lists can be modified after creation"
        }
    ]


@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return {
        "content": "# Python Variables\n\nVariables are containers...",
        "exercises": [
            {
                "description": "Create a variable and print it",
                "type": "coding"
            }
        ],
        "resources": [
            {
                "title": "Python Tutorial",
                "url": "https://docs.python.org/3/tutorial/",
                "type": "web"
            }
        ],
        "diagram": "graph TD\n    A[Variable] --> B[Value]\n    A --> C[Type]"
    }


@pytest.fixture
def mock_db():
    """Mock database operations"""
    with patch("db_postgres.get_user") as mock_get_user, \
         patch("db_postgres.create_user") as mock_create_user, \
         patch("db_postgres.get_user_profile") as mock_get_profile, \
         patch("db_postgres.create_user_profile") as mock_create_profile, \
         patch("db_postgres.create_learning_journey") as mock_create_journey, \
         patch("db_postgres.log_agent_decision") as mock_log_decision, \
         patch("db_postgres.get_topic_mastery") as mock_get_mastery:

        # Configure return values
        mock_get_user.return_value = None
        mock_get_profile.return_value = {
            "skill_level": "beginner",
            "interests": ["Python"],
            "learning_goals": ["career_change"]
        }
        mock_get_mastery.return_value = None

        yield {
            "get_user": mock_get_user,
            "create_user": mock_create_user,
            "get_profile": mock_get_profile,
            "create_profile": mock_create_profile,
            "create_journey": mock_create_journey,
            "log_decision": mock_log_decision,
            "get_mastery": mock_get_mastery
        }


@pytest.fixture
def app_client():
    """FastAPI test client"""
    # Import after environment variables are set
    from main import app
    return TestClient(app)
