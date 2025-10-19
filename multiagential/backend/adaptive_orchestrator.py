"""
Adaptive Orchestrator - Master Multi-Agent Coordination System

This module orchestrates all adaptive learning agents to create
a cohesive, personalized learning experience. It manages the complex
workflows between Learner Profiler, Journey Architect, Performance Analyzer,
Recommendation Agent, and content delivery agents.

This is the "brain" of the adaptive learning system.
"""

from typing import Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
import json

# Import all agents
from learner_profiler_agent import create_learner_profile
from journey_architect_agent import create_learning_journey, adjust_journey
from performance_analyzer_agent import analyze_performance
from recommendation_agent import generate_recommendations
from content_graph import create_content_graph
# Legacy imports removed: graph.py (deleted), feedback_graph.py (legacy)

# Import database operations
import db_postgres as db


# =========================
# ORCHESTRATION WORKFLOWS
# =========================

class OnboardingState(TypedDict):
    """State for onboarding orchestration"""
    user_id: str
    onboarding_data: Dict
    learner_profile: Optional[Dict]
    learning_journey: Optional[List[Dict]]
    status: str
    agent_log: List[Dict]


class ContentDeliveryState(TypedDict):
    """State for content delivery orchestration"""
    user_id: str
    topic: str
    user_mastery: Optional[Dict]
    recommended_difficulty: str
    content: Dict
    agent_log: List[Dict]


# QuizFlowState removed - legacy quiz orchestration deleted


# =========================
# ONBOARDING ORCHESTRATION
# =========================

def onboarding_profiler_node(state: OnboardingState) -> OnboardingState:
    """
    Step 1: Create learner profile from onboarding data
    Uses Learner Profiler Agent
    """
    user_id = state["user_id"]
    onboarding_data = state["onboarding_data"]

    print(f"🤖 [Learner Profiler Agent] Analyzing onboarding data for user {user_id}...")

    # Ensure user exists in database first (required for foreign key)
    if not db.get_user(user_id):
        db.create_user(user_id)

    # Run Learner Profiler Agent
    profile_result = create_learner_profile(onboarding_data)

    # Save to database
    db.create_user_profile(user_id, {
        "interests": onboarding_data.get("interests", []),
        "skill_level": profile_result["learner_profile"].get("overall_skill_level", "beginner"),
        "learning_goals": onboarding_data.get("learning_goals", []),
        "time_commitment": onboarding_data.get("time_commitment", 5),
        "learning_style": onboarding_data.get("learning_style", "mixed")
    })

    # Log agent decision
    db.log_agent_decision(
        user_id=user_id,
        agent_name="learner_profiler",
        decision_type="profile_created",
        input_data=onboarding_data,
        output_data=profile_result["learner_profile"],
        reasoning=profile_result["reasoning"],
        confidence=profile_result["confidence"]
    )

    agent_log = state.get("agent_log", [])
    agent_log.append({
        "agent": "Learner Profiler",
        "action": "Created comprehensive learner profile",
        "confidence": f"{profile_result['confidence']:.0%}"
    })

    return {
        "learner_profile": profile_result["learner_profile"],
        "agent_log": agent_log,
        "status": "profile_created"
    }


def onboarding_journey_node(state: OnboardingState) -> OnboardingState:
    """
    Step 2: Create personalized learning journey
    Uses Journey Architect Agent
    """
    user_id = state["user_id"]
    learner_profile = state["learner_profile"]

    print(f"🤖 [Journey Architect Agent] Designing learning journey for user {user_id}...")

    # Run Journey Architect Agent
    journey_result = create_learning_journey(learner_profile)

    # Save to database
    db.create_learning_journey(user_id, journey_result["learning_journey"])

    # Log agent decision
    db.log_agent_decision(
        user_id=user_id,
        agent_name="journey_architect",
        decision_type="journey_created",
        input_data={"profile": learner_profile},
        output_data={"journey_length": len(journey_result["learning_journey"])},
        reasoning=journey_result["reasoning"]
    )

    agent_log = state.get("agent_log", [])
    agent_log.append({
        "agent": "Journey Architect",
        "action": f"Designed {len(journey_result['learning_journey'])} topic learning path",
        "reasoning": journey_result["reasoning"][:100] + "..."
    })

    return {
        "learning_journey": journey_result["learning_journey"],
        "agent_log": agent_log,
        "status": "journey_created"
    }


def create_onboarding_orchestrator():
    """
    Creates the onboarding orchestration graph

    Workflow: Onboarding Data → Learner Profiler → Journey Architect
    """
    workflow = StateGraph(OnboardingState)

    workflow.add_node("profiler", onboarding_profiler_node)
    workflow.add_node("journey_architect", onboarding_journey_node)

    workflow.set_entry_point("profiler")
    workflow.add_edge("profiler", "journey_architect")
    workflow.add_edge("journey_architect", END)

    return workflow.compile()


# =========================
# CONTENT DELIVERY ORCHESTRATION
# =========================

