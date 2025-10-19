"""
Performance Analyzer Agent - Multi-Agent Adaptive Learning System

This agent analyzes quiz performance, engagement metrics, and learning patterns
to calculate mastery scores and recommend adaptations.

Role: Data analyst that informs Quiz Generator, Content Personalizer, and Journey Architect
Tools: Statistical analysis, pattern detection, mastery calculation
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional
from openai import OpenAI
import os
import json
from datetime import datetime

# --- State ---
class PerformanceAnalysisState(TypedDict):
    """State for performance analysis workflow"""
    # Inputs
    user_id: str
    quiz_history: List[Dict]  # Recent quiz attempts
    topic_mastery: Dict  # Current mastery scores
    engagement_data: Optional[Dict]  # Time spent, interactions

    # Intermediate
    score_trends: Dict  # Statistical trends
    knowledge_gaps: List[str]  # Topics user struggles with
    strengths: List[str]  # Topics user excels at
    learning_velocity: float  # How fast user is learning

    # Outputs
    mastery_updates: Dict  # Updated mastery scores
    difficulty_recommendations: Dict  # Suggested difficulty per topic
    path_adjustments: Dict  # Recommendations for Journey Architect
    performance_summary: str  # Human-readable analysis
    confidence: float  # Confidence in analysis


# --- LLM Client ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

# List of models to try with fallback
LLM_MODELS = [
    "openai/gpt-oss-120b",
    "nousresearch/deephermes-3-mistral-24b-preview",
    "google/gemini-2.5-flash-lite"
]

def invoke_llm_for_performance(system_prompt: str, user_prompt: str, user_id: str, max_retries: int = 3):
    """
    Invokes a language model with retry and fallback logic for performance analysis.
    """
    for model in LLM_MODELS:
        last_error = None
        current_prompt = user_prompt

        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}/{max_retries} with model {model} for performance analysis...")
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": current_prompt},
                    ],
                )
                response_content = completion.choices[0].message.content

                if not response_content:
                    print(f"Empty response from {model}")
                    last_error = "Empty response"
                    continue

                # Try to extract JSON
                if "```json" in response_content:
                    response_content = response_content.split("```json")[1].split("```")[0].strip()
                elif "```" in response_content:
                    response_content = response_content.split("```")[1].split("```")[0].strip()

                # Try to parse the JSON
                analysis = json.loads(response_content)

                # Validate structure
                if "knowledge_gaps" in analysis or "strengths" in analysis:
                    print(f"Successfully analyzed performance with {model}")
                    return analysis
                else:
                    last_error = "Invalid JSON structure"
                    current_prompt = f"""Your previous response had an invalid structure.
                                    Original prompt: {user_prompt}
                                    Invalid response: {response_content[:500]}
                                    Please return valid JSON with 'knowledge_gaps' and 'strengths' arrays."""

            except json.JSONDecodeError as je:
                print(f"JSON DECODE ERROR with {model}: {je}")
                print(f"Raw response: {response_content[:500] if response_content else 'Empty'}")
                last_error = je
                current_prompt = f"""Your previous response was not valid JSON. Please fix it.
                                Original prompt: {user_prompt}
                                Error: {je}
                                Please return ONLY valid JSON."""

            except Exception as e:
                print(f"ERROR with {model}: {e}")
                last_error = e

        print(f"Failed with model {model} after {max_retries} attempts.")

    # If all models fail, return fallback
    print(f"All models failed. Returning fallback analysis. Last error: {last_error}")
    return {
        "knowledge_gaps": [],
        "strengths": [],
        "patterns": [],
        "reasoning": "Fallback analysis - unable to generate detailed insights"
    }


# --- Agents/Nodes ---

def statistical_analyzer_node(state: PerformanceAnalysisState) -> PerformanceAnalysisState:
    """
    Analyzes quiz history statistically to identify trends

    Calculates metrics like average score, improvement rate, consistency, etc.
    """
    quiz_history = state["quiz_history"]

    if not quiz_history:
        return {
            "score_trends": {},
            "learning_velocity": 0.0
        }

    # Calculate per-topic trends
    topic_scores = {}
    for quiz in quiz_history:
        topic = quiz["topic"]
        if topic not in topic_scores:
            topic_scores[topic] = []

        percentage = quiz.get("percentage", 0)
        topic_scores[topic].append({
            "score": percentage,
            "date": quiz["completed_at"]
        })

    # Analyze trends
    trends = {}
    overall_velocity = []

    for topic, scores in topic_scores.items():
        if len(scores) < 2:
            trend = "insufficient_data"
            velocity = 0.0
        else:
            # Simple trend: compare first half to second half
            mid = len(scores) // 2
            first_half_avg = sum(s["score"] for s in scores[:mid]) / mid
            second_half_avg = sum(s["score"] for s in scores[mid:]) / (len(scores) - mid)

            improvement = second_half_avg - first_half_avg

            if improvement > 10:
                trend = "improving"
            elif improvement < -10:
                trend = "declining"
            else:
                trend = "stable"

            velocity = improvement / len(scores)  # Rate of improvement
            overall_velocity.append(velocity)

        trends[topic] = {
            "trend": trend,
            "recent_avg": sum(s["score"] for s in scores[-3:]) / min(3, len(scores)),
            "total_attempts": len(scores),
            "velocity": velocity
        }

    # Overall learning velocity
    avg_velocity = sum(overall_velocity) / len(overall_velocity) if overall_velocity else 0.0

    return {
        "score_trends": trends,
        "learning_velocity": avg_velocity
    }


def knowledge_gap_identifier_node(state: PerformanceAnalysisState) -> PerformanceAnalysisState:
    """
    Identifies knowledge gaps and strengths using LLM reasoning

    Goes beyond simple scores to understand WHY user struggles or excels.
    """
    quiz_history = state["quiz_history"]
    score_trends = state["score_trends"]
    topic_mastery = state["topic_mastery"]
    user_id = state["user_id"]

    system_prompt = "You are an expert educational psychologist analyzing learning performance."

    user_prompt = f"""
    Analyze learning performance to identify knowledge gaps and strengths.

    Quiz History Summary:
    {json.dumps([{
        "topic": q["topic"],
        "score": f"{q['score']}/{q['total_questions']}",
        "percentage": q.get("percentage", 0),
        "difficulty": q.get("difficulty", "unknown")
    } for q in quiz_history[-10:]], indent=2)}

    Score Trends: {json.dumps(score_trends, indent=2)}
    Current Mastery: {json.dumps(topic_mastery, indent=2)}

    Identify:
    1. Knowledge gaps (topics/concepts where learner struggles)
    2. Strengths (topics where learner excels)
    3. Patterns (e.g., struggles with advanced but good at basics)
    4. Recommended actions for each gap

    Return JSON:
    {{
        "knowledge_gaps": [
            {{
                "topic": "...",
                "severity": "high|medium|low",
                "indicators": ["indicator1", "indicator2"],
                "recommended_action": "..."
            }}
        ],
        "strengths": [
            {{
                "topic": "...",
                "mastery_level": 0-100,
                "evidence": "..."
            }}
        ],
        "patterns": ["pattern1", "pattern2"],
        "reasoning": "..."
    }}
    """

    print(f"🤖 Analyzing performance for user {user_id} with retry logic...")

    # Use retry logic with multiple models
    analysis = invoke_llm_for_performance(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        user_id=user_id
    )

    # Extract lists
    gaps = [g["topic"] if isinstance(g, dict) else g for g in analysis.get("knowledge_gaps", [])]
    strengths = [s["topic"] if isinstance(s, dict) else s for s in analysis.get("strengths", [])]

    return {
        "knowledge_gaps": gaps,
        "strengths": strengths
    }


def mastery_calculator_node(state: PerformanceAnalysisState) -> PerformanceAnalysisState:
    """
    Calculates updated mastery scores for each topic

    Uses sophisticated algorithm considering:
    - Recent performance
    - Historical trends
    - Time decay
    - Difficulty level
    """
    quiz_history = state["quiz_history"]
    current_mastery = state["topic_mastery"]
    score_trends = state["score_trends"]

    updated_mastery = {}

    # Group quizzes by topic
    topic_quizzes = {}
    for quiz in quiz_history:
        topic = quiz["topic"]
        if topic not in topic_quizzes:
            topic_quizzes[topic] = []
        topic_quizzes[topic].append(quiz)

    # Calculate mastery for each topic
    for topic, quizzes in topic_quizzes.items():
        # Get most recent quizzes (last 5)
        recent_quizzes = sorted(quizzes, key=lambda x: x["completed_at"], reverse=True)[:5]

        # Calculate weighted average (more weight to recent)
        weights = [2**i for i in range(len(recent_quizzes))][::-1]  # [1, 2, 4, 8, 16]
        total_weight = sum(weights)

        weighted_score = sum(
            q.get("percentage", 0) * w
            for q, w in zip(recent_quizzes, weights)
        ) / total_weight if total_weight > 0 else 0

        # Adjust for difficulty
        difficulty_bonus = {
            "easy": -10,  # Penalize if only doing easy
            "medium": 0,
            "hard": +10   # Bonus for handling hard questions
        }

        avg_difficulty = recent_quizzes[0].get("difficulty", "medium") if recent_quizzes else "medium"
        adjusted_score = weighted_score + difficulty_bonus.get(avg_difficulty, 0)

        # Cap at 100
        mastery_score = min(100, max(0, adjusted_score))

        # Determine skill level
        if mastery_score >= 80:
            skill_level = "advanced"
        elif mastery_score >= 50:
            skill_level = "intermediate"
        else:
            skill_level = "beginner"

        updated_mastery[topic] = {
            "mastery_score": round(mastery_score, 2),
            "skill_level": skill_level,
            "trend": score_trends.get(topic, {}).get("trend", "unknown"),
            "attempts": len(quizzes),
            "confidence": min(100, len(quizzes) * 20)  # More attempts = higher confidence
        }

    return {"mastery_updates": updated_mastery}


def adaptation_recommender_node(state: PerformanceAnalysisState) -> PerformanceAnalysisState:
    """
    Generates recommendations for other agents

    Recommends:
    - Difficulty levels for Quiz Generator
    - Content complexity for Content Personalizer
    - Path adjustments for Journey Architect
    """
    mastery_updates = state["mastery_updates"]
    knowledge_gaps = state["knowledge_gaps"]
    strengths = state["strengths"]
    learning_velocity = state["learning_velocity"]

    # Difficulty recommendations (for Quiz Generator)
    difficulty_recs = {}
    for topic, mastery in mastery_updates.items():
        score = mastery["mastery_score"]
        trend = mastery["trend"]

        if score >= 80 and trend != "declining":
            difficulty_recs[topic] = "hard"
        elif score >= 60:
            difficulty_recs[topic] = "medium"
        elif score < 40 or trend == "declining":
            difficulty_recs[topic] = "easy"
        else:
            difficulty_recs[topic] = "medium"

    # Path adjustments (for Journey Architect)
    path_adjustments = {
        "skip_topics": [],  # Topics to fast-track
        "review_topics": [],  # Topics to review
        "add_topics": [],  # Topics to add for gaps
        "reasoning": ""
    }

    # Identify topics to skip (mastery > 85, improving trend)
    for topic, mastery in mastery_updates.items():
        if mastery["mastery_score"] > 85 and mastery["trend"] == "improving":
            path_adjustments["skip_topics"].append(topic)

    # Topics to review (in knowledge gaps)
    path_adjustments["review_topics"] = knowledge_gaps

    # Generate reasoning
    path_adjustments["reasoning"] = f"""
Performance analysis complete.

Strong areas ({len(strengths)}): {', '.join(strengths[:3])}
Weak areas ({len(knowledge_gaps)}): {', '.join(knowledge_gaps[:3])}
Learning velocity: {learning_velocity:.2f}

Recommendations:
- Fast-track {len(path_adjustments['skip_topics'])} mastered topics
- Add review for {len(knowledge_gaps)} struggling topics
- Maintain current difficulty for stable topics
    """.strip()

    return {
        "difficulty_recommendations": difficulty_recs,
        "path_adjustments": path_adjustments
    }


def summary_generator_node(state: PerformanceAnalysisState) -> PerformanceAnalysisState:
    """
    Generates human-readable performance summary

    Creates a summary for display to the user and other agents.
    """
    mastery_updates = state["mastery_updates"]
    knowledge_gaps = state["knowledge_gaps"]
    strengths = state["strengths"]
    learning_velocity = state["learning_velocity"]

    # Calculate overall mastery
    if mastery_updates:
        overall_mastery = sum(m["mastery_score"] for m in mastery_updates.values()) / len(mastery_updates)
    else:
        overall_mastery = 0

    summary = f"""
📊 Performance Analysis Summary

Overall Mastery: {overall_mastery:.1f}%
Learning Velocity: {"Fast" if learning_velocity > 5 else "Moderate" if learning_velocity > 0 else "Needs attention"}

