"""
Quiz Generator Agent - Adaptive Learning System
Creates difficulty-appropriate assessments based on learner profile and performance data.

This agent generates adaptive quizzes that match the user's current skill level,
ensuring optimal challenge without overwhelming beginners or boring advanced learners.
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from openai import OpenAI
import os
import json

class QuizGenerationState(TypedDict):
    topic: str
    user_id: str
    skill_level: str  # From Performance Analyzer: beginner, intermediate, advanced
    num_questions: int
    questions: List[Dict]
    difficulty: str

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

def invoke_llm_for_quiz(system_prompt: str, user_prompt: str, topic: str, skill_level: str, num_questions: int, max_retries: int = 3):
    """
    Invokes a language model with retry and fallback logic for quiz generation.
    """
    for model in LLM_MODELS:
        last_error = None
        current_prompt = user_prompt

        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}/{max_retries} with model {model} for quiz on '{topic}'...")
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": current_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                response_content = completion.choices[0].message.content

                if not response_content:
                    print(f"Empty response from {model}")
                    last_error = "Empty response"
                    continue

                # Try to parse the JSON
                quiz_data = json.loads(response_content)

                # Validate structure
                if "questions" in quiz_data and isinstance(quiz_data["questions"], list):
                    num_generated = len(quiz_data["questions"])

                    # Validate we got the right number of questions
                    if num_generated > 0:
                        print(f"Successfully generated {num_generated} questions with {model}")
                        return quiz_data
                    else:
                        last_error = "No questions generated"
                        current_prompt = f"""Your previous response for quiz on '{topic}' contained no questions.
                                        Original prompt: {user_prompt}
                                        Please generate exactly {num_questions} quiz questions."""
                else:
                    last_error = "Invalid JSON structure - missing 'questions' array"
                    current_prompt = f"""Your previous response for quiz on '{topic}' had an invalid structure.
                                    Original prompt: {user_prompt}
                                    Invalid response: {response_content[:500]}
                                    Error: {last_error}
                                    Please return a valid JSON object with a 'questions' array containing {num_questions} questions."""

            except json.JSONDecodeError as je:
                print(f"JSON DECODE ERROR for {topic} with {model}: {je}")
                print(f"Raw response: {response_content[:500] if response_content else 'Empty'}")
                last_error = je
                # Create a new prompt to fix the JSON
                current_prompt = f"""Your previous response for quiz on '{topic}' was not valid JSON. Please fix it.
                                Original prompt: {user_prompt}
                                Invalid response: {response_content[:500] if response_content else 'Empty'}
                                Error: {je}
                                Please return ONLY a valid JSON object with {num_questions} quiz questions."""

            except Exception as e:
                print(f"ERROR generating quiz for {topic} with {model}: {e}")
                last_error = e

        print(f"Failed to generate quiz with model {model} after {max_retries} attempts.")

    # If all models fail
    raise Exception(f"Failed to generate quiz for topic '{topic}' with all available models. Last error: {last_error}")


def quiz_generator_node(state: QuizGenerationState) -> QuizGenerationState:
    """Generate adaptive quiz based on learner skill level"""
    topic = state["topic"]
    skill_level = state.get("skill_level", "intermediate")
    num_questions = state.get("num_questions", 5)

    difficulty_guidance = {
        "beginner": "Basic concepts, definitions, simple recall questions. Focus on fundamental understanding.",
        "intermediate": "Application, understanding, problem-solving. Mix of recall and applied knowledge.",
        "advanced": "Analysis, synthesis, complex problem-solving. Deep understanding and edge cases."
    }

    system_prompt = "You are an expert quiz generator. Always return valid JSON with well-crafted educational questions."

    user_prompt = f"""Generate a quiz with {num_questions} multiple-choice questions about {topic}.

DIFFICULTY LEVEL: {skill_level.upper()}
{difficulty_guidance.get(skill_level, difficulty_guidance["intermediate"])}

Return ONLY valid JSON with this exact structure:
{{
    "questions": [
        {{
            "question": "Question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Correct option text (must match one of the options exactly)",
            "explanation": "Why this answer is correct"
        }}
    ]
}}

Requirements:
- Exactly {num_questions} questions
- Each question must have exactly 4 options
- The 'answer' field must contain the EXACT text of the correct option
- Questions should be appropriate for {skill_level} learners
- No code blocks, just pure JSON
"""

    try:
        print(f"🤖 Generating quiz for '{topic}' (skill: {skill_level}) with retry logic...")

        # Use retry logic with multiple models
        quiz_data = invoke_llm_for_quiz(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            topic=topic,
            skill_level=skill_level,
            num_questions=num_questions
        )

        return {
            "questions": quiz_data.get("questions", []),
            "difficulty": skill_level
        }

    except Exception as e:
        print(f"❌ FATAL ERROR: All quiz generation attempts failed for {topic}: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "questions": [],
            "difficulty": skill_level
        }


def create_quiz_generator_graph():
    """Creates the quiz generation graph"""
    workflow = StateGraph(QuizGenerationState)
    workflow.add_node("quiz_generator", quiz_generator_node)
    workflow.set_entry_point("quiz_generator")
    workflow.add_edge("quiz_generator", END)
    return workflow.compile()


# Testing function
if __name__ == "__main__":
    print("🧪 Testing Quiz Generator Agent\n")

    quiz_graph = create_quiz_generator_graph()

    # Test case 1: Beginner level
    print("=" * 50)
    print("TEST 1: Beginner Python Quiz")
    print("=" * 50)

    result = quiz_graph.invoke({
        "topic": "Python Basics",
        "user_id": "test_user",
        "skill_level": "beginner",
        "num_questions": 3
    })

    print(f"Difficulty: {result['difficulty']}")
    print(f"Questions generated: {len(result['questions'])}")

    if result['questions']:
        print("\nSample question:")
        q = result['questions'][0]
        print(f"Q: {q['question']}")
        print(f"Options: {q['options']}")
        print(f"Answer: {q['answer']}")

    # Test case 2: Advanced level
    print("\n" + "=" * 50)
    print("TEST 2: Advanced Data Structures Quiz")
    print("=" * 50)

    result = quiz_graph.invoke({
        "topic": "Advanced Data Structures",
        "user_id": "test_user",
        "skill_level": "advanced",
        "num_questions": 3
    })

    print(f"Difficulty: {result['difficulty']}")
    print(f"Questions generated: {len(result['questions'])}")

    if result['questions']:
        print("\nSample question:")
        q = result['questions'][0]
        print(f"Q: {q['question']}")
        print(f"Options: {q['options']}")
        print(f"Answer: {q['answer']}")

    print("\n✅ Quiz Generator Agent ready!")
