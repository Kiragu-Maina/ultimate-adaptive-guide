from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from openai import OpenAI
import os
from duckduckgo_search import DDGS
import httpx
from bs4 import BeautifulSoup
import json
from diagram_generator_agent import diagram_generator_node

# --- State ---
class ContentState(TypedDict):
    topic: str
    skill_level: str  # "beginner", "intermediate", "advanced" - adaptive parameter
    content: str
    exercises: List[str]
    resources: List[Dict]
    diagram: str

# --- Tools ---
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.environ.get("OPENROUTER_API_KEY"),
)

def web_search_tool(topic: str) -> List[Dict]:
    """
    Performs a web search for the given topic and returns a list of results.
    """
    # This tool is commented out as per user request to rely solely on LLM for content
    # with DDGS() as ddgs:
    #     search_query = f"{topic}"
    #     print(f"DEBUG: Searching for: {search_query}")
    #     try:
    #         results = ddgs.text(search_query, max_results=5, region="us-en")
    #     except Exception as e:
    #         print(f"ERROR: DDGS search failed for '{search_query}': {e}")
    #         results = []
    #     print("DDGS results:", results)
    #     return results
    return [] # Return empty list as web search is disabled

def fetch_and_parse(url: str) -> str:
    """
    Fetches the content of a URL and parses it to extract the main text.
    """
    # This tool is commented out as per user request to rely solely on LLM for content
    # try:
    #     with httpx.Client(timeout=10.0) as client:
    #         response = client.get(url)
    #         response.raise_for_status()
    #         soup = BeautifulSoup(response.text, 'html.parser')
            
    #         for script_or_style in soup(['script', 'style']):
    #             script_or_style.decompose()
            
    #         text = soup.get_text()
            
    #         lines = (line.strip() for line in text.splitlines())
    #         chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    #         text = '\n'.join(chunk for chunk in chunks if chunk)
            
    #         return text
    # except (httpx.RequestError, httpx.HTTPStatusError) as e:
    #     print(f"Error fetching {url}: {e}")
    #     return ""
    return "" # Return empty string as web fetching is disabled

# --- Nodes ---
LLM_MODELS = [
    "openai/gpt-oss-120b",
   
    "nousresearch/deephermes-3-mistral-24b-preview",
    "google/gemini-2.5-flash-lite"
    
]

def invoke_llm(system_prompt: str, user_prompt: str, topic: str, max_retries: int = 3):
    """
    Invokes a language model with retry and fallback logic.
    """
    for model in LLM_MODELS:
        last_error = None
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}/{max_retries} with model {model} for topic '{topic}'...")
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                content_response = completion.choices[0].message.content
                
                # Try to parse the JSON
                content_data = json.loads(content_response)
                
                # Basic validation
                if "content" in content_data and "exercises" in content_data and "resources" in content_data:
                    print(f"Successfully generated content with {model}")
                    return content_data
                else:
                    last_error = "Invalid JSON structure"
                    user_prompt = f"""Your previous response for topic '{topic}' had an invalid structure. Please fix it.
                                    Original prompt: {user_prompt}
                                    Invalid response: {content_response}
                                    Error: {last_error}
                                    Please return a valid JSON object with 'content', 'exercises', and 'resources' keys."""

            except json.JSONDecodeError as je:
                print(f"JSON DECODE ERROR for {topic} with {model}: {je}")
                print(f"Raw response: {content_response[:500]}")
                last_error = je
                # Create a new prompt to fix the JSON
                user_prompt = f"""Your previous response for topic '{topic}' was not valid JSON. Please fix it.
                                Original prompt: {user_prompt}
                                Invalid response: {content_response}
                                Error: {je}
                                Please return ONLY a valid JSON object."""

            except Exception as e:
                print(f"ERROR generating content for {topic} with {model}: {e}")
                last_error = e
        
        print(f"Failed to generate content with model {model} after {max_retries} attempts.")

    # If all models fail
    raise Exception(f"Failed to generate content for topic '{topic}' with all available models. Last error: {last_error}")


