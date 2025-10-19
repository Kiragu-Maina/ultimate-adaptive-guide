#!/usr/bin/env python3
"""Test all 8 agents individually"""
import sys
import os

# Verify API key
if not os.environ.get("OPENROUTER_API_KEY"):
    print("ERROR: OPENROUTER_API_KEY not found")
    sys.exit(1)

print("=" * 60)
print("Testing All 8 Agents Individually")
print("=" * 60)
print()

# Test 1: Learner Profiler Agent
print("1. Learner Profiler Agent...")
try:
    from learner_profiler_agent import create_learner_profiler_graph
    graph = create_learner_profiler_graph()
    result = graph.invoke({
        "interests": ["Python"],
        "learning_goals": ["career_change"],
        "time_commitment": 10,
        "learning_style": "visual",
        "skill_level": "beginner",
        "background": "No experience"
    })
    print(f"   ✅ Created profile, skill: {result.get('skill_level')}")
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
print()

# Test 2: Journey Architect Agent  
print("2. Journey Architect Agent...")
try:
    from journey_architect_agent import create_journey_architect_graph
    graph = create_journey_architect_graph()
    result = graph.invoke({
        "profile": {
            "interests": ["Python"],
            "learning_goals": ["career_change"],
            "skill_level": "beginner"
        }
    })
    topics = result.get('learning_journey', [])
    print(f"   ✅ Created journey with {len(topics)} topics")
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
print()

# Test 3: Performance Analyzer Agent
print("3. Performance Analyzer Agent...")
try:
    from performance_analyzer_agent import create_performance_analyzer_graph
    graph = create_performance_analyzer_graph()
    result = graph.invoke({
        "user_id": "test_user",
        "quiz_results": [{"topic": "Python", "score": 80, "total": 100}]
    })
    print(f"   ✅ Analyzed performance, skill: {result.get('skill_level')}")
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
print()

# Test 4: Content Personalizer Agent
print("4. Content Personalizer Agent...")
try:
    from content_graph import create_content_graph
    graph = create_content_graph()
    result = graph.invoke({"topic": "Python Variables", "skill_level": "beginner"})
    print(f"   ✅ Generated content={bool(result.get('content'))}, exercises={bool(result.get('exercises'))}, diagram={bool(result.get('diagram'))}")
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
print()

# Test 5: Quiz Generator Agent
print("5. Quiz Generator Agent...")
try:
    from quiz_generator_agent import create_quiz_generator_graph
    graph = create_quiz_generator_graph()
    result = graph.invoke({
        "topic": "Python Basics",
        "user_id": "test",
        "skill_level": "beginner",
        "num_questions": 3
    })
    print(f"   ✅ Generated {len(result.get('questions', []))} questions at '{result.get('difficulty')}' level")
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
print()

# Test 6: Diagram Generator Agent
print("6. Diagram Generator Agent...")
try:
    from diagram_generator_agent import create_diagram_generator_graph
    graph = create_diagram_generator_graph()
    result = graph.invoke({"topic": "Python Data Types"})
    diagram = result.get('diagram', '')
    print(f"   ✅ Generated Mermaid diagram (valid={diagram.startswith('graph')})")
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
print()

# Test 7: Recommendation Agent
print("7. Recommendation Agent...")
try:
    from recommendation_agent import create_recommendation_agent_graph
    graph = create_recommendation_agent_graph()
    result = graph.invoke({
        "user_id": "test",
        "current_topic": "Python Basics",
        "performance_data": {
            "strengths": ["Variables"],
            "knowledge_gaps": ["Loops"],
            "recent_score": 75
        }
    })
    print(f"   ✅ Generated {len(result.get('recommendations', []))} recommendations")
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
print()

# Test 8: Feedback Agent
print("8. Feedback Agent...")
try:
    from feedback_agent import create_feedback_graph
    graph = create_feedback_graph()
    result = graph.invoke({
        "user_input": "I'm enjoying this!",
        "performance_context": {
            "strengths": ["Python Basics"],
            "knowledge_gaps": ["Advanced Topics"],
            "recent_score": 85
        }
    })
    print(f"   ✅ Sentiment='{result.get('sentiment')}', feedback={bool(result.get('feedback'))}")
except Exception as e:
    print(f"   ❌ FAILED: {str(e)[:80]}")
print()

print("=" * 60)
print("Agent Testing Complete!")
print("=" * 60)
