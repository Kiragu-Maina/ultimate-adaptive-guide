"""
Unit tests for all 8 adaptive learning agents
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import os

# Ensure API key is set
os.environ["OPENROUTER_API_KEY"] = "test-key-12345"


@pytest.mark.unit
class TestLearnerProfilerAgent:
    """Tests for Learner Profiler Agent"""

    @patch("learner_profiler_agent.client")
    def test_create_learner_profile(self, mock_client, sample_onboarding_data):
        """Test learner profile creation"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "overall_skill_level": "beginner",
            "strengths": ["Eager to learn"],
            "knowledge_gaps": ["Advanced concepts"],
            "recommended_pace": "moderate",
            "learning_preferences": ["interactive", "visual"]
        })
        mock_client.chat.completions.create.return_value = mock_response

        from learner_profiler_agent import create_learner_profile

        result = create_learner_profile(sample_onboarding_data)

        assert "learner_profile" in result
        assert "reasoning" in result
        assert "confidence" in result
        assert result["learner_profile"]["overall_skill_level"] == "beginner"
        assert isinstance(result["confidence"], float)


@pytest.mark.unit
class TestJourneyArchitectAgent:
    """Tests for Journey Architect Agent"""

    @patch("journey_architect_agent.client")
    def test_create_learning_journey(self, mock_client, sample_learner_profile):
        """Test learning journey creation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "learning_journey": [
                {
                    "topic": "Python Basics",
                    "description": "Variables and data types",
                    "estimated_hours": 5,
                    "prerequisites": []
                },
                {
                    "topic": "Functions",
                    "description": "Functions and modules",
                    "estimated_hours": 4,
                    "prerequisites": ["Python Basics"]
                }
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response

        from journey_architect_agent import create_learning_journey

        result = create_learning_journey(sample_learner_profile)

        assert "learning_journey" in result
        assert "reasoning" in result
        assert isinstance(result["learning_journey"], list)
        assert len(result["learning_journey"]) >= 1
        assert "topic" in result["learning_journey"][0]

    @patch("journey_architect_agent.client")
    def test_adjust_journey(self, mock_client, sample_learning_journey):
        """Test journey adjustment based on performance"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "adjusted_journey": sample_learning_journey,
            "changes_made": ["Added reinforcement topics"]
        })
        mock_client.chat.completions.create.return_value = mock_response

        from journey_architect_agent import adjust_journey

        performance_data = {
            "strengths": ["Python Basics"],
            "knowledge_gaps": ["Loops", "Functions"],
            "recent_scores": [45, 60]
        }

        result = adjust_journey(sample_learning_journey, performance_data)

        assert "adjusted_journey" in result
        assert "reasoning" in result
        assert isinstance(result["adjusted_journey"], list)


@pytest.mark.unit
class TestPerformanceAnalyzerAgent:
    """Tests for Performance Analyzer Agent"""

    @patch("performance_analyzer_agent.client")
    def test_analyze_performance(self, mock_client):
        """Test performance analysis"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "skill_level": "intermediate",
            "strengths": ["Python Basics", "Functions"],
            "knowledge_gaps": ["OOP", "Decorators"],
            "mastery_scores": {"Python Basics": 85, "Functions": 70},
            "recommendations": ["Focus on OOP concepts"]
        })
        mock_client.chat.completions.create.return_value = mock_response

        from performance_analyzer_agent import analyze_performance

        quiz_history = [
            {"topic": "Python Basics", "score": 85, "total": 100},
            {"topic": "Functions", "score": 70, "total": 100}
        ]

        result = analyze_performance("test_user", quiz_history)

        assert "skill_level" in result
        assert "strengths" in result
        assert "knowledge_gaps" in result
        assert isinstance(result["strengths"], list)


@pytest.mark.unit
class TestContentPersonalizerAgent:
    """Tests for Content Personalizer Agent (content_graph.py)"""

    @patch("content_graph.client")
    def test_content_generation(self, mock_client):
        """Test content personalization"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "content": "# Python Variables\n\nVariables are containers for storing data...",
            "exercises": [
                {"description": "Create variables", "type": "coding"}
            ],
            "resources": [
                {"title": "Python Docs", "url": "https://python.org", "type": "web"}
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response

        from content_graph import create_content_graph

        content_graph = create_content_graph()
        result = content_graph.invoke({
            "topic": "Python Variables",
            "skill_level": "beginner"
        })

        assert "content" in result
        assert "exercises" in result or "resources" in result
        assert isinstance(result.get("content", ""), str)


@pytest.mark.unit
class TestQuizGeneratorAgent:
    """Tests for Quiz Generator Agent"""

    @patch("quiz_generator_agent.client")
    def test_quiz_generation(self, mock_client):
        """Test adaptive quiz generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "questions": [
                {
                    "question": "What is a variable?",
                    "options": ["A", "B", "C", "D"],
                    "answer": "A",
                    "explanation": "Because..."
                }
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response

        from quiz_generator_agent import create_quiz_generator_graph

        quiz_graph = create_quiz_generator_graph()
        result = quiz_graph.invoke({
            "topic": "Python Basics",
            "user_id": "test_user",
            "skill_level": "beginner",
            "num_questions": 3
        })

        assert "questions" in result
        assert "difficulty" in result
        assert isinstance(result["questions"], list)

    @patch("quiz_generator_agent.client")
    def test_quiz_difficulty_levels(self, mock_client):
        """Test quiz generation at different difficulty levels"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "questions": [
                {"question": "Q1", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "E1"}
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response

        from quiz_generator_agent import create_quiz_generator_graph

        quiz_graph = create_quiz_generator_graph()

        for level in ["beginner", "intermediate", "advanced"]:
            result = quiz_graph.invoke({
                "topic": "Python",
                "user_id": "test",
                "skill_level": level,
                "num_questions": 2
            })
            assert result["difficulty"] == level


@pytest.mark.unit
class TestDiagramGeneratorAgent:
    """Tests for Diagram Generator Agent"""

    @patch("diagram_generator_agent.client")
    def test_diagram_generation(self, mock_client):
        """Test Mermaid diagram generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "graph TD\n    A[Start] --> B[End]"
        mock_client.chat.completions.create.return_value = mock_response

        from diagram_generator_agent import create_diagram_generator_graph

        diagram_graph = create_diagram_generator_graph()
        result = diagram_graph.invoke({
            "topic": "Python Data Flow"
        })

        assert "diagram" in result
        assert isinstance(result["diagram"], str)
        assert "graph" in result["diagram"].lower()

    @patch("diagram_generator_agent.client")
    def test_diagram_cleanup(self, mock_client):
        """Test diagram code cleanup (removes code blocks)"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "```mermaid\ngraph TD\n    A[Test]\n```"
        mock_client.chat.completions.create.return_value = mock_response

        from diagram_generator_agent import create_diagram_generator_graph

        diagram_graph = create_diagram_generator_graph()
        result = diagram_graph.invoke({"topic": "Test"})

        assert "```" not in result["diagram"]
        assert "graph TD" in result["diagram"]


@pytest.mark.unit
class TestRecommendationAgent:
    """Tests for Recommendation Agent"""

    @patch("recommendation_agent.client")
    def test_generate_recommendations(self, mock_client):
        """Test recommendation generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "recommendations": [
                {
                    "topic": "Python Loops",
                    "reason": "Identified knowledge gap",
                    "priority": "high"
                }
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response

        from recommendation_agent import generate_recommendations

        performance_data = {
            "strengths": ["Variables"],
            "knowledge_gaps": ["Loops", "Functions"],
            "recent_score": 60
        }

        result = generate_recommendations("test_user", "Python Basics", performance_data)

        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)


@pytest.mark.unit
class TestFeedbackAgent:
    """Tests for Feedback Agent (Motivation & Feedback)"""

    @patch("feedback_agent.client")
    def test_sentiment_analysis(self, mock_client):
        """Test sentiment analysis"""
        # Mock sentiment analysis
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "positive"
        mock_client.chat.completions.create.return_value = mock_response

        from feedback_agent import sentiment_analysis_tool

        result = sentiment_analysis_tool("I love this platform!")
        assert result in ["positive", "negative", "neutral"]

    @patch("feedback_agent.client")
    def test_feedback_generation(self, mock_client):
        """Test motivational feedback generation"""
        # Mock sentiment
        mock_sentiment = Mock()
        mock_sentiment.choices = [Mock()]
        mock_sentiment.choices[0].message.content = "positive"

        # Mock feedback
        mock_feedback = Mock()
        mock_feedback.choices = [Mock()]
        mock_feedback.choices[0].message.content = "Great job! Keep it up!"

        mock_client.chat.completions.create.side_effect = [mock_sentiment, mock_feedback]

        from feedback_agent import create_feedback_graph

        feedback_graph = create_feedback_graph()
        result = feedback_graph.invoke({
            "user_input": "I'm doing great!",
            "performance_context": {
                "strengths": ["Python Basics"],
                "knowledge_gaps": ["Advanced"],
                "recent_score": 85
            }
        })

        assert "sentiment" in result
        assert "feedback" in result
        assert isinstance(result["feedback"], str)

    @patch("feedback_agent.client")
    def test_feedback_without_performance_context(self, mock_client):
        """Test feedback generation without performance data"""
        mock_sentiment = Mock()
        mock_sentiment.choices = [Mock()]
        mock_sentiment.choices[0].message.content = "neutral"

        mock_feedback = Mock()
        mock_feedback.choices = [Mock()]
        mock_feedback.choices[0].message.content = "Keep learning!"

        mock_client.chat.completions.create.side_effect = [mock_sentiment, mock_feedback]

        from feedback_agent import create_feedback_graph

        feedback_graph = create_feedback_graph()
        result = feedback_graph.invoke({
            "user_input": "Just started learning"
        })

        assert "sentiment" in result
        assert "feedback" in result


@pytest.mark.unit
class TestAgentErrorHandling:
    """Test error handling across agents"""

    @patch("content_graph.client")
    def test_content_agent_handles_json_error(self, mock_client):
        """Test content agent handles invalid JSON gracefully"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_client.chat.completions.create.return_value = mock_response

        from content_graph import create_content_graph

        content_graph = create_content_graph()
        result = content_graph.invoke({
            "topic": "Test Topic",
            "skill_level": "beginner"
        })

        # Should return error content, not crash
        assert "content" in result

    @patch("quiz_generator_agent.client")
    def test_quiz_agent_handles_json_error(self, mock_client):
        """Test quiz agent handles invalid JSON gracefully"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Not valid JSON"
        mock_client.chat.completions.create.return_value = mock_response

        from quiz_generator_agent import create_quiz_generator_graph

        quiz_graph = create_quiz_generator_graph()
        result = quiz_graph.invoke({
            "topic": "Test",
            "user_id": "test",
            "skill_level": "beginner",
            "num_questions": 3
        })

        # Should return empty questions, not crash
        assert "questions" in result
        assert result["questions"] == []