🌟 Strengths ({len(strengths)} topics):
{', '.join(strengths[:5]) if strengths else "Complete more quizzes to identify strengths"}

🎯 Areas for Improvement ({len(knowledge_gaps)} topics):
{', '.join(knowledge_gaps[:5]) if knowledge_gaps else "No significant gaps identified"}

📈 Topic Mastery:
{chr(10).join(f"- {topic}: {data['mastery_score']:.0f}% ({data['skill_level'].title()}, {data['trend'].title()})" for topic, data in list(mastery_updates.items())[:5])}

Recommendation: {"Keep up the great work!" if overall_mastery >= 70 else "Focus on review and practice" if overall_mastery >= 50 else "Consider revisiting foundational topics"}
    """.strip()

    # Confidence based on amount of data
    total_attempts = sum(m["attempts"] for m in mastery_updates.values()) if mastery_updates else 0
    confidence = min(1.0, total_attempts / 20)  # Full confidence after 20 quizzes

    return {
        "performance_summary": summary,
        "confidence": confidence
    }


# --- Graph Creation ---

def create_performance_analyzer_graph():
    """
    Creates the Performance Analyzer agent graph

    Workflow:
    1. Statistical analysis (trends, velocity)
    2. Knowledge gap identification (what's missing)
    3. Mastery calculation (updated scores)
    4. Adaptation recommendations (for other agents)
    5. Summary generation (human-readable output)
    """
    workflow = StateGraph(PerformanceAnalysisState)

    # Add nodes
    workflow.add_node("statistical_analyzer", statistical_analyzer_node)
    workflow.add_node("knowledge_gap_identifier", knowledge_gap_identifier_node)
    workflow.add_node("mastery_calculator", mastery_calculator_node)
    workflow.add_node("adaptation_recommender", adaptation_recommender_node)
    workflow.add_node("summary_generator", summary_generator_node)

    # Define flow
    workflow.set_entry_point("statistical_analyzer")
    workflow.add_edge("statistical_analyzer", "knowledge_gap_identifier")
    workflow.add_edge("knowledge_gap_identifier", "mastery_calculator")
    workflow.add_edge("mastery_calculator", "adaptation_recommender")
    workflow.add_edge("adaptation_recommender", "summary_generator")
    workflow.add_edge("summary_generator", END)

    return workflow.compile()


# --- Convenience Functions ---

def analyze_performance(user_id: str, quiz_history: List[Dict],
                       topic_mastery: Dict, engagement_data: Optional[Dict] = None) -> Dict:
    """
    Main function to analyze user performance

    Args:
        user_id: User identifier
        quiz_history: List of quiz attempts
        topic_mastery: Current mastery scores
        engagement_data: Optional engagement metrics

    Returns:
        Dict with mastery_updates, recommendations, summary, confidence
    """
    graph = create_performance_analyzer_graph()

    initial_state = {
        "user_id": user_id,
        "quiz_history": quiz_history,
        "topic_mastery": topic_mastery,
        "engagement_data": engagement_data
    }

    result = graph.invoke(initial_state)

    return {
        "mastery_updates": result["mastery_updates"],
        "difficulty_recommendations": result["difficulty_recommendations"],
        "path_adjustments": result["path_adjustments"],
        "knowledge_gaps": result["knowledge_gaps"],
        "strengths": result["strengths"],
        "performance_summary": result["performance_summary"],
        "confidence": result["confidence"]
    }


# --- Testing ---
if __name__ == "__main__":
    # Test the performance analyzer
    test_quiz_history = [
        {
            "topic": "Python Basics",
            "score": 8,
            "total_questions": 10,
            "percentage": 80,
            "difficulty": "medium",
            "completed_at": "2024-01-01T10:00:00"
        },
        {
            "topic": "Python Basics",
            "score": 9,
            "total_questions": 10,
            "percentage": 90,
            "difficulty": "medium",
            "completed_at": "2024-01-02T10:00:00"
        },
        {
            "topic": "Data Structures",
            "score": 5,
            "total_questions": 10,
            "percentage": 50,
            "difficulty": "hard",
            "completed_at": "2024-01-03T10:00:00"
        }
    ]

    test_mastery = {
        "Python Basics": {"mastery_score": 75, "attempts": 5},
        "Data Structures": {"mastery_score": 45, "attempts": 2}
    }

    result = analyze_performance("test_user", test_quiz_history, test_mastery)
    print(json.dumps(result, indent=2))
    print("\n" + result["performance_summary"])