def content_performance_check_node(state: ContentDeliveryState) -> ContentDeliveryState:
    """
    Step 1: Check user's mastery level for topic
    Uses Performance Analyzer Agent
    """
    user_id = state["user_id"]
    topic = state["topic"]

    print(f"🤖 [Performance Analyzer Agent] Checking mastery for topic '{topic}'...")

    # Get user's mastery for this topic
    mastery = db.get_topic_mastery(user_id, topic)

    if mastery:
        # Use existing mastery to recommend difficulty
        if mastery["mastery_score"] >= 80:
            difficulty = "hard"
        elif mastery["mastery_score"] >= 50:
            difficulty = "medium"
        else:
            difficulty = "easy"
    else:
        # New topic - use user profile
        profile = db.get_user_profile(user_id)
        if profile:
            skill_level = profile.get("skill_level", "beginner")
            difficulty = "easy" if skill_level == "beginner" else "medium"
        else:
            difficulty = "easy"

    agent_log = state.get("agent_log", [])
    agent_log.append({
        "agent": "Performance Analyzer",
        "action": f"Recommended '{difficulty}' difficulty",
        "mastery": mastery["mastery_score"] if mastery else "No data"
    })

    return {
        "user_mastery": mastery,
        "recommended_difficulty": difficulty,
        "agent_log": agent_log
    }


def content_generation_node(state: ContentDeliveryState) -> ContentDeliveryState:
    """
    Step 2: Generate personalized content
    Uses Content Personalizer Agent
    """
    topic = state["topic"]
    difficulty = state["recommended_difficulty"]

    print(f"🤖 [Content Personalizer Agent] Generating {difficulty} content for '{topic}'...")

    # Run content graph
    content_graph = create_content_graph()
    result = content_graph.invoke({
        "topic": topic,
        "difficulty": difficulty  # Pass difficulty to content generator
    })

    agent_log = state.get("agent_log", [])
    agent_log.append({
        "agent": "Content Personalizer",
        "action": f"Generated {difficulty}-level content",
        "exercises": len(result.get("exercises", []))
    })

    agent_log.append({
        "agent": "Diagram Generator",
        "action": "Created visual diagram",
        "diagram_type": "Mermaid flowchart"
    })

    return {
        "content": result,
        "agent_log": agent_log
    }


def create_content_delivery_orchestrator():
    """
    Creates the content delivery orchestration graph

    Workflow: Request → Performance Check → Content Generation
    """
    workflow = StateGraph(ContentDeliveryState)

    workflow.add_node("performance_check", content_performance_check_node)
    workflow.add_node("content_generation", content_generation_node)

    workflow.set_entry_point("performance_check")
    workflow.add_edge("performance_check", "content_generation")
    workflow.add_edge("content_generation", END)

    return workflow.compile()


# =========================
# QUIZ FLOW ORCHESTRATION - DELETED (LEGACY)
# =========================
# Quiz flow orchestration removed - was not used by any endpoint
# New adaptive quiz system will be created in Day 3-4 of consolidation


# =========================
# CONVENIENCE FUNCTIONS
# =========================

def orchestrate_onboarding(user_id: str, onboarding_data: Dict) -> Dict:
    """
    Orchestrates the complete onboarding workflow

    Returns profile, journey, and agent activity log
    """
    orchestrator = create_onboarding_orchestrator()

    result = orchestrator.invoke({
        "user_id": user_id,
        "onboarding_data": onboarding_data,
        "agent_log": []
    })

    return {
        "learner_profile": result["learner_profile"],
        "learning_journey": result["learning_journey"],
        "agent_activity": result["agent_log"],
        "status": result["status"]
    }


def orchestrate_content_delivery(user_id: str, topic: str) -> Dict:
    """
    Orchestrates adaptive content delivery

    Returns personalized content and agent activity log
    """
    orchestrator = create_content_delivery_orchestrator()

    result = orchestrator.invoke({
        "user_id": user_id,
        "topic": topic,
        "agent_log": []
    })

    return {
        "content": result["content"],
        "difficulty": result["recommended_difficulty"],
        "mastery": result.get("user_mastery"),
        "agent_activity": result["agent_log"]
    }


# orchestrate_quiz_flow() removed - legacy function not used by any endpoint


# =========================
# TESTING
# =========================

if __name__ == "__main__":
    print("🚀 Testing Adaptive Orchestrator\n")

    # Test onboarding
    print("=" * 50)
    print("TEST 1: Onboarding Orchestration")
    print("=" * 50)

    test_onboarding = {
        "interests": ["Python Programming", "Data Science"],
        "learning_goals": ["career_change"],
        "time_commitment": 10,
        "learning_style": "interactive",
        "skill_level": "beginner"
    }

    # Note: This requires database to be initialized
    # result = orchestrate_onboarding("test_user_123", test_onboarding)
    # print(json.dumps(result["agent_activity"], indent=2))

    print("\n✅ Orchestrator ready!")
    print("   - Onboarding: Learner Profiler → Journey Architect")
    print("   - Content: Performance Check → Content Generation")
    print("   - Quiz Flow: Quiz → Analysis → Recommendations → Journey Adjust → Motivation")
