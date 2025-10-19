"""
Recommendation Agent - Multi-Agent Adaptive Learning System

This agent generates intelligent topic recommendations based on performance,
interests, and learning journey progress. It coordinates with Performance Analyzer
and Journey Architect to suggest optimal next steps.

Role: Recommendation engine coordinating multiple data sources
Tools: Recommendation algorithms, collaborative filtering concepts, DuckDuckGo
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional
from openai import OpenAI
import os
import json
from tools.duckduckgo_tool import get_related_learning_topics

# --- State ---
class RecommendationState(TypedDict):
    """State for recommendation generation workflow"""
    # Inputs
    user_id: str
    learner_profile: Dict  # From Learner Profiler
    performance_analysis: Dict  # From Performance Analyzer
    learning_journey: List[Dict]  # From Journey Architect
    current_topic: Optional[str]  # What user just completed

    # Intermediate
    candidate_topics: List[Dict]  # Potential recommendations
    relevance_scores: Dict  # Scored candidates
    context_analysis: Dict  # Learning context

    # Outputs
    recommendations: List[Dict]  # Top recommendations
    reasoning: str  # Why these recommendations
    confidence: float  # Confidence in recommendations


# --- LLM Client ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


# --- Agents/Nodes ---

def candidate_generator_node(state: RecommendationState) -> RecommendationState:
    """
    Generates candidate topics for recommendation

    Sources:
    1. Next topics in learning journey
    2. Related topics from DuckDuckGo
    3. Review topics based on weak areas
    4. Challenge topics based on strengths
    """
    journey = state["learning_journey"]
    performance = state["performance_analysis"]
    profile = state["learner_profile"]
    current_topic = state.get("current_topic")

    candidates = []

    # 1. Journey progression (next unlocked topics)
    for topic_item in journey:
        if topic_item["status"] in ["available", "recommended"]:
            candidates.append({
                "topic": topic_item["topic"],
                "source": "journey_progression",
                "position": topic_item["position"],
                "estimated_hours": topic_item.get("estimated_hours", 10),
                "reasoning": topic_item.get("reasoning", "")
            })

    # 2. Review topics (knowledge gaps)
    gaps = performance.get("knowledge_gaps", [])
    for gap in gaps[:3]:
        candidates.append({
            "topic": f"Review: {gap}",
            "source": "knowledge_gap_review",
            "priority": "high",
            "reasoning": f"Addressing identified knowledge gap in {gap}"
        })

    # 3. Challenge topics (based on strengths)
    strengths = performance.get("strengths", [])
    for strength in strengths[:2]:
        # Get related advanced topics
        related = get_related_learning_topics(strength)
        for rel in related[:2]:
            candidates.append({
                "topic": rel,
                "source": "strength_extension",
                "base_topic": strength,
                "reasoning": f"Advanced topic building on strength in {strength}"
            })

    # 4. Interest-based exploration
    interests = profile.get("interests_detail", {})
    for interest_name in list(interests.keys())[:2]:
        related = get_related_learning_topics(interest_name)
        for rel in related[:2]:
            if not any(c["topic"] == rel for c in candidates):
                candidates.append({
                    "topic": rel,
                    "source": "interest_exploration",
                    "interest_area": interest_name,
                    "reasoning": f"Exploring related topic in {interest_name}"
                })

    return {"candidate_topics": candidates}


def relevance_scorer_node(state: RecommendationState) -> RecommendationState:
    """
    Scores each candidate based on multiple factors using LLM reasoning

    Factors:
    - Alignment with learning goals
    - Prerequisite completion
    - Current skill level appropriateness
    - Diversity (not all from same area)
    - Timing (based on journey progression)
    """
    candidates = state["candidate_topics"]
    profile = state["learner_profile"]
    performance = state["performance_analysis"]
    current_topic = state.get("current_topic")

    prompt = f"""
    Score these learning topic recommendations for relevance and appropriateness.

    User Profile:
    - Goals: {profile.get("learning_goals", [])}
    - Skill Level: {profile.get("overall_skill_level", "beginner")}
    - Interests: {list(profile.get("interests_detail", {}).keys())}
    - Learning Pace: {profile.get("learning_pace", "moderate")}

    Current Context:
    - Just completed: {current_topic if current_topic else "Nothing recent"}
    - Strengths: {performance.get("strengths", [])}
    - Weak areas: {performance.get("knowledge_gaps", [])}

    Candidate Topics:
    {json.dumps([{
        "topic": c["topic"],
        "source": c["source"],
        "reasoning": c.get("reasoning", "")
    } for c in candidates], indent=2)}

    For each topic, provide:
    1. Relevance score (0-100)
    2. Timing score (is now the right time?) (0-100)
    3. Engagement potential (0-100)
    4. Overall priority (high/medium/low)
    5. Brief reasoning

    Return JSON:
    {{
        "topic_name": {{
            "relevance_score": 0-100,
            "timing_score": 0-100,
            "engagement_score": 0-100,
            "priority": "high|medium|low",
            "reasoning": "..."
        }}
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert recommendation system for personalized education."
                },
                {"role": "user", "content": prompt}
            ],
        )

        response = completion.choices[0].message.content

        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            scores = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: give equal moderate scores
            scores = {
                c["topic"]: {
                    "relevance_score": 70,
                    "timing_score": 70,
                    "engagement_score": 70,
                    "priority": "medium",
                    "reasoning": "Default scoring"
                }
                for c in candidates
            }

        return {"relevance_scores": scores}

    except Exception as e:
        print(f"Error scoring candidates: {e}")
        return {
            "relevance_scores": {
                c["topic"]: {
                    "relevance_score": 60,
                    "timing_score": 60,
                    "engagement_score": 60,
                    "priority": "medium",
                    "reasoning": "Fallback"
                }
                for c in candidates
            }
        }