def content_personalizer_agent(state: ContentState) -> ContentState:
    """
    Generates comprehensive adaptive content (overview, exercises, resources) for the given topic.
    Uses skill_level parameter from Performance Analyzer to personalize content depth.
    """
    topic = state["topic"]
    skill_level = state.get("skill_level", "intermediate")

    skill_guidance = {
        "beginner": "Focus on fundamental concepts with clear explanations and simple examples. Avoid jargon. Use analogies.",
        "intermediate": "Balance theory and practice. Include more technical details and moderate complexity examples.",
        "advanced": "Deep dive into advanced concepts, edge cases, and best practices. Include complex examples and optimizations."
    }

    system_prompt = "You are an expert educational content generator. You ALWAYS respond with valid JSON containing markdown content, structured exercises, and curated resources."
    user_prompt = f"""
    Generate a comprehensive learning module for the topic "{topic}".

    SKILL LEVEL: {skill_level.upper()}
    {skill_guidance.get(skill_level, skill_guidance["intermediate"])}

    You MUST respond with ONLY a valid JSON object. Do not include any text before or after the JSON.

    Required JSON structure:
    {{
        "content": "Detailed Markdown content here with ## headers, **bold**, code blocks, etc.",
        "exercises": [
            {{"description": "Exercise description", "type": "coding"}},
            {{"description": "Exercise description", "type": "analysis"}}
        ],
        "resources": [
            {{"title": "Resource name", "url": "https://example.com", "type": "web"}},
            {{"title": "PDF resource", "url": "https://example.com/file.pdf", "type": "pdf"}}
        ]
    }}

    Requirements:
    - "content": MUST be in Markdown format with proper headers (##, ###), bullet points, code blocks (```), bold (**text**), etc.
    - "exercises": Array of 3-5 exercise objects, each with "description" (string) and "type" (one of: "coding", "analysis", "optimization", "debugging")
    - "resources": Array of 3-5 resource objects, each with "title" (string), "url" (valid URL string), "type" (either "web" or "pdf")

    Return ONLY the JSON object, nothing else.
    """
    
    try:
        content_data = invoke_llm(system_prompt, user_prompt, topic)

        # Validate structure
        if not isinstance(content_data.get("content"), str):
            print(f"WARNING: Invalid content field type: {type(content_data.get('content'))}")
            content_data["content"] = str(content_data.get("content", ""))

        if not isinstance(content_data.get("exercises"), list):
            print(f"WARNING: Invalid exercises field type: {type(content_data.get('exercises'))}")
            content_data["exercises"] = []

        if not isinstance(content_data.get("resources"), list):
            print(f"WARNING: Invalid resources field type: {type(content_data.get('resources'))}")
            content_data["resources"] = []

        return {
            "content": content_data.get("content", ""),
            "exercises": content_data.get("exercises", []),
            "resources": content_data.get("resources", [])
        }
    except Exception as e:
        print(f"ERROR in content_personalizer_agent for {topic}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "content": f"# {topic}\n\nAn error occurred while generating content.",
            "exercises": [],
            "resources": []
        }

# diagram_generator_agent moved to diagram_generator_agent.py and imported above

# --- Graph ---
def create_content_graph():
    """
    Creates the content personalization graph.

    Combines Content Personalizer Agent and Diagram Generator Agent
    to deliver comprehensive, visually-enhanced learning materials.
    """
    workflow = StateGraph(ContentState)

    workflow.add_node("content_personalizer", content_personalizer_agent)
    workflow.add_node("diagram_generator", diagram_generator_node)

    workflow.set_entry_point("content_personalizer")
    workflow.add_edge("content_personalizer", "diagram_generator")
    workflow.add_edge("diagram_generator", END)

    return workflow.compile()