"""
Learner Profiler Agent - Multi-Agent Adaptive Learning System

This agent analyzes user onboarding data to create a comprehensive learner profile.
It determines skill levels across different interest areas and identifies learning preferences.

Role: Foundation agent that feeds into Journey Architect
Tools: LLM analysis, skill assessment, learning style detection
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional
from openai import OpenAI
import os
import json

# --- State ---
class LearnerProfileState(TypedDict):
    """State for learner profiling workflow"""
    # Inputs
    interests: List[str]  # ["Programming", "Data Science", ...]
    learning_goals: List[str]  # ["career_change", "skill_upgrade", ...]
    time_commitment: int  # hours per week
    learning_style_preference: str  # "visual", "reading", "interactive", "video"
    self_assessed_level: str  # "beginner", "intermediate", "advanced"
    background_info: Optional[str]  # Optional: previous experience

    # Intermediate
    analyzed_interests: Dict  # Detailed analysis of each interest
    skill_assessments: Dict  # Per-interest skill levels
    learning_style_analysis: Dict  # Detailed learning style breakdown

    # Outputs
    learner_profile: Dict  # Final comprehensive profile
    reasoning: str  # Agent's reasoning for profile decisions
    confidence: float  # Confidence in profile accuracy


# --- LLM Client ---
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


# --- Agents/Nodes ---

def interest_analyzer_node(state: LearnerProfileState) -> LearnerProfileState:
    """
    Analyzes user interests to determine topic categories and depth

    This node examines each interest area and categorizes it for better
    curriculum design by the Journey Architect agent.
    """
    interests = state["interests"]
    background = state.get("background_info", "")

    prompt = f"""
    Analyze the following learning interests for an adaptive learning platform.

    User Interests: {interests}
    Background: {background if background else "Not provided"}

    For each interest, determine:
    1. Category (e.g., "Programming", "Data Science", "Design", "Business")
    2. Specific topics within that interest
    3. Recommended starting difficulty based on common prerequisites
    4. Related interests that might benefit the learner

    Return a JSON object with this structure:
    {{
        "interest_name": {{
            "category": "...",
            "topics": ["topic1", "topic2", ...],
            "suggested_starting_level": "beginner|intermediate|advanced",
            "related_interests": ["..."],
            "reasoning": "why this analysis"
        }}
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educational counselor who analyzes learning interests and designs curriculum paths."
                },
                {"role": "user", "content": prompt}
            ],
        )

        response = completion.choices[0].message.content

        # Try to parse JSON
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            analyzed = json.loads(response)
        except json.JSONDecodeError:
            # If parsing fails, create a basic structure
            analyzed = {
                interest: {
                    "category": interest,
                    "topics": [interest],
                    "suggested_starting_level": state["self_assessed_level"],
                    "related_interests": [],
                    "reasoning": "Based on user self-assessment"
                }
                for interest in interests
            }

        return {"analyzed_interests": analyzed}

    except Exception as e:
        print(f"Error in interest_analyzer: {e}")
        # Fallback to basic analysis
        return {
            "analyzed_interests": {
                interest: {
                    "category": interest,
                    "topics": [interest],
                    "suggested_starting_level": state["self_assessed_level"],
                    "related_interests": [],
                    "reasoning": "Fallback analysis"
                }
                for interest in interests
            }
        }


