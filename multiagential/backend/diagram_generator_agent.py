"""
Diagram Generator Agent - Adaptive Learning System
Generates visual learning aids using Mermaid syntax.

This agent creates clear, educational diagrams that illustrate key concepts
and relationships for any given topic, enhancing visual learning.
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict
from openai import OpenAI
import os

class DiagramGenerationState(TypedDict):
    topic: str
    diagram: str

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

def diagram_generator_node(state: DiagramGenerationState) -> DiagramGenerationState:
    """
    Generates a Mermaid diagram for the given topic.

    Creates clear visual representations of concepts and their relationships
    to enhance understanding and retention.
    """
    topic = state["topic"]

    prompt = f"""
    Generate a Mermaid diagram that illustrates the key concepts of "{topic}".

    Requirements:
    - Use `graph TD` (Top Down flowchart)
    - Include 5-10 nodes maximum for clarity
    - Use clear, concise labels
    - Show relationships between concepts with arrows

    CRITICAL: Return ONLY the raw Mermaid code. DO NOT wrap it in ```mermaid code blocks.
    DO NOT include any explanatory text before or after the code.

    Example format (return exactly like this):
    graph TD
        A[Concept 1] --> B[Concept 2]
        B --> C[Concept 3]
        A --> D[Concept 4]
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in creating simple and clear Mermaid diagrams for educational purposes.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        diagram_code = completion.choices[0].message.content.strip()

        # Clean up the response - remove code blocks if present
        if "```mermaid" in diagram_code:
            diagram_code = diagram_code.split("```mermaid")[1].split("```")[0].strip()
        elif "```" in diagram_code:
            diagram_code = diagram_code.split("```")[1].split("```")[0].strip()

        # Validate it starts with graph
        if not diagram_code.startswith("graph"):
            print(f"WARNING: Diagram doesn't start with 'graph': {diagram_code[:100]}")

        return {"diagram": diagram_code}

    except Exception as e:
        print(f"Error generating diagram for {topic}: {e}")
        return {"diagram": "graph TD\n    A[Error generating diagram]"}


def create_diagram_generator_graph():
    """Creates the diagram generation graph"""
    workflow = StateGraph(DiagramGenerationState)
    workflow.add_node("diagram_generator", diagram_generator_node)
    workflow.set_entry_point("diagram_generator")
    workflow.add_edge("diagram_generator", END)
    return workflow.compile()


# Testing function
if __name__ == "__main__":
    print("🎨 Testing Diagram Generator Agent\n")

    diagram_graph = create_diagram_generator_graph()

    # Test case 1: Python concepts
    print("=" * 50)
    print("TEST 1: Python Data Structures")
    print("=" * 50)

    result = diagram_graph.invoke({
        "topic": "Python Data Structures"
    })

    print("Generated Mermaid diagram:")
    print(result['diagram'])
    print()

    # Test case 2: Complex topic
    print("=" * 50)
    print("TEST 2: Machine Learning Pipeline")
    print("=" * 50)

    result = diagram_graph.invoke({
        "topic": "Machine Learning Pipeline"
    })

    print("Generated Mermaid diagram:")
    print(result['diagram'])

    print("\n✅ Diagram Generator Agent ready!")
