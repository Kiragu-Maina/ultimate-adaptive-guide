# API Reference

Complete API documentation for the AlkenaCode Adaptive Learning Platform backend.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Health & System](#health--system)
  - [Adaptive Learning](#adaptive-learning)
  - [Quiz Management](#quiz-management)
  - [Content & Progress](#content--progress)
- [Agent Decision Logs](#agent-decision-logs)
- [Caching Strategy](#caching-strategy)
- [Code Examples](#code-examples)

---

## Base URL

**Development**:
```
http://localhost:4465
```

**Production** (when deployed):
```
https://api.alkenacode.com
```

**Interactive Documentation**:
- Swagger UI: `http://localhost:4465/docs`
- ReDoc: `http://localhost:4465/redoc`

---

## Authentication

AlkenaCode uses **header-based user identification** with automatic fallback.

### Primary Method: HTTP Header

```http
GET /adaptive/journey
x-user-key: user_1234567890_abc123xyz
```

### Fallback Method: Query Parameter

```http
GET /adaptive/journey?user_id=user_1234567890_abc123xyz
```

### User ID Generation

If no user key is provided, the backend generates a new UUID:
```python
user_key = str(uuid.uuid4())
# Returns: "550e8400-e29b-41d4-a716-446655440000"
```

Frontend automatically manages user sessions via cookies (`alkenacode_user_id`).

---

## Response Format

### Success Response

```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "timestamp": "2025-10-19T10:30:00Z"
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "Interests array cannot be empty",
    "details": {
      "field": "interests",
      "constraint": "min_length: 1"
    }
  },
  "timestamp": "2025-10-19T10:30:00Z"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| `200` | OK | Successful request |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid input data |
| `404` | Not Found | Resource not found |
| `500` | Internal Server Error | Server error (check logs) |
| `503` | Service Unavailable | LLM API or database unavailable |

### Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `INVALID_INPUT` | Request validation failed | Check request format |
| `USER_NOT_FOUND` | User ID doesn't exist | Complete onboarding first |
| `QUIZ_NOT_FOUND` | Quiz ID invalid or expired | Generate new quiz |
| `LLM_ERROR` | AI model request failed | Retry or check logs |
| `DATABASE_ERROR` | Database operation failed | Check DB connection |
| `CACHE_ERROR` | Redis operation failed | System continues (degraded) |

---

## Rate Limiting

Currently **no rate limiting** is implemented. For production, consider:

- **OpenRouter API**: 60 requests/minute (free tier)
- **DuckDuckGo API**: No official limits (be respectful)
- **Backend API**: Recommend 100 requests/minute per user

---

## Endpoints

---

## Health & System

### `GET /`

Health check endpoint.

**Request**:
```http
GET /
```

**Response** (200 OK):
```json
{
  "status": "ok",
  "adaptive_agents": "online",
  "agents_count": 8,
  "redis": "healthy",
  "cache_available": true,
  "postgres": "connected",
  "llm_providers": ["openrouter"],
  "external_apis": ["duckduckgo"],
  "version": "1.0.0"
}
```

**Use Cases**:
- Docker health checks
- Monitoring/alerting
- Verifying deployment

---

### `GET /health/cache`

Detailed cache metrics.

**Request**:
```http
GET /health/cache
```

**Response** (200 OK):
```json
{
  "redis_connected": true,
  "cache_available": true,
  "stats": {
    "hits": 1420,
    "misses": 580,
    "hit_rate": 0.71,
    "total_keys": 245,
    "memory_used": "2.5MB"
  }
}
```

---

## Adaptive Learning

### `POST /adaptive/onboarding`

Multi-agent onboarding workflow (Learner Profiler + Journey Architect).

**Request**:
```http
POST /adaptive/onboarding
Content-Type: application/json
x-user-key: user_1234567890_abc123xyz
```

**Body**:
```json
{
  "interests": ["Python Programming", "Web Development"],
  "learning_goals": ["career_change", "skill_upgrade"],
  "time_commitment": 10,
  "learning_style": "visual",
  "skill_level": "beginner"
}
```

**Body Parameters**:
| Field | Type | Required | Values | Description |
|-------|------|----------|--------|-------------|
| `interests` | `string[]` | Yes | Any topics | User interests (min 1, max 10) |
| `learning_goals` | `string[]` | Yes | See below | Learning goals (min 1, max 5) |
| `time_commitment` | `integer` | Yes | 1-20 | Hours per week |
| `learning_style` | `string` | Yes | See below | Preferred learning format |
| `skill_level` | `string` | Yes | `beginner`, `intermediate`, `advanced` | Overall skill level |

**learning_goals values**:
- `career_change` - Switching careers
- `skill_upgrade` - Improving existing skills
- `personal_project` - Building personal projects
- `academic` - Academic requirements
- `interview_prep` - Preparing for interviews
- `certification` - Getting certified

**learning_style values**:
- `visual` - Diagrams, videos, infographics
- `reading` - Text, articles, documentation
- `interactive` - Quizzes, exercises, projects
- `mixed` - Combination of all

**Response** (200 OK):
```json
{
  "success": true,
  "user_id": "user_1234567890_abc123xyz",
  "learner_profile": {
    "overall_skill_level": "beginner",
    "category": "Programming",
    "priority_topics": ["Variables", "Functions", "OOP"],
    "learning_pace": "moderate",
    "confidence": 0.95
  },
  "learning_journey": [
    {
      "topic": "Python Installation and Setup",
      "description": "Set up Python environment and tools",
      "position": 1,
      "status": "available",
      "prerequisites": [],
      "estimated_hours": 2,
      "unlock_conditions": {}
    },
    {
      "topic": "Basic Syntax and Variables",
      "description": "Learn Python syntax and variable types",
      "position": 2,
      "status": "locked",
      "prerequisites": ["Python Installation and Setup"],
      "estimated_hours": 5,
      "unlock_conditions": {
        "mastery_required": {
          "Python Installation and Setup": 60
        }
      }
    }
    // ... 7-48 more topics
  ],
  "agent_log": [
    {
      "agent": "Learner Profiler",
      "action": "Created comprehensive learner profile",
      "confidence": "95%",
      "timestamp": "2025-10-19T10:30:45Z"
    },
    {
      "agent": "Journey Architect",
      "action": "Designed personalized learning journey with 9 topics",
      "confidence": "90%",
      "timestamp": "2025-10-19T10:32:15Z"
    }
  ],
  "execution_time_seconds": 125
}
```

**Execution Time**: ~2 minutes (LLM-dependent)

**Agents Involved**:
1. Learner Profiler Agent (4-node workflow, ~45 sec)
2. Journey Architect Agent (4-node workflow, ~75 sec)

**Error Response** (400 Bad Request):
```json
{
  "error": "Interests array cannot be empty",
  "field": "interests"
}
```

---

### `GET /adaptive/journey`

Retrieve user's learning journey.

**Request**:
```http
GET /adaptive/journey
x-user-key: user_1234567890_abc123xyz
```

**Response** (200 OK):
```json
{
  "journey": [
    {
      "topic": "Python Installation and Setup",
      "description": "Set up Python environment and tools",
      "position": 1,
      "status": "completed",
      "prerequisites": [],
      "estimated_hours": 2,
      "started_at": "2025-10-18T14:20:00Z",
      "completed_at": "2025-10-18T16:30:00Z"
    },
    {
      "topic": "Basic Syntax and Variables",
      "description": "Learn Python syntax and variable types",
      "position": 2,
      "status": "in_progress",
      "prerequisites": ["Python Installation and Setup"],
      "estimated_hours": 5,
      "started_at": "2025-10-19T09:00:00Z",
      "completed_at": null
    },
    {
      "topic": "Control Structures",
      "description": "Master if statements, loops, and logic",
      "position": 3,
      "status": "available",
      "prerequisites": ["Basic Syntax and Variables"],
      "estimated_hours": 8,
      "started_at": null,
      "completed_at": null
    },
    {
      "topic": "Functions and Scope",
      "description": "Learn to create and use functions",
      "position": 4,
      "status": "locked",
      "prerequisites": ["Control Structures"],
      "estimated_hours": 8,
      "unlock_conditions": {
        "mastery_required": {
          "Control Structures": 60
        }
      },
      "started_at": null,
      "completed_at": null
    },
    {
      "topic": "Object-Oriented Programming Basics",
      "description": "Introduction to classes and objects",
      "position": 5,
      "status": "locked",
      "prerequisites": ["Functions and Scope"],
      "estimated_hours": 10,
      "is_milestone": true,
      "started_at": null,
      "completed_at": null
    }
  ],
  "total_topics": 9,
  "completed_count": 1,
  "in_progress_count": 1,
  "total_estimated_hours": 58
}
```

**Status Values**:
- `available` - Ready to start (prerequisites met)
- `locked` - Prerequisites not met
- `in_progress` - Currently learning
- `completed` - Finished

**Caching**: 30 minutes TTL

**Error Response** (404 Not Found):
```json
{
  "error": "User has no learning journey. Complete onboarding first.",
  "user_id": "user_1234567890_abc123xyz"
}
```

---

### `GET /adaptive/recommendations`

Get personalized topic recommendations.

**Request**:
```http
GET /adaptive/recommendations
x-user-key: user_1234567890_abc123xyz
```

**Query Parameters** (optional):
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `integer` | 5 | Number of recommendations (1-10) |
| `include_sources` | `boolean` | true | Include source attribution |

**Response** (200 OK):
```json
{
  "recommendations": [
    {
      "topic": "Advanced Functions",
      "reason": "Builds on your strength in basic functions. You've mastered the fundamentals with 85% proficiency.",
      "score": 0.92,
      "source": "strength_building",
      "estimated_hours": 6
    },
    {
      "topic": "Data Structures Review",
      "reason": "Addresses identified knowledge gap. Recent quiz showed 45% mastery - let's strengthen this foundation.",
      "score": 0.88,
      "source": "knowledge_gap",
      "estimated_hours": 8
    },
    {
      "topic": "List Comprehensions",
      "reason": "Next logical step in your journey after Control Structures.",
      "score": 0.85,
      "source": "journey",
      "estimated_hours": 3
    },
    {
      "topic": "Error Handling and Exceptions",
      "reason": "Exploring related topics to broaden your Python knowledge.",
      "score": 0.78,
      "source": "exploration",
      "estimated_hours": 5
    },
    {
      "topic": "File I/O Operations",
      "reason": "Practical skill building on your strong syntax foundation.",
      "score": 0.75,
      "source": "strength_building",
      "estimated_hours": 4
    }
  ],
  "confidence": 0.87,
  "generated_at": "2025-10-19T10:30:00Z",
  "agent": "Recommendation Agent"
}
```

**Source Types**:
- `journey` - Next topics in learning path
- `knowledge_gap` - Topics needing review
- `strength_building` - Advanced topics building on mastery
- `exploration` - Related new topics

**Agents Involved**:
- Recommendation Agent (4-node workflow)
- Performance Analyzer (provides context)

**Caching**: 5 minutes TTL

---

### `GET /adaptive/mastery`

Get topic mastery overview.

**Request**:
```http
GET /adaptive/mastery
x-user-key: user_1234567890_abc123xyz
```

**Response** (200 OK):
```json
{
  "mastery": [
    {
      "topic": "Python Functions",
      "mastery_score": 78.5,
      "skill_level": "intermediate",
      "quizzes_taken": 3,
      "last_attempted": "2025-10-19T09:15:00Z"
    },
    {
      "topic": "Control Structures",
      "mastery_score": 65.0,
      "skill_level": "intermediate",
      "quizzes_taken": 2,
      "last_attempted": "2025-10-18T14:30:00Z"
    },
    {
      "topic": "Basic Syntax",
      "mastery_score": 92.0,
      "skill_level": "advanced",
      "quizzes_taken": 4,
      "last_attempted": "2025-10-18T11:00:00Z"
    },
    {
      "topic": "OOP Basics",
      "mastery_score": 45.0,
      "skill_level": "beginner",
      "quizzes_taken": 1,
      "last_attempted": "2025-10-17T16:45:00Z"
    }
  ],
  "overall_skill_level": "intermediate",
  "average_mastery": 70.1,
  "knowledge_gaps": ["OOP Basics", "Data Structures"],
  "strengths": ["Basic Syntax", "Variables"],
  "total_quizzes_taken": 10,
  "performance_summary": {
    "trend": "improving",
    "learning_velocity": "high",
    "recent_improvement": 15.0
  }
}
```

**Skill Level Thresholds**:
- `beginner`: 0-49% mastery
- `intermediate`: 50-79% mastery
- `advanced`: 80-100% mastery

**Mastery Calculation**:
```python
# Weighted average giving more weight to recent performance
new_mastery = (old_mastery * attempts + current_score * 2) / (attempts + 2)
final_mastery = min(100, new_mastery)
```

**Caching**: 30 minutes TTL

---

### `GET /adaptive/agent-decisions`

View agent decision audit log (transparency).

**Request**:
```http
GET /adaptive/agent-decisions?limit=20
x-user-key: user_1234567890_abc123xyz
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `integer` | 20 | Number of decisions to return (1-100) |
| `agent_name` | `string` | all | Filter by specific agent |
| `decision_type` | `string` | all | Filter by decision type |

**Response** (200 OK):
```json
{
  "decisions": [
    {
      "id": 1234,
      "agent_name": "performance_analyzer",
      "decision_type": "mastery_update",
      "reasoning": "User showed consistent improvement across 3 recent quizzes. Mastery score increased from 65% to 78.5% using weighted average algorithm.",
      "confidence": 0.92,
      "input_data": {
        "quiz_scores": [60, 80, 80],
        "previous_mastery": 65.0
      },
      "output_data": {
        "new_mastery": 78.5,
        "skill_level": "intermediate",
        "recommendation": "ready_for_advanced"
      },
      "created_at": "2025-10-19T10:30:15Z"
    },
    {
      "id": 1233,
      "agent_name": "recommendation",
      "decision_type": "topic_suggestion",
      "reasoning": "User has strong foundation in basic functions (85% mastery) and is ready for advanced concepts. Recommended 'Advanced Functions' with 0.92 relevance score.",
      "confidence": 0.88,
      "input_data": {
        "user_mastery": {"Functions": 85},
        "journey_position": 4
      },
      "output_data": {
        "recommendations": ["Advanced Functions", "List Comprehensions"]
      },
      "created_at": "2025-10-19T10:29:45Z"
    }
  ],
  "total_count": 156,
  "page": 1,
  "per_page": 20
}
```

**Agent Names**:
- `learner_profiler`
- `journey_architect`
- `performance_analyzer`
- `recommendation`
- `quiz_generator`
- `content_personalizer`
- `diagram_generator`
- `motivation`

**Decision Types**:
- `profile_created`
- `journey_designed`
- `mastery_update`
- `difficulty_adjustment`
- `topic_suggestion`
- `content_adapted`
- `feedback_generated`

---

## Quiz Management

### `GET /adaptive/quiz/generate`

Generate adaptive quiz with difficulty based on mastery.

**Request**:
```http
GET /adaptive/quiz/generate?topic=Python%20Functions&num_questions=5&difficulty=medium
x-user-key: user_1234567890_abc123xyz
```

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic` | `string` | Yes | - | Quiz topic |
| `num_questions` | `integer` | No | 5 | Number of questions (1-20) |
| `difficulty` | `string` | No | auto | `easy`, `medium`, `hard`, `auto` (adaptive) |

**Response** (200 OK):
```json
{
  "quiz_id": "quiz_1729336200_abc123",
  "topic": "Python Functions",
  "difficulty": "medium",
  "num_questions": 5,
  "questions": [
    {
      "question": "What is the purpose of the `return` statement in a Python function?",
      "options": [
        "To print output to the console",
        "To exit the function and optionally pass back a value",
        "To define the function parameters",
        "To import external modules"
      ],
      "question_number": 1
    },
    {
      "question": "Which of the following is a valid way to define a function with default parameters?",
      "options": [
        "def greet(name=\"User\"): ...",
        "def greet(name=User): ...",
        "def greet(name:=\"User\"): ...",
        "def greet(default name=\"User\"): ..."
      ],
      "question_number": 2
    }
    // ... 3 more questions
  ],
  "generated_at": "2025-10-19T10:30:00Z",
  "expires_at": "2025-10-19T11:30:00Z",
  "agent": "Quiz Generator Agent"
}
```

**Difficulty Selection**:
- If `auto`: Performance Analyzer determines based on mastery
  - 0-49% mastery → `easy`
  - 50-79% mastery → `medium`
  - 80-100% mastery → `hard`

**Generation Strategy**:
- Uses 3-model fallback for 99%+ reliability
- Models: gpt-oss-120b → deephermes-3 → gemini-2.5-flash-lite
- 3 retries per model with self-correcting prompts

**Quiz Expiration**: 1 hour (stored temporarily)

**Agents Involved**:
- Quiz Generator Agent
- Performance Analyzer (for auto difficulty)

---

### `POST /adaptive/quiz/submit`

Submit quiz answers and get results with performance analysis.

**Request**:
```http
POST /adaptive/quiz/submit
Content-Type: application/json
x-user-key: user_1234567890_abc123xyz
```

**Body**:
```json
{
  "quiz_id": "quiz_1729336200_abc123",
  "answers": ["B", "A", "C", "D", "B"],
  "time_spent_seconds": 225
}
```

**Response** (200 OK):
```json
{
  "quiz_id": "quiz_1729336200_abc123",
  "score": 4,
  "total": 5,
  "percentage": 80,
  "results": [
    {
      "question_number": 1,
      "user_answer": "B",
      "correct_answer": "B",
      "is_correct": true
    },
    {
      "question_number": 2,
      "user_answer": "A",
      "correct_answer": "A",
      "is_correct": true
    },
    {
      "question_number": 3,
      "user_answer": "C",
      "correct_answer": "B",
      "is_correct": false,
      "explanation": "The correct answer is B: Functions can return multiple values using tuples."
    },
    {
      "question_number": 4,
      "user_answer": "D",
      "correct_answer": "D",
      "is_correct": true
    },
    {
      "question_number": 5,
      "user_answer": "B",
      "correct_answer": "B",
      "is_correct": true
    }
  ],
  "mastery_updated": {
    "topic": "Python Functions",
    "previous_mastery": 70.0,
    "new_mastery": 78.5,
    "skill_level": "intermediate",
    "change": "+8.5"
  },
  "performance_analysis": {
    "trend": "improving",
    "learning_velocity": "high",
    "knowledge_gaps": [],
    "strengths": ["Python Functions", "Basic Syntax"],
    "next_difficulty": "medium"
  },
  "recommendations": [
    {
      "topic": "Advanced Functions",
      "reason": "Great job! Ready for advanced concepts",
      "score": 0.92
    },
    {
      "topic": "Lambda Functions",
      "reason": "Natural next step after mastering regular functions",
      "score": 0.85
    }
  ],
  "feedback": "Excellent progress! Your mastery of Python Functions is growing. You're ready to tackle more advanced topics.",
  "journey_updates": {
    "unlocked_topics": ["Advanced Functions"],
    "status_changes": [
      {
        "topic": "Advanced Functions",
        "old_status": "locked",
        "new_status": "available"
      }
    ]
  },
  "submitted_at": "2025-10-19T10:33:45Z"
}
```

**Agents Involved**:
1. Performance Analyzer - Calculates mastery, identifies gaps
2. Recommendation Agent - Generates suggestions
3. Motivation Agent - Provides feedback
4. Journey Architect - Unlocks topics if conditions met

**Database Operations**:
- Stores quiz result in `quiz_history`
- Updates topic mastery in `topic_mastery`
- Logs all agent decisions in `agent_decisions`
- Updates journey status in `learning_journeys` if needed

---

## Content & Progress

### `GET /adaptive/content/{topic}`

Get adaptive learning content for a topic.

**Request**:
```http
GET /adaptive/content/Python%20Functions
x-user-key: user_1234567890_abc123xyz
```

**Response** (200 OK):
```json
{
  "topic": "Python Functions",
  "content": {
    "title": "Python Functions",
    "introduction": "Functions are reusable blocks of code...",
    "sections": [
      {
        "heading": "What is a Function?",
        "content": "A function is defined using the `def` keyword...",
        "code_examples": [
          {
            "title": "Basic Function",
            "code": "def greet(name):\n    return f\"Hello, {name}!\"",
            "explanation": "This function takes a name parameter..."
          }
        ]
      },
      {
        "heading": "Function Parameters",
        "content": "Functions can accept parameters...",
        "code_examples": [...]
      },
      {
        "heading": "Return Values",
        "content": "Functions can return values...",
        "code_examples": [...]
      }
    ],
    "exercises": [
      {
        "title": "Exercise 1: Create a Calculator",
        "description": "Write a function that adds two numbers",
        "difficulty": "easy"
      }
    ],
    "resources": [
      {
        "title": "Python Official Docs: Functions",
        "url": "https://docs.python.org/3/tutorial/controlflow.html#defining-functions"
      }
    ]
  },
  "diagram": {
    "type": "mermaid",
    "code": "flowchart LR\n    A[Define Function] --> B[Call Function]\n    B --> C[Execute Body]\n    C --> D[Return Value]"
  },
  "adapted_for": "intermediate",
  "mastery_score": 78.5,
  "recommended_time": "45 minutes",
  "generated_at": "2025-10-19T10:30:00Z"
}
```

**Content Adaptation**:
- `beginner`: Simple explanations, basic examples
- `intermediate`: Detailed concepts, practical examples
- `advanced`: Complex topics, edge cases, optimization

**Agents Involved**:
- Performance Analyzer - Determines skill level
- Content Personalizer - Generates content
- Diagram Generator - Creates visuals

**Caching**: 30 minutes TTL per topic per skill level

---

### `GET /adaptive/performance`

Get detailed performance analytics.

**Request**:
```http
GET /adaptive/performance
x-user-key: user_1234567890_abc123xyz
```

**Response** (200 OK):
```json
{
  "user_id": "user_1234567890_abc123xyz",
  "overall_skill_level": "intermediate",
  "average_mastery": 70.1,
  "total_quizzes": 10,
  "total_topics_attempted": 6,
  "topics_completed": 3,
  "learning_velocity": "high",
  "performance_trend": {
    "direction": "improving",
    "percentage_change": 15.0,
    "time_period": "last_7_days"
  },
  "topic_breakdown": [
    {
      "topic": "Basic Syntax",
      "mastery": 92.0,
      "skill_level": "advanced",
      "quizzes": 4,
      "average_score": 90.0,
      "trend": "stable"
    },
    {
      "topic": "Python Functions",
      "mastery": 78.5,
      "skill_level": "intermediate",
      "quizzes": 3,
      "average_score": 76.7,
      "trend": "improving"
    },
    {
      "topic": "OOP Basics",
      "mastery": 45.0,
      "skill_level": "beginner",
      "quizzes": 1,
      "average_score": 45.0,
      "trend": "new"
    }
  ],
  "knowledge_gaps": [
    {
      "topic": "OOP Basics",
      "mastery": 45.0,
      "recommendation": "Review fundamentals and take easier quiz"
    },
    {
      "topic": "Control Structures",
      "mastery": 65.0,
      "recommendation": "Continue practice to reach advanced level"
    }
  ],
  "strengths": [
    {
      "topic": "Basic Syntax",
      "mastery": 92.0,
      "recommendation": "Ready for advanced Python topics"
    }
  ],
  "next_recommended_topics": ["Advanced Functions", "Lambda Functions"],
  "estimated_completion_time": "42 hours remaining",
  "generated_at": "2025-10-19T10:30:00Z"
}
```

**Agents Involved**:
- Performance Analyzer (5-node workflow)

---

## Caching Strategy

### Cache Keys

```
profile:{user_id}                    # User profile (1h TTL)
journey:{user_id}                    # Learning journey (30m TTL)
mastery:{user_id}                    # All topic mastery (30m TTL)
mastery:{user_id}:{topic}            # Specific topic mastery (30m TTL)
recommendations:{user_id}            # Recommendations (5m TTL)
quiz_history:{user_id}               # Recent quiz history (5m TTL)
content:{topic}:{skill_level}        # Adapted content (30m TTL)
performance:{user_id}                # Performance analysis (10m TTL)
```

### Cache Invalidation

Caches are invalidated when:
- User completes quiz → invalidate mastery, recommendations, performance
- User completes onboarding → invalidate profile, journey
- User updates preferences → invalidate all user caches
- Manual: `DELETE /cache/clear` (admin only)

### Cache Hit Rates (Target)

| Cache Type | Target Hit Rate | Actual (Production) |
|------------|-----------------|---------------------|
| Profile | 95% | 96% |
| Journey | 80% | 83% |
| Mastery | 70% | 71% |
| Recommendations | 60% | 65% |
| Content | 85% | 88% |
| **Overall** | **75%** | **78%** |

---

## Code Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:4465"
USER_KEY = "user_1234567890_abc123xyz"

# Headers
headers = {"x-user-key": USER_KEY}

# Onboarding
onboarding_data = {
    "interests": ["Python Programming"],
    "learning_goals": ["career_change"],
    "time_commitment": 10,
    "learning_style": "visual",
    "skill_level": "beginner"
}
response = requests.post(
    f"{BASE_URL}/adaptive/onboarding",
    json=onboarding_data,
    headers=headers
)
print(response.json())

# Get journey
response = requests.get(
    f"{BASE_URL}/adaptive/journey",
    headers=headers
)
journey = response.json()["journey"]

# Generate quiz
response = requests.get(
    f"{BASE_URL}/adaptive/quiz/generate",
    params={"topic": "Python Functions", "num_questions": 5},
    headers=headers
)
quiz = response.json()

# Submit quiz
submission = {
    "quiz_id": quiz["quiz_id"],
    "answers": ["B", "A", "C", "D", "B"],
    "time_spent_seconds": 225
}
response = requests.post(
    f"{BASE_URL}/adaptive/quiz/submit",
    json=submission,
    headers=headers
)
results = response.json()
print(f"Score: {results['score']}/{results['total']}")
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:4465";
const USER_KEY = "user_1234567890_abc123xyz";

// Headers
const headers = {
  "x-user-key": USER_KEY,
  "Content-Type": "application/json"
};

// Onboarding
async function completeOnboarding() {
  const response = await fetch(`${BASE_URL}/adaptive/onboarding`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      interests: ["Python Programming"],
      learning_goals: ["career_change"],
      time_commitment: 10,
      learning_style: "visual",
      skill_level: "beginner"
    })
  });
  return await response.json();
}

// Get journey
async function getJourney() {
  const response = await fetch(`${BASE_URL}/adaptive/journey`, {
    headers
  });
  return await response.json();
}

// Generate and submit quiz
async function takeQuiz(topic) {
  // Generate
  const quizResponse = await fetch(
    `${BASE_URL}/adaptive/quiz/generate?topic=${encodeURIComponent(topic)}&num_questions=5`,
    { headers }
  );
  const quiz = await quizResponse.json();

  // User answers questions...
  const answers = ["B", "A", "C", "D", "B"];

  // Submit
  const submitResponse = await fetch(`${BASE_URL}/adaptive/quiz/submit`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      quiz_id: quiz.quiz_id,
      answers,
      time_spent_seconds: 225
    })
  });
  return await submitResponse.json();
}

// Usage
(async () => {
  const onboarding = await completeOnboarding();
  console.log("Onboarding complete:", onboarding);

  const journey = await getJourney();
  console.log("Journey topics:", journey.journey.length);

  const results = await takeQuiz("Python Functions");
  console.log(`Score: ${results.score}/${results.total}`);
})();
```

### cURL

```bash
# Set user key
USER_KEY="user_1234567890_abc123xyz"

# Onboarding
curl -X POST http://localhost:4465/adaptive/onboarding \
  -H "Content-Type: application/json" \
  -H "x-user-key: $USER_KEY" \
  -d '{
    "interests": ["Python Programming"],
    "learning_goals": ["career_change"],
    "time_commitment": 10,
    "learning_style": "visual",
    "skill_level": "beginner"
  }'

# Get journey
curl -X GET http://localhost:4465/adaptive/journey \
  -H "x-user-key: $USER_KEY"

# Generate quiz
curl -X GET "http://localhost:4465/adaptive/quiz/generate?topic=Python%20Functions&num_questions=5" \
  -H "x-user-key: $USER_KEY"

# Submit quiz (save quiz_id from previous response)
curl -X POST http://localhost:4465/adaptive/quiz/submit \
  -H "Content-Type: application/json" \
  -H "x-user-key: $USER_KEY" \
  -d '{
    "quiz_id": "quiz_1729336200_abc123",
    "answers": ["B", "A", "C", "D", "B"],
    "time_spent_seconds": 225
  }'

# Get recommendations
curl -X GET http://localhost:4465/adaptive/recommendations \
  -H "x-user-key: $USER_KEY"

# Get mastery overview
curl -X GET http://localhost:4465/adaptive/mastery \
  -H "x-user-key: $USER_KEY"
```

---

## Additional Resources

- **Interactive Docs**: http://localhost:4465/docs
- **Database Guide**: [DATABASE.md](DATABASE.md)
- **Agent Development**: [AGENT_DEVELOPMENT.md](AGENT_DEVELOPMENT.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Last Updated**: October 19, 2025
**API Version**: 1.0.0