def skill_assessor_node(state: LearnerProfileState) -> LearnerProfileState:
    """
    Assesses skill level for each interest area based on goals and background

    This provides more nuanced skill assessment than simple self-reporting,
    which helps the Performance Analyzer agent calibrate quiz difficulty.
    """
    analyzed_interests = state["analyzed_interests"]
    learning_goals = state["learning_goals"]
    self_assessed = state["self_assessed_level"]
    background = state.get("background_info", "")

    prompt = f"""
    Assess the skill level for each learning interest area.

    Analyzed Interests: {json.dumps(analyzed_interests, indent=2)}
    Learning Goals: {learning_goals}
    Self-Assessment: {self_assessed}
    Background: {background if background else "Not provided"}

    For each interest, provide:
    1. Recommended starting skill level (beginner/intermediate/advanced)
    2. Confidence in this assessment (0-100)
    3. Key indicators that influenced the decision
    4. Suggested quick assessment topics to verify level

    Return JSON:
    {{
        "interest_name": {{
            "skill_level": "beginner|intermediate|advanced",
            "confidence": 0-100,
            "indicators": ["indicator1", "indicator2"],
            "verification_topics": ["topic1", "topic2"],
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
                    "content": "You are an expert at assessing learner skill levels for personalized education."
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

            assessments = json.loads(response)
        except json.JSONDecodeError:
            # Fallback
            assessments = {
                interest: {
                    "skill_level": self_assessed,
                    "confidence": 70,
                    "indicators": ["Self-reported level"],
                    "verification_topics": [],
                    "reasoning": "Based on self-assessment"
                }
                for interest in analyzed_interests.keys()
            }

        return {"skill_assessments": assessments}

    except Exception as e:
        print(f"Error in skill_assessor: {e}")
        return {
            "skill_assessments": {
                interest: {
                    "skill_level": self_assessed,
                    "confidence": 70,
                    "indicators": [],
                    "verification_topics": [],
                    "reasoning": "Fallback"
                }
                for interest in analyzed_interests.keys()
            }
        }


def learning_style_analyzer_node(state: LearnerProfileState) -> LearnerProfileState:
    """
    Analyzes learning style preferences to personalize content delivery

    Helps Content Personalizer agent choose appropriate content formats.
    """
    style_preference = state["learning_style_preference"]
    goals = state["learning_goals"]
    time_commitment = state["time_commitment"]

    prompt = f"""
    Analyze learning style preferences for personalized content delivery.

    Preferred Style: {style_preference}
    Learning Goals: {goals}
    Time Commitment: {time_commitment} hours/week

    Provide recommendations for:
    1. Primary content format (text, video, interactive, visual)
    2. Secondary formats to use occasionally
    3. Optimal lesson length based on time commitment
    4. Engagement strategies for this learning style
    5. Warning signs if content format isn't working

    Return JSON:
    {{
        "primary_format": "...",
        "secondary_formats": ["..."],
        "optimal_lesson_length": "...",
        "engagement_strategies": ["..."],
        "warning_signs": ["..."],
        "personalization_notes": "..."
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in learning science and personalized education delivery."
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

            analysis = json.loads(response)
        except json.JSONDecodeError:
            analysis = {
                "primary_format": style_preference,
                "secondary_formats": ["text", "visual"],
                "optimal_lesson_length": "15-20 minutes",
                "engagement_strategies": ["Interactive exercises"],
                "warning_signs": ["Low completion rate"],
                "personalization_notes": "Standard approach"
            }

        return {"learning_style_analysis": analysis}

    except Exception as e:
        print(f"Error in learning_style_analyzer: {e}")
        return {
            "learning_style_analysis": {
                "primary_format": style_preference,
                "secondary_formats": ["text"],
                "optimal_lesson_length": "15 minutes",
                "engagement_strategies": [],
                "warning_signs": [],
                "personalization_notes": "Fallback"
            }
        }


def profile_synthesizer_node(state: LearnerProfileState) -> LearnerProfileState:
    """
    Synthesizes all analysis into a comprehensive learner profile

    This is the final output that Journey Architect will use to create
    the personalized learning path.
    """
    analyzed_interests = state["analyzed_interests"]
    skill_assessments = state["skill_assessments"]
    learning_style = state["learning_style_analysis"]
    goals = state["learning_goals"]
    time_commitment = state["time_commitment"]

    prompt = f"""
    Create a comprehensive learner profile by synthesizing all analysis.

    Interest Analysis: {json.dumps(analyzed_interests, indent=2)}
    Skill Assessments: {json.dumps(skill_assessments, indent=2)}
    Learning Style: {json.dumps(learning_style, indent=2)}
    Goals: {goals}
    Time Commitment: {time_commitment} hours/week

    Create a unified profile with:
    1. Overall skill level across all interests
    2. Priority topics to start with
    3. Learning pace recommendation (fast/moderate/slow)
    4. Personalization strategy summary
    5. Success metrics to track
    6. Confidence in this profile (0-100)

    Return JSON:
    {{
        "overall_skill_level": "beginner|intermediate|advanced",
        "priority_topics": ["topic1", "topic2", ...],
        "learning_pace": "fast|moderate|slow",
        "personalization_strategy": "...",
        "success_metrics": ["metric1", "metric2"],
        "confidence": 0-100,
        "profile_summary": "Human-readable summary",
        "reasoning": "Why this profile was created"
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educational profiler creating personalized learning plans."
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

            profile = json.loads(response)
        except json.JSONDecodeError:
            # Create basic profile
            profile = {
                "overall_skill_level": state["self_assessed_level"],
                "priority_topics": list(analyzed_interests.keys())[:3],
                "learning_pace": "moderate",
                "personalization_strategy": f"Focus on {learning_style['primary_format']} content",
                "success_metrics": ["completion_rate", "quiz_scores"],
                "confidence": 75,
                "profile_summary": f"Learner interested in {', '.join(analyzed_interests.keys())}",
                "reasoning": "Synthesized from user inputs"
            }

        # Add raw data to profile for Journey Architect
        full_profile = {
            **profile,
            "interests_detail": analyzed_interests,
            "skill_assessments_detail": skill_assessments,
            "learning_style_detail": learning_style,
            "time_commitment": time_commitment,
            "learning_goals": goals
        }

        return {
            "learner_profile": full_profile,
            "reasoning": profile.get("reasoning", "Profile created from comprehensive analysis"),
            "confidence": profile.get("confidence", 75) / 100.0
        }

    except Exception as e:
        print(f"Error in profile_synthesizer: {e}")
        return {
            "learner_profile": {
                "overall_skill_level": state["self_assessed_level"],
                "priority_topics": state["interests"][:3],
                "learning_pace": "moderate",
                "confidence": 70
            },
            "reasoning": "Fallback profile",
            "confidence": 0.7
        }


# --- Graph Creation ---

def create_learner_profiler_graph():
    """
    Creates the Learner Profiler agent graph

    Workflow:
    1. Analyze interests (categorize and expand)
    2. Assess skill levels (per interest)
    3. Analyze learning style (format preferences)
    4. Synthesize profile (comprehensive output)
    """
    workflow = StateGraph(LearnerProfileState)

    # Add nodes
    workflow.add_node("interest_analyzer", interest_analyzer_node)
    workflow.add_node("skill_assessor", skill_assessor_node)
    workflow.add_node("learning_style_analyzer", learning_style_analyzer_node)
    workflow.add_node("profile_synthesizer", profile_synthesizer_node)

    # Define flow
    workflow.set_entry_point("interest_analyzer")
    workflow.add_edge("interest_analyzer", "skill_assessor")
    workflow.add_edge("skill_assessor", "learning_style_analyzer")
    workflow.add_edge("learning_style_analyzer", "profile_synthesizer")
    workflow.add_edge("profile_synthesizer", END)

    return workflow.compile()


# --- Convenience Function ---

def create_learner_profile(onboarding_data: Dict) -> Dict:
    """
    Main function to create a learner profile from onboarding data

    Args:
        onboarding_data: Dict with interests, goals, time_commitment, etc.

    Returns:
        Dict with learner_profile, reasoning, confidence
    """
    graph = create_learner_profiler_graph()

    # Prepare initial state
    initial_state = {
        "interests": onboarding_data.get("interests", []),
        "learning_goals": onboarding_data.get("learning_goals", []),
        "time_commitment": onboarding_data.get("time_commitment", 5),
        "learning_style_preference": onboarding_data.get("learning_style", "mixed"),
        "self_assessed_level": onboarding_data.get("skill_level", "beginner"),
        "background_info": onboarding_data.get("background", "")
    }

    # Run the graph
    result = graph.invoke(initial_state)

    return {
        "learner_profile": result["learner_profile"],
        "reasoning": result["reasoning"],
        "confidence": result["confidence"]
    }


# --- Testing ---
if __name__ == "__main__":
    # Test the learner profiler
    test_data = {
        "interests": ["Python Programming", "Machine Learning", "Web Development"],
        "learning_goals": ["career_change", "skill_upgrade"],
        "time_commitment": 10,
        "learning_style": "interactive",
        "skill_level": "beginner",
        "background": "Have done some online tutorials"
    }

    result = create_learner_profile(test_data)
    print(json.dumps(result, indent=2))