def recommendation_selector_node(state: RecommendationState) -> RecommendationState:
    """
    Selects top recommendations ensuring diversity and balance

    Ensures:
    - Mix of progression, review, and exploration
    - Not all from same source
    - Appropriate difficulty spread
    - Engaging variety
    """
    candidates = state["candidate_topics"]
    scores = state["relevance_scores"]

    # Calculate composite score for each candidate
    scored_candidates = []
    for candidate in candidates:
        topic = candidate["topic"]
        score_data = scores.get(topic, {
            "relevance_score": 50,
            "timing_score": 50,
            "engagement_score": 50,
            "priority": "medium"
        })

        # Weighted composite score
        composite = (
            score_data.get("relevance_score", 50) * 0.4 +
            score_data.get("timing_score", 50) * 0.3 +
            score_data.get("engagement_score", 50) * 0.3
        )

        # Priority boost
        if score_data.get("priority") == "high":
            composite += 15
        elif score_data.get("priority") == "low":
            composite -= 10

        scored_candidates.append({
            **candidate,
            "composite_score": composite,
            "score_breakdown": score_data
        })

    # Sort by composite score
    scored_candidates.sort(key=lambda x: x["composite_score"], reverse=True)

    # Select top recommendations with diversity
    selected = []
    sources_used = []  # Use list to track source counts
    max_per_source = 2

    for candidate in scored_candidates:
        source = candidate["source"]

        # Ensure diversity
        if sources_used.count(source) >= max_per_source:
            continue

        selected.append(candidate)
        sources_used.append(source)  # Use append for list

        if len(selected) >= 5:  # Top 5 recommendations
            break

    # If we don't have enough, fill with highest scoring remaining
    if len(selected) < 3:
        for candidate in scored_candidates:
            if candidate not in selected:
                selected.append(candidate)
                if len(selected) >= 3:
                    break

    return {"recommendations": selected}


def reasoning_generator_node(state: RecommendationState) -> RecommendationState:
    """
    Generates human-readable reasoning for recommendations

    Explains why these topics were chosen and what user will gain.
    """
    recommendations = state["recommendations"]
    profile = state["learner_profile"]
    performance = state["performance_analysis"]

    if not recommendations:
        return {
            "reasoning": "No recommendations available. Please complete more quizzes for personalized suggestions.",
            "confidence": 0.0
        }

    prompt = f"""
    Create engaging explanations for these learning recommendations.

    User Context:
    - Profile: {profile.get("profile_summary", "New learner")}
    - Recent performance: {performance.get("performance_summary", "No data yet")}

    Recommendations:
    {json.dumps([{
        "topic": r["topic"],
        "source": r["source"],
        "score": r.get("composite_score", 0),
        "reasoning": r.get("score_breakdown", {}).get("reasoning", "")
    } for r in recommendations], indent=2)}

    Create:
    1. Brief introduction (why these recommendations make sense)
    2. For each topic, a compelling one-sentence pitch
    3. Overall learning strategy suggestion

    Return JSON:
    {{
        "introduction": "...",
        "topic_pitches": {{
            "topic_name": "compelling pitch",
            ...
        }},
        "strategy_suggestion": "...",
        "confidence_note": "..."
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an enthusiastic learning advisor creating motivating recommendations."
                },
                {"role": "user", "content": prompt}
            ],
        )

        response = completion.choices[0].message.content

        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            reasoning_data = json.loads(response)

            reasoning = f"""
{reasoning_data.get("introduction", "Here are your personalized recommendations:")}

