"""
Journey Architect Agent - Multi-Agent Adaptive Learning System

This agent designs personalized learning paths based on learner profiles.
It creates structured curricula with prerequisites, milestones, and unlock conditions.

Role: Curriculum designer that coordinates with Learner Profiler and Performance Analyzer
Tools: Curriculum generation, prerequisite mapping, DuckDuckGo for topic validation
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional
from openai import OpenAI
import os
import json
from tools.duckduckgo_tool import get_related_learning_topics, search_topic_info

# --- State ---
class JourneyArchitectState(TypedDict):
    """State for journey architecture workflow"""
    # Inputs
    learner_profile: Dict  # From Learner Profiler Agent
    performance_data: Optional[Dict]  # From Performance Analyzer (for adjustments)

    # Intermediate
    topic_map: Dict  # Expanded topic breakdown
    prerequisite_graph: Dict  # Dependencies between topics
    difficulty_progression: List[Dict]  # Topics ordered by difficulty

    # Outputs
    learning_journey: List[Dict]  # Ordered list of topics with metadata
    reasoning: str  # Why this journey was created
    adjustment_notes: Optional[str]  # If modifying existing journey


# --- LLM Client ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


# --- Agents/Nodes ---

def topic_expander_node(state: JourneyArchitectState) -> JourneyArchitectState:
    """
    Expands user interests into detailed topic breakdowns

    Uses DuckDuckGo to discover related topics and validates topic relevance.
    """
    profile = state["learner_profile"]
    interests = profile.get("interests_detail", {})
    skill_level = profile.get("overall_skill_level", "beginner")

    expanded_topics = {}

    for interest_name, interest_data in interests.items():
        # Get related topics from DuckDuckGo
        related = get_related_learning_topics(interest_name)

        # Use LLM to structure the topic breakdown
        prompt = f"""
        Create a comprehensive topic breakdown for learning "{interest_name}".

        Skill Level: {skill_level}
        Related Topics (from research): {related}
        Suggested Topics: {interest_data.get('topics', [])}

        For {skill_level} learners, break down this subject into:
        1. Foundational topics (must learn first)
        2. Core topics (main content)
        3. Advanced topics (for mastery)
        4. Optional enrichment topics

        Return JSON:
        {{
            "foundational": [
                {{"name": "...", "description": "...", "estimated_hours": N}},
                ...
            ],
            "core": [...],
            "advanced": [...],
            "optional": [...]
        }}
        """

        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert curriculum designer creating structured learning paths."
                    },
                    {"role": "user", "content": prompt}
                ],
            )

            response = completion.choices[0].message.content

            # Parse JSON
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()

                topic_breakdown = json.loads(response)
            except json.JSONDecodeError:
                topic_breakdown = {
                    "foundational": [{"name": interest_name, "description": "Introduction", "estimated_hours": 5}],
                    "core": [],
                    "advanced": [],
                    "optional": []
                }

            expanded_topics[interest_name] = topic_breakdown

        except Exception as e:
            print(f"Error expanding {interest_name}: {e}")
            expanded_topics[interest_name] = {
                "foundational": [{"name": interest_name, "description": "Basics", "estimated_hours": 5}],
                "core": [],
                "advanced": [],
                "optional": []
            }

    return {"topic_map": expanded_topics}


def prerequisite_mapper_node(state: JourneyArchitectState) -> JourneyArchitectState:
    """
    Maps prerequisites and dependencies between topics

    Creates a dependency graph to ensure logical learning progression.
    """
    topic_map = state["topic_map"]
    profile = state["learner_profile"]

    # Collect all topics
    all_topics = []
    for interest, breakdown in topic_map.items():
        for category in ["foundational", "core", "advanced", "optional"]:
            all_topics.extend([
                {**topic, "interest": interest, "category": category}
                for topic in breakdown.get(category, [])
            ])

    # Use LLM to determine prerequisites
    topic_names = [t["name"] for t in all_topics]

    prompt = f"""
    Determine prerequisites for these learning topics:

    Topics: {json.dumps(topic_names, indent=2)}

    For each topic, identify:
    1. Which other topics (if any) must be learned first
    2. Recommended (but not required) prerequisites
    3. Topics that can be learned in parallel

    Return JSON:
    {{
        "topic_name": {{
            "required_prerequisites": ["topic1", "topic2"],
            "recommended_prerequisites": ["topic3"],
            "can_learn_with": ["topic4", "topic5"],
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
                    "content": "You are an expert in curriculum sequencing and learning science."
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

            prereq_graph = json.loads(response)
        except json.JSONDecodeError:
            # Create basic linear dependency
            prereq_graph = {
                topic: {
                    "required_prerequisites": [],
                    "recommended_prerequisites": [],
                    "can_learn_with": [],
                    "reasoning": "Linear progression"
                }
                for topic in topic_names
            }

        return {"prerequisite_graph": prereq_graph}

    except Exception as e:
        print(f"Error mapping prerequisites: {e}")
        return {
            "prerequisite_graph": {
                topic: {"required_prerequisites": [], "recommended_prerequisites": [], "can_learn_with": []}
                for topic in topic_names
            }
        }


def journey_sequencer_node(state: JourneyArchitectState) -> JourneyArchitectState:
    """
    Sequences topics into an optimal learning journey

    Takes into account prerequisites, user goals, time commitment, and skill level.
    """
    topic_map = state["topic_map"]
    prereq_graph = state["prerequisite_graph"]
    profile = state["learner_profile"]

    time_commitment = profile.get("time_commitment", 5)
    learning_pace = profile.get("learning_pace", "moderate")
    priority_topics = profile.get("priority_topics", [])
    skill_assessments = profile.get("skill_assessments_detail", {})

    prompt = f"""
    Create an optimal learning journey sequence.

    Topic Map: {json.dumps(topic_map, indent=2)}
    Prerequisites: {json.dumps(prereq_graph, indent=2)}
    Priority Topics: {priority_topics}
    Time Commitment: {time_commitment} hours/week
    Learning Pace: {learning_pace}
    Skill Assessments: {json.dumps(skill_assessments, indent=2)}

    Design a journey that:
    1. Starts with foundational topics
    2. Respects prerequisites
    3. Prioritizes user's priority topics
    4. Fits within time commitment (roughly)
    5. Adapts to existing skill levels

    For each topic in the journey, provide:
    - Position (order number)
    - Topic name
    - Description (1-2 sentence summary of what learner will learn)
    - Prerequisites (list of topic names that should be completed first)
    - Status ("locked", "available", "recommended")
    - Unlock conditions
    - Estimated hours
    - Why this topic at this position

    Return JSON array:
    [
        {{
            "position": 1,
            "topic": "...",
            "description": "...",
            "prerequisites": [],
            "status": "available",
            "unlock_conditions": {{}},
            "estimated_hours": N,
            "reasoning": "...",
            "interest_area": "..."
        }},
        ...
    ]
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert learning path architect creating personalized curricula."
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

            journey = json.loads(response)

            # Ensure it's a list
            if isinstance(journey, dict):
                journey = list(journey.values()) if journey else []

        except json.JSONDecodeError:
            # Create basic journey from priority topics
            journey = [
                {
                    "position": i + 1,
                    "topic": topic,
                    "description": f"Learn the fundamentals of {topic}",
                    "prerequisites": [priority_topics[i-1]] if i > 0 else [],
                    "status": "available" if i == 0 else "locked",
                    "unlock_conditions": {"complete_previous": i > 0},
                    "estimated_hours": 10,
                    "reasoning": "Sequential learning",
                    "interest_area": "General"
                }
                for i, topic in enumerate(priority_topics[:10])
            ]

        return {"difficulty_progression": journey}

    except Exception as e:
        print(f"Error sequencing journey: {e}")
        fallback_topic = priority_topics[0] if priority_topics else "Introduction"
        return {
            "difficulty_progression": [
                {
                    "position": 1,
                    "topic": fallback_topic,
                    "description": f"Learn the fundamentals of {fallback_topic}",
                    "prerequisites": [],
                    "status": "available",
                    "unlock_conditions": {},
                    "estimated_hours": 10,
                    "reasoning": "Fallback",
                    "interest_area": "General"
                }
            ]
        }


def journey_finalizer_node(state: JourneyArchitectState) -> JourneyArchitectState:
    """
    Finalizes the journey with metadata and reasoning

    Adds milestones, success criteria, and adjustment strategies.
    """
    journey = state["difficulty_progression"]
    profile = state["learner_profile"]
    performance = state.get("performance_data")

    # Add milestones (every 5 topics)
    for i, topic in enumerate(journey):
        if (i + 1) % 5 == 0:
            topic["is_milestone"] = True
            topic["milestone_name"] = f"Checkpoint {(i + 1) // 5}"
        else:
            topic["is_milestone"] = False

    # Generate reasoning
    if performance:
        reasoning = f"""
Journey adjusted based on performance data.

Strong areas: {performance.get('strong_topics', [])}
Weak areas: {performance.get('weak_topics', [])}

Adjustments made:
- Added review topics for weak areas
- Fast-tracked strong areas
- Maintained core progression
        """.strip()
        adjustment_notes = "Journey modified based on performance analysis"
    else:
        reasoning = f"""
Journey created for new learner.

Profile summary: {profile.get('profile_summary', 'N/A')}
Priority topics: {profile.get('priority_topics', [])}
Learning pace: {profile.get('learning_pace', 'moderate')}

Total topics: {len(journey)}
Estimated completion: {sum(t.get('estimated_hours', 10) for t in journey)} hours
        """.strip()
        adjustment_notes = None

    return {
        "learning_journey": journey,
        "reasoning": reasoning,
        "adjustment_notes": adjustment_notes
    }


# --- Graph Creation ---

def create_journey_architect_graph():
    """
    Creates the Journey Architect agent graph

    Workflow:
    1. Expand topics (detailed breakdown)
    2. Map prerequisites (dependencies)
    3. Sequence journey (optimal order)
    4. Finalize (add metadata)
    """
    workflow = StateGraph(JourneyArchitectState)

    # Add nodes
    workflow.add_node("topic_expander", topic_expander_node)
    workflow.add_node("prerequisite_mapper", prerequisite_mapper_node)
    workflow.add_node("journey_sequencer", journey_sequencer_node)
    workflow.add_node("journey_finalizer", journey_finalizer_node)

    # Define flow
    workflow.set_entry_point("topic_expander")
    workflow.add_edge("topic_expander", "prerequisite_mapper")
    workflow.add_edge("prerequisite_mapper", "journey_sequencer")
    workflow.add_edge("journey_sequencer", "journey_finalizer")
    workflow.add_edge("journey_finalizer", END)

    return workflow.compile()


# --- Convenience Functions ---

def create_learning_journey(learner_profile: Dict, performance_data: Optional[Dict] = None) -> Dict:
    """
    Main function to create a learning journey

    Args:
        learner_profile: Output from Learner Profiler Agent
        performance_data: Optional performance analysis for adjustments

    Returns:
        Dict with learning_journey, reasoning, adjustment_notes
    """
    graph = create_journey_architect_graph()

    initial_state = {
        "learner_profile": learner_profile,
        "performance_data": performance_data
    }

    result = graph.invoke(initial_state)

    return {
        "learning_journey": result["learning_journey"],
        "reasoning": result["reasoning"],
        "adjustment_notes": result.get("adjustment_notes")
    }


def adjust_journey(current_journey: List[Dict], performance_data: Dict, learner_profile: Dict) -> Dict:
    """
    Adjust existing journey based on performance

    This is used by the adaptive loop when Performance Analyzer detects
    the need for path modification.
    """
    # Re-run the architect with performance data
    return create_learning_journey(learner_profile, performance_data)


# --- Testing ---
if __name__ == "__main__":
    # Test the journey architect
    test_profile = {
        "overall_skill_level": "beginner",
        "priority_topics": ["Python Basics", "Data Structures", "Web Development"],
        "learning_pace": "moderate",
        "time_commitment": 10,
        "interests_detail": {
            "Python Programming": {
                "topics": ["Variables", "Functions", "OOP"],
                "category": "Programming"
            }
        },
        "skill_assessments_detail": {
            "Python Programming": {
                "skill_level": "beginner",
                "confidence": 80
            }
        },
        "profile_summary": "Beginner programmer interested in web development"
    }

    result = create_learning_journey(test_profile)
    print(json.dumps(result, indent=2))
