"""
Feedback Agent - Adaptive Learning System
Provides context-aware motivational feedback based on learner performance.

This agent analyzes user sentiment and combines it with performance data
from the Performance Analyzer to deliver personalized, encouraging feedback
that keeps learners motivated and engaged.
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict
from openai import OpenAI
import os

# --- State ---
class FeedbackState(TypedDict):
    user_input: str
    sentiment: str
    feedback: str
    performance_context: Optional[Dict]  # From Performance Analyzer for personalized feedback

# --- Tools ---
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.environ.get("OPENROUTER_API_KEY"),
)

def sentiment_analysis_tool(text: str) -> str:
    """
    Performs sentiment analysis on the given text using an OpenRouter model.
    """
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a sentiment analysis expert. Analyze the sentiment of the following text and return 'positive', 'negative', or 'neutral'.",
            },
            {"role": "user", "content": text},
        ],
    )
    return completion.choices[0].message.content.lower()

# --- Nodes ---
def motivation_agent(state: FeedbackState) -> FeedbackState:
    """
    The Motivation and Feedback Agent node - now adaptive!

    Uses performance context from Performance Analyzer to provide
    personalized, context-aware motivational feedback.
    """
    user_input = state["user_input"]
    performance_context = state.get("performance_context", {})
    sentiment = sentiment_analysis_tool(user_input)

    # Base feedback based on sentiment
    feedback_prompt = ""
    if "positive" in sentiment:
        feedback_prompt = "The user seems happy and engaged. Provide some encouraging feedback."
    elif "negative" in sentiment:
        feedback_prompt = "The user seems frustrated or disengaged. Provide some supportive and motivational feedback."
    else:
        feedback_prompt = "The user seems neutral. Provide some feedback to keep them engaged."

    # Enhance with performance context if available
    if performance_context:
        strengths = performance_context.get("strengths", [])
        gaps = performance_context.get("knowledge_gaps", [])
        recent_score = performance_context.get("recent_score")

        context_info = f"\n\nPerformance Context:"
        if strengths:
            context_info += f"\n- Strengths: {', '.join(strengths[:3])}"
        if gaps:
            context_info += f"\n- Areas to improve: {', '.join(gaps[:3])}"
        if recent_score is not None:
            context_info += f"\n- Recent quiz score: {recent_score}%"

        feedback_prompt += context_info
        feedback_prompt += "\n\nProvide personalized feedback that acknowledges their progress and motivates them."

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a motivational coach for an adaptive learning platform. Provide personalized, encouraging feedback based on the user's performance and sentiment.",
            },
            {"role": "user", "content": feedback_prompt},
        ],
    )
    feedback = completion.choices[0].message.content

    return {"sentiment": sentiment, "feedback": feedback}

# --- Graph ---
def create_feedback_graph():
    """
    Creates the feedback generation graph.

    Provides adaptive, performance-aware motivational feedback.
    """
    workflow = StateGraph(FeedbackState)

    workflow.add_node("motivation_agent", motivation_agent)
    workflow.set_entry_point("motivation_agent")
    workflow.add_edge("motivation_agent", END)

    return workflow.compile()


# Testing function
if __name__ == "__main__":
    print("💬 Testing Feedback Agent\n")

    feedback_graph = create_feedback_graph()

    # Test case 1: Frustrated learner with performance context
    print("=" * 50)
    print("TEST 1: Frustrated Learner with Low Performance")
    print("=" * 50)

    result = feedback_graph.invoke({
        "user_input": "I'm really struggling with this topic. I don't think I'm making any progress.",
        "performance_context": {
            "strengths": ["Python Basics", "Data Types"],
            "knowledge_gaps": ["Recursion", "Dynamic Programming"],
            "recent_score": 45
        }
    })

    print(f"Sentiment: {result['sentiment']}")
    print(f"Feedback: {result['feedback']}")

    # Test case 2: Excited learner
    print("\n" + "=" * 50)
    print("TEST 2: Excited Learner with Good Performance")
    print("=" * 50)

    result = feedback_graph.invoke({
        "user_input": "This is amazing! I finally understand how this works!",
        "performance_context": {
            "strengths": ["Algorithms", "Data Structures", "Problem Solving"],
            "knowledge_gaps": ["System Design"],
            "recent_score": 85
        }
    })

    print(f"Sentiment: {result['sentiment']}")
    print(f"Feedback: {result['feedback']}")

    # Test case 3: No performance context
    print("\n" + "=" * 50)
    print("TEST 3: New Learner (No Performance Data)")
    print("=" * 50)

    result = feedback_graph.invoke({
        "user_input": "Just started learning. Not sure what to expect."
    })

    print(f"Sentiment: {result['sentiment']}")
    print(f"Feedback: {result['feedback']}")

    print("\n✅ Feedback Agent ready!")