{chr(10).join(f"📚 {rec['topic']}: {reasoning_data.get('topic_pitches', {}).get(rec['topic'], 'Recommended for you')}" for rec in recommendations[:5])}

💡 {reasoning_data.get("strategy_suggestion", "Work through these topics at your own pace.")}
            """.strip()

        except json.JSONDecodeError:
            reasoning = f"""
Based on your learning profile and performance, here are your personalized recommendations:

{chr(10).join(f"📚 {rec['topic']} - {rec.get('reasoning', 'Recommended based on your progress')}" for rec in recommendations[:5])}

These topics are selected to match your skill level and learning goals.
            """.strip()

        # Confidence based on data quality
        data_points = len(performance.get("knowledge_gaps", [])) + len(performance.get("strengths", []))
        confidence = min(1.0, data_points / 10)  # Full confidence with 10+ data points

        return {
            "reasoning": reasoning,
            "confidence": confidence
        }

    except Exception as e:
        print(f"Error generating reasoning: {e}")
        return {
            "reasoning": "Recommendations generated based on your profile.",
            "confidence": 0.5
        }


# --- Graph Creation ---

def create_recommendation_graph():
    """
    Creates the Recommendation Agent graph

    Workflow:
    1. Generate candidates (from multiple sources)
    2. Score for relevance (multi-factor)
    3. Select best (with diversity)
    4. Generate reasoning (human-readable)
    """
    workflow = StateGraph(RecommendationState)

    # Add nodes
    workflow.add_node("candidate_generator", candidate_generator_node)
    workflow.add_node("relevance_scorer", relevance_scorer_node)
    workflow.add_node("recommendation_selector", recommendation_selector_node)
    workflow.add_node("reasoning_generator", reasoning_generator_node)

    # Define flow
    workflow.set_entry_point("candidate_generator")
    workflow.add_edge("candidate_generator", "relevance_scorer")
    workflow.add_edge("relevance_scorer", "recommendation_selector")
    workflow.add_edge("recommendation_selector", "reasoning_generator")
    workflow.add_edge("reasoning_generator", END)

    return workflow.compile()


# --- Convenience Functions ---

def generate_recommendations(user_id: str, learner_profile: Dict,
                            performance_analysis: Dict, learning_journey: List[Dict],
                            current_topic: Optional[str] = None) -> Dict:
    """
    Main function to generate topic recommendations

    Args:
        user_id: User identifier
        learner_profile: From Learner Profiler Agent
        performance_analysis: From Performance Analyzer Agent
        learning_journey: From Journey Architect Agent
        current_topic: Optional recently completed topic

    Returns:
        Dict with recommendations, reasoning, confidence
    """
    graph = create_recommendation_graph()

    initial_state = {
        "user_id": user_id,
        "learner_profile": learner_profile,
        "performance_analysis": performance_analysis,
        "learning_journey": learning_journey,
        "current_topic": current_topic
    }

    result = graph.invoke(initial_state)

    return {
        "recommendations": result["recommendations"],
        "reasoning": result["reasoning"],
        "confidence": result["confidence"]
    }


# --- Testing ---
if __name__ == "__main__":
    # Test the recommendation agent
    test_profile = {
        "profile_summary": "Beginner programmer interested in web development",
        "overall_skill_level": "beginner",
        "learning_goals": ["career_change"],
        "learning_pace": "moderate",
        "interests_detail": {
            "Python Programming": {},
            "Web Development": {}
        }
    }

    test_performance = {
        "strengths": ["Python Basics"],
        "knowledge_gaps": ["Data Structures"],
        "performance_summary": "Doing well in basics, needs work on data structures"
    }

    test_journey = [
        {"topic": "Python Variables", "status": "completed", "position": 1},
        {"topic": "Python Functions", "status": "available", "position": 2, "estimated_hours": 8, "reasoning": "Next logical step"},
        {"topic": "Data Structures", "status": "locked", "position": 3},
    ]

    result = generate_recommendations(
        "test_user",
        test_profile,
        test_performance,
        test_journey,
        "Python Variables"
    )

    print(json.dumps([{
        "topic": r["topic"],
        "score": r.get("composite_score"),
        "source": r["source"]
    } for r in result["recommendations"]], indent=2))

    print("\n" + result["reasoning"])
    print(f"\nConfidence: {result['confidence']:.0%}")
