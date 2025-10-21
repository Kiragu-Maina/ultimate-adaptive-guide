# FastAPI backend for AI-Powered Adaptive Learning Mentor
import os
import uuid
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

from content_graph import create_content_graph
# import database  # Old SQLite database - replaced with PostgreSQL
from adaptive_orchestrator import (
    orchestrate_onboarding,
    orchestrate_content_delivery
)
import db_postgres as db_pg
import cache_redis as cache
from quiz_generator_agent import create_quiz_generator_graph
from feedback_agent import create_feedback_graph
from performance_analyzer_agent import analyze_performance
from job_queue import (
    JobQueue, JobStatus, start_job_worker, stop_job_worker,
    register_job_processor
)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def startup_event():
    db_pg.init_db()
    # Start background job worker
    start_job_worker()
    print("✅ Background job worker started")


@app.on_event("shutdown")
async def shutdown_event():
    # Stop background job worker
    stop_job_worker()
    print("✅ Background job worker stopped")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-User-Key"],
)

# --- User Handling ---
async def get_user_key(request: Request, response: Response):
    print("\n" + "="*60)
    print("🔍 USER IDENTIFICATION FLOW")
    print("="*60)

    # Try to get user ID from multiple sources (for backwards compatibility)
    user_key = request.headers.get("x-user-key")
    print(f"📥 Checking x-user-key header: {user_key}")

    if not user_key:
        # Fallback: check query params (e.g., ?user_id=xxx)
        user_key = request.query_params.get("user_id")
        print(f"📥 Checking query param user_id: {user_key}")

    if not user_key:
        # No user ID found - generate new one
        user_key = str(uuid.uuid4())
        response.headers["X-User-Key"] = user_key
        print(f"🆕 Generated new user_key: {user_key}")
    else:
        print(f"✅ Using existing user_key: {user_key}")

    existing_user = db_pg.get_user(user_key)
    if not existing_user:
        db_pg.create_user(user_key)
        print(f"👤 Created new user in database: {user_key}")
    else:
        print(f"👤 Found existing user in database: {user_key}")

    print("="*60 + "\n")
    return user_key

# --- Models ---
class QuizQuestionForClient(BaseModel):
    question: str
    options: List[str]

class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[QuizQuestionForClient]

class QuizSubmission(BaseModel):
    quiz_id: str
    answers: List[str]

class FeedbackRequest(BaseModel):
    user_input: str

class ContentResponse(BaseModel):
    content: str
    exercises: List[str]
    resources: List[Dict]
    diagram: str

class ProgressResponse(BaseModel):
    current_topic: Optional[str]

class MermaidInteractionRequest(BaseModel):
    mermaid_diagram_content: str
    hovered_item: str

class ContentCompleteRequest(BaseModel):
    topic: str

class OnboardingRequest(BaseModel):
    interests: List[str]
    learning_goals: List[str]
    time_commitment: int
    learning_style: str
    skill_level: str
    background: Optional[str] = None

class OnboardingResponse(BaseModel):
    learner_profile: Dict
    learning_journey: List[Dict]
    agent_activity: List[Dict]
    message: str


class JobResponse(BaseModel):
    """Response for async job submission"""
    job_id: str
    status: str
    message: str
    poll_url: str


class JobStatusResponse(BaseModel):
    """Response for job status polling"""
    job_id: str
    status: str
    progress: int
    created_at: str
    updated_at: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress_message: Optional[str] = None

# --- Graphs ---
content_graph = create_content_graph()


# --- Job Processors ---
# Register async job processors that run in background

@register_job_processor("onboarding")
def process_onboarding_job(params, job_id):
    """
    Process onboarding in background

    Args:
        params: {user_key, onboarding_data}
        job_id: Job identifier for progress tracking
    """
    user_key = params["user_key"]
    onboarding_data = params["onboarding_data"]

    print(f"\n{'='*60}")
    print(f"🎓 PROCESSING ONBOARDING JOB: {job_id}")
    print(f"{'='*60}")
    print(f"👤 User: {user_key}")
    print(f"📚 Interests: {onboarding_data['interests']}")

    try:
        # Update progress
        JobQueue.update_job_progress(job_id, 20, "Running Learner Profiler Agent...")

        # Orchestrate multi-agent onboarding
        result = orchestrate_onboarding(user_key, onboarding_data)

        # Update progress
        JobQueue.update_job_progress(job_id, 90, "Finalizing learning journey...")

        journey_count = len(result["learning_journey"])
        print(f"✅ Journey created with {journey_count} topics")
        print(f"{'='*60}\n")

        return {
            "learner_profile": result["learner_profile"],
            "learning_journey": result["learning_journey"],
            "agent_activity": result["agent_activity"],
            "message": "Your personalized learning journey has been created by our AI agents!"
        }

    except Exception as e:
        print(f"❌ Onboarding job failed: {str(e)}")
        raise


@register_job_processor("content_generation")
def process_content_generation_job(params, job_id):
    """
    Process content generation in background

    Args:
        params: {user_key, topic}
        job_id: Job identifier for progress tracking
    """
    user_key = params["user_key"]
    topic = params["topic"]

    print(f"\n{'='*60}")
    print(f"📚 PROCESSING CONTENT GENERATION JOB: {job_id}")
    print(f"{'='*60}")
    print(f"👤 User: {user_key}")
    print(f"📖 Topic: {topic}")

    try:
        # Update progress
        JobQueue.update_job_progress(job_id, 20, "Preparing content generation...")

        # Orchestrate content delivery
        result = orchestrate_content_delivery(user_key, topic)

        # Update progress
        JobQueue.update_job_progress(job_id, 90, "Finalizing content...")

        print(f"✅ Content generated for topic: {topic}")
        print(f"{'='*60}\n")

        return {
            "content": result["content"],
            "exercises": result.get("exercises", []),
            "resources": result.get("resources", []),
            "diagram": result.get("diagram", ""),
            "agent_activity": result.get("agent_activity", [])
        }

    except Exception as e:
        print(f"❌ Content generation job failed: {str(e)}")
        raise

# --- Endpoints ---

@app.get("/adaptive/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of an async job

    Poll this endpoint to check job progress and retrieve results
    when status is 'completed'
    """
    job_data = JobQueue.get_job_status(job_id)

    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job_data["job_id"],
        status=job_data["status"],
        progress=job_data.get("progress", 0),
        created_at=job_data["created_at"],
        updated_at=job_data["updated_at"],
        result=job_data.get("result"),
        error=job_data.get("error"),
        progress_message=job_data.get("progress_message")
    )


@app.post("/adaptive/onboarding", response_model=JobResponse, status_code=202)
@limiter.limit("10/minute")
async def adaptive_onboarding(request: Request, response: Response, req: OnboardingRequest):
    """
    🤖 MULTI-AGENT WORKFLOW: Onboarding (Async)

    Orchestrates Learner Profiler Agent → Journey Architect Agent
    to create a personalized learning experience.

    Returns immediately with a job_id. Poll /adaptive/jobs/{job_id}
    to get progress and results.

    This endpoint showcases agent collaboration!
    """
    user_key = await get_user_key(request, response)

    print("\n" + "="*60)
    print("🎓 ONBOARDING ENDPOINT (ASYNC)")
    print("="*60)
    print(f"👤 Creating learning journey for user: {user_key}")
    print(f"📚 Interests: {req.interests}")
    print(f"🎯 Goals: {req.learning_goals}")
    print(f"⏱️  Time commitment: {req.time_commitment}h/week")

    # Prepare onboarding data
    onboarding_data = {
        "interests": req.interests,
        "learning_goals": req.learning_goals,
        "time_commitment": req.time_commitment,
        "learning_style": req.learning_style,
        "skill_level": req.skill_level,
        "background": req.background
    }

    # Create async job
    job_id = JobQueue.create_job("onboarding", {
        "user_key": user_key,
        "onboarding_data": onboarding_data
    })

    print(f"✅ Job created: {job_id}")
    print("="*60 + "\n")

    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Onboarding job created. Poll /adaptive/jobs/{job_id} for status.",
        poll_url=f"/adaptive/jobs/{job_id}"
    )


@app.get("/adaptive/journey")
@limiter.limit("30/minute")
async def get_adaptive_journey(request: Request, response: Response):
    """
    Gets the user's personalized learning journey (with caching).
    """
    user_key = await get_user_key(request, response)

    print("\n" + "="*60)
    print("🗺️  JOURNEY ENDPOINT")
    print("="*60)
    print(f"📍 Fetching journey for user: {user_key}")

    try:
        # Try cache first
        print("💾 Checking cache...")
        cached_journey = cache.get_cached_learning_journey(user_key)
        if cached_journey:
            print(f"✅ Cache HIT! Found {len(cached_journey)} topics in cache")
            print("="*60 + "\n")
            return {
                "journey": cached_journey,
                "total_topics": len(cached_journey),
                "completed": len([t for t in cached_journey if t["status"] == "completed"]),
                "in_progress": len([t for t in cached_journey if t["status"] == "in_progress"]),
                "cached": True
            }

        # Cache miss - get from database
        print("❌ Cache MISS - querying database...")
        journey = db_pg.get_learning_journey(user_key)

        if not journey:
            print("⚠️  No journey found in database for this user")
            print("💡 User needs to complete onboarding first")
            print("="*60 + "\n")
            return {"journey": [], "message": "Complete onboarding to get your personalized journey"}

        # Cache the result
        print(f"✅ Found {len(journey)} topics in database")
        print(f"📊 Journey summary:")
        for topic in journey:
            print(f"   - {topic['topic']} (status: {topic['status']})")

        cache.set_cached_learning_journey(user_key, journey)
        print("💾 Cached journey for future requests")
        print("="*60 + "\n")

        return {
            "journey": journey,
            "total_topics": len(journey),
            "completed": len([t for t in journey if t["status"] == "completed"]),
            "in_progress": len([t for t in journey if t["status"] == "in_progress"]),
            "cached": False
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Failed to get journey: {str(e)}")


@app.get("/adaptive/recommendations")
@limiter.limit("20/minute")
async def get_adaptive_recommendations(request: Request, response: Response):
    """
    🤖 MULTI-AGENT WORKFLOW: Smart Recommendations (with caching)

    Uses Recommendation Agent coordinating with:
    - Learner Profiler (for context)
    - Performance Analyzer (for performance data)
    - Journey Architect (for journey state)
    """
    user_key = await get_user_key(request, response)

    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS ENDPOINT")
    print("="*60)
    print(f"📍 Generating recommendations for user: {user_key}")

    try:
        # Try cache first
        print("💾 Checking cache...")
        cached_recs = cache.get_cached_recommendations(user_key)
        if cached_recs:
            print(f"✅ Cache HIT! Returning cached recommendations")
            print("="*60 + "\n")
            return {
                **cached_recs,
                "cached": True
            }

        print("❌ Cache MISS - generating recommendations...")

        from recommendation_agent import generate_recommendations

        # Get required data (with caching where applicable)
        print("📊 Fetching user data...")
        profile = cache.get_cached_learner_profile(user_key) or db_pg.get_user_profile(user_key)
        journey = cache.get_cached_learning_journey(user_key) or db_pg.get_learning_journey(user_key)
        quiz_history = db_pg.get_quiz_history(user_key, limit=20)

        print(f"   - Profile: {'Found' if profile else 'None'}")
        print(f"   - Journey: {len(journey) if journey else 0} topics")
        print(f"   - Quiz history: {len(quiz_history) if quiz_history else 0} quizzes")

        if not profile or not journey:
            print("⚠️  Missing profile or journey - user needs onboarding")
            print("="*60 + "\n")
            return {"recommendations": [], "message": "Complete onboarding first"}

        # Get mastery data
        all_mastery = cache.get_cached_topic_mastery(user_key) or db_pg.get_all_topic_mastery(user_key)
        topic_mastery = {m["topic"]: m for m in all_mastery}

        # Simple performance analysis for recommendations
        from performance_analyzer_agent import analyze_performance
        performance = analyze_performance(user_key, quiz_history, topic_mastery) if quiz_history else {
            "strengths": [],
            "knowledge_gaps": [],
            "performance_summary": "No quiz data yet"
        }

        # Generate recommendations
        recommendations = generate_recommendations(
            user_key,
            profile,
            performance,
            journey
        )

        # Cache the result
        cache.set_cached_recommendations(user_key, recommendations)

        print(f"✅ Generated {len(recommendations['recommendations'])} recommendations")
        print("💾 Cached for future requests")
        print("="*60 + "\n")

        return {
            "recommendations": recommendations["recommendations"],
            "reasoning": recommendations["reasoning"],
            "confidence": recommendations["confidence"],
            "cached": False
        }

    except Exception as e:
        import traceback
        print(f"❌ ERROR generating recommendations:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@app.get("/adaptive/content", response_model=JobResponse, status_code=202)
@limiter.limit("20/minute")
async def get_adaptive_content(request: Request, response: Response, topic: str):
    """
    🤖 MULTI-AGENT WORKFLOW: Adaptive Content Delivery (Async)

    Orchestrates Performance Analyzer → Content Personalizer → Diagram Generator
    to deliver content at the right difficulty level.

    Returns immediately with a job_id. Poll /adaptive/jobs/{job_id}
    to get progress and results.
    """
    user_key = await get_user_key(request, response)

    print("\n" + "="*60)
    print("📚 CONTENT DELIVERY ENDPOINT (ASYNC)")
    print("="*60)
    print(f"👤 User: {user_key}")
    print(f"📖 Topic: {topic}")

    # Create async job
    job_id = JobQueue.create_job("content_generation", {
        "user_key": user_key,
        "topic": topic
    })

    print(f"✅ Job created: {job_id}")
    print("="*60 + "\n")

    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Content generation job created. Poll /adaptive/jobs/{job_id} for status.",
        poll_url=f"/adaptive/jobs/{job_id}"
    )


@app.post("/adaptive/content/complete")
@limiter.limit("30/minute")
async def mark_content_complete(request: Request, response: Response, req: ContentCompleteRequest):
    """
    Marks a topic as complete for the user.
    """
    user_key = await get_user_key(request, response)

    try:
        # Update journey status in the database
        db_pg.update_journey_status(user_key, req.topic, "completed")

        # Invalidate all caches for the user to ensure fresh data
        cache.invalidate_user_cache(user_key)

        return {"message": f"Topic '{req.topic}' marked as complete."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark content as complete: {str(e)}")


@app.get("/adaptive/performance")
@limiter.limit("20/minute")
async def get_performance_analysis(request: Request, response: Response):
    """
    🤖 AGENT: Performance Analyzer

    Provides detailed performance analysis including:
    - Topic mastery scores
    - Knowledge gaps
    - Strengths
    - Learning velocity
    """
    user_key = await get_user_key(request, response)

    try:
        from performance_analyzer_agent import analyze_performance

        # Get data
        quiz_history = db_pg.get_quiz_history(user_key, limit=20)
        all_mastery = db_pg.get_all_topic_mastery(user_key)
        topic_mastery = {m["topic"]: m for m in all_mastery}

        if not quiz_history:
            return {
                "message": "Take some quizzes to see your performance analysis",
                "mastery": {},
                "summary": "No data yet"
            }

        # Analyze performance
        analysis = analyze_performance(user_key, quiz_history, topic_mastery)

        return {
            "mastery_updates": analysis["mastery_updates"],
            "knowledge_gaps": analysis["knowledge_gaps"],
            "strengths": analysis["strengths"],
            "difficulty_recommendations": analysis["difficulty_recommendations"],
            "performance_summary": analysis["performance_summary"],
            "confidence": analysis["confidence"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze performance: {str(e)}")


@app.get("/adaptive/agent-decisions")
@limiter.limit("20/minute")
async def get_agent_decisions(request: Request, response: Response, agent_name: Optional[str] = None):
    """
    🔍 TRANSPARENCY: Agent Decision Log

    Shows all decisions made by adaptive agents for this user.
    Demonstrates the multi-agent reasoning process.
    """
    user_key = await get_user_key(request, response)

    try:
        decisions = db_pg.get_agent_decisions(user_key, agent_name, limit=20)

        return {
            "decisions": decisions,
            "total": len(decisions),
            "agents": list(set(d["agent_name"] for d in decisions))
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent decisions: {str(e)}")


@app.get("/adaptive/profile")
@limiter.limit("30/minute")
async def get_learner_profile(request: Request, response: Response):
    """
    👤 Get Learner Profile

    Returns the user's complete learner profile including interests,
    skill level, learning goals, and preferences.
    """
    user_key = await get_user_key(request, response)

    try:
        profile = db_pg.get_user_profile(user_key)

        if not profile:
            return {
                "message": "No profile found. Please complete onboarding first.",
                "profile": None
            }

        return {
            "profile": profile,
            "user_id": user_key
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@app.get("/adaptive/quiz")
@limiter.limit("10/minute")
async def generate_quiz(request: Request, response: Response, topic: str, num_questions: int = 5):
    """
    🧪 Generate Adaptive Quiz

    Creates a difficulty-appropriate quiz based on user's skill level and performance.
    Uses Quiz Generator Agent.
    """
    user_key = await get_user_key(request, response)

    print("\n" + "="*60)
    print("🧪 QUIZ GENERATION ENDPOINT")
    print("="*60)
    print(f"👤 User: {user_key}")
    print(f"📚 Topic: {topic}")
    print(f"❓ Number of questions: {num_questions}")

    try:
        # Get user's skill level from profile or performance
        print("📊 Determining difficulty level...")
        profile = db_pg.get_user_profile(user_key)
        skill_level = profile.get("skill_level", "beginner") if profile else "beginner"
        print(f"   Profile skill level: {skill_level}")

        # Check topic mastery to adjust difficulty
        mastery = db_pg.get_topic_mastery(user_key, topic)
        if mastery:
            print(f"   Topic mastery: {mastery.get('mastery_score', 0):.1f}%")

        if mastery and mastery.get("mastery_score", 0) >= 80:
            skill_level = "advanced"
        elif mastery and mastery.get("mastery_score", 0) >= 50:
            skill_level = "intermediate"

        print(f"   Final difficulty: {skill_level}")

        # Generate quiz using Quiz Generator Agent
        print("🤖 Generating quiz with Quiz Generator Agent...")
        quiz_graph = create_quiz_generator_graph()
        result = quiz_graph.invoke({
            "topic": topic,
            "user_id": user_key,
            "skill_level": skill_level,
            "num_questions": num_questions
        })

        num_questions_generated = len(result.get('questions', []))
        print(f"✅ Generated {num_questions_generated} questions")

        # Validate we actually got questions
        if num_questions_generated == 0:
            print(f"❌ ERROR: Quiz generation failed - 0 questions generated")
            print("="*60 + "\n")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate quiz questions. The LLM might be experiencing issues. Please try again."
            )

        # Store quiz ID for submission tracking
        quiz_id = str(uuid.uuid4())

        # Log agent decision
        db_pg.log_agent_decision(
            user_id=user_key,
            agent_name="quiz_generator",
            decision_type="quiz_generated",
            input_data={"topic": topic, "skill_level": skill_level},
            output_data={"num_questions": len(result["questions"]), "difficulty": result["difficulty"]},
            reasoning=f"Generated {skill_level}-level quiz on {topic}"
        )

        # Cache quiz for submission validation
        print("💾 Caching quiz for submission tracking...")
        cache.cache_quiz(quiz_id, {
            "topic": topic,
            "questions": result["questions"],
            "difficulty": result["difficulty"],
            "user_id": user_key
        })

        print(f"✅ Quiz generated successfully! ID: {quiz_id}")
        print("="*60 + "\n")

        return {
            "quiz_id": quiz_id,
            "topic": topic,
            "difficulty": result["difficulty"],
            "questions": [
                {
                    "question": q["question"],
                    "options": q["options"]
                } for q in result["questions"]
            ],
            "num_questions": len(result["questions"])
        }

    except Exception as e:
        import traceback
        print(f"❌ ERROR generating quiz:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@app.post("/adaptive/quiz/submit")
@limiter.limit("15/minute")
async def submit_quiz(request: Request, response: Response, submission: QuizSubmission):
    """
    ✅ Submit Quiz Answers

    Processes quiz answers, calculates score, updates mastery tracking,
    and triggers Performance Analyzer.
    """
    user_key = await get_user_key(request, response)

    print("\n" + "="*60)
    print("📝 QUIZ SUBMIT ENDPOINT")
    print("="*60)
    print(f"👤 User: {user_key}")
    print(f"🆔 Quiz ID: {submission.quiz_id}")
    print(f"📊 Answers submitted: {len(submission.answers)}")

    try:
        # Get cached quiz
        print("💾 Fetching quiz from cache...")
        quiz_data = cache.get_cached_quiz(submission.quiz_id)

        if not quiz_data:
            print("❌ Quiz not found in cache!")
            print("="*60 + "\n")
            raise HTTPException(status_code=404, detail="Quiz not found or expired")

        print(f"✅ Quiz found - Topic: {quiz_data.get('topic')}")
        print(f"   User ID in quiz: {quiz_data.get('user_id')}")
        print(f"   Questions: {len(quiz_data.get('questions', []))}")

        if quiz_data["user_id"] != user_key:
            print(f"❌ User mismatch! Quiz belongs to {quiz_data['user_id']}, not {user_key}")
            print("="*60 + "\n")
            raise HTTPException(status_code=403, detail="Quiz does not belong to this user")

        # Calculate score
        print("🧮 Calculating score...")
        questions = quiz_data["questions"]
        correct = 0
        total = len(questions)
        results = []

        for i, (question, user_answer) in enumerate(zip(questions, submission.answers)):
            is_correct = user_answer == question["answer"]
            if is_correct:
                correct += 1

            results.append({
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": question["answer"],
                "is_correct": is_correct,
                "explanation": question.get("explanation", "")
            })

        score_percent = (correct / total * 100) if total > 0 else 0
        print(f"📊 Score: {correct}/{total} ({score_percent:.1f}%)")

        # Update quiz history
        print("💾 Saving quiz result to database...")
        db_pg.store_quiz_history(
            user_id=user_key,
            quiz_data={
                "quiz_id": submission.quiz_id,
                "topic": quiz_data["topic"],
                "difficulty": quiz_data["difficulty"],
                "score": correct,
                "total_questions": total,
                "time_spent": 0,  # TODO: Track actual time
                "questions_data": results
            }
        )
        print("✅ Quiz result saved")

        # Update topic mastery
        print("📈 Updating topic mastery...")
        current_mastery = db_pg.get_topic_mastery(user_key, quiz_data["topic"])

        if current_mastery:
            print(f"   Previous mastery: {current_mastery['mastery_score']:.1f}%")

        # update_topic_mastery handles weighted averaging internally
        db_pg.update_topic_mastery(
            user_id=user_key,
            topic=quiz_data["topic"],
            score=score_percent,
            difficulty=quiz_data["difficulty"]
        )

        # Get updated mastery to show in logs
        updated_mastery = db_pg.get_topic_mastery(user_key, quiz_data["topic"])
        new_mastery_score = updated_mastery['mastery_score'] if updated_mastery else score_percent
        print(f"   New mastery: {new_mastery_score:.1f}%")
        print("✅ Mastery updated")

        # Get updated performance analysis
        print("🤖 Running performance analysis...")
        quiz_history = db_pg.get_quiz_history(user_key, limit=10)
        all_mastery = db_pg.get_all_topic_mastery(user_key)
        topic_mastery_dict = {m["topic"]: m for m in all_mastery}

        performance_data = analyze_performance(user_key, quiz_history, topic_mastery_dict)
        print(f"   Skill level: {performance_data.get('skill_level', 'beginner')}")

        # Log agent decision
        db_pg.log_agent_decision(
            user_id=user_key,
            agent_name="performance_analyzer",
            decision_type="mastery_updated",
            input_data={"quiz_score": score_percent},
            output_data={"new_mastery": new_mastery_score, "skill_level": performance_data.get("skill_level")},
            reasoning=f"Updated mastery for {quiz_data['topic']} based on quiz performance"
        )

        # Clear cached quiz
        cache.clear_cached_quiz(submission.quiz_id)

        print("✅ Quiz submission complete!")
        print("="*60 + "\n")

        return {
            "score": correct,
            "total": total,
            "percentage": score_percent,
            "results": results,
            "mastery_update": {
                "topic": quiz_data["topic"],
                "previous_mastery": current_mastery["mastery_score"] if current_mastery else 0,
                "new_mastery": new_mastery_score,
                "skill_level": performance_data.get("skill_level", "beginner")
            },
            "performance_insights": {
                "strengths": performance_data.get("strengths", []),
                "knowledge_gaps": performance_data.get("knowledge_gaps", [])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ ERROR submitting quiz:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")


@app.get("/adaptive/mastery")
@limiter.limit("30/minute")
async def get_mastery_scores(request: Request, response: Response):
    """
    📊 Get Mastery Scores

    Returns all topic mastery scores, knowledge gaps, and strengths.
    """
    user_key = await get_user_key(request, response)

    print("\n" + "="*60)
    print("📊 MASTERY ENDPOINT")
    print("="*60)
    print(f"👤 User: {user_key}")

    try:
        # Get mastery data
        print("📚 Fetching mastery data...")
        mastery_data = db_pg.get_all_topic_mastery(user_key)
        print(f"   Found mastery for {len(mastery_data)} topics")

        # Get quiz history
        print("📜 Fetching quiz history...")
        quiz_history = db_pg.get_quiz_history(user_key, limit=20)
        print(f"   Found {len(quiz_history)} quizzes")

        if not quiz_history:
            print("⚠️  No quiz history - returning default response")
            print("="*60 + "\n")
            return {
                "message": "No quiz data yet. Complete some quizzes to see your mastery scores!",
                "mastery": [],
                "strengths": [],
                "knowledge_gaps": [],
                "overall_skill_level": "beginner"
            }

        # Convert mastery list to dict for performance analyzer
        print("🤖 Running performance analysis...")
        topic_mastery_dict = {m["topic"]: m for m in mastery_data}

        # Analyze performance
        performance = analyze_performance(user_key, quiz_history, topic_mastery_dict)

        print(f"   Overall skill level: {performance.get('skill_level', 'beginner')}")
        print(f"   Strengths: {len(performance.get('strengths', []))} topics")
        print(f"   Knowledge gaps: {len(performance.get('knowledge_gaps', []))} topics")

        # Calculate average score
        avg_score = sum(q.get("score", 0) / q.get("total_questions", 1) * 100 for q in quiz_history) / len(quiz_history) if quiz_history else 0
        print(f"   Average score: {avg_score:.1f}%")

        print("✅ Mastery data retrieved successfully")
        print("="*60 + "\n")

        return {
            "mastery": mastery_data,
            "strengths": performance.get("strengths", []),
            "knowledge_gaps": performance.get("knowledge_gaps", []),
            "overall_skill_level": performance.get("skill_level", "beginner"),
            "total_quizzes": len(quiz_history),
            "average_score": avg_score
        }

    except Exception as e:
        import traceback
        print(f"❌ ERROR getting mastery scores:")
        print(traceback.format_exc())
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=f"Failed to get mastery scores: {str(e)}")


@app.post("/adaptive/feedback")
@limiter.limit("20/minute")
async def get_motivational_feedback(request: Request, response: Response, feedback_request: FeedbackRequest):
    """
    💬 Get Motivational Feedback

    Provides context-aware motivational feedback based on user sentiment
    and performance data. Uses Feedback Agent.
    """
    user_key = await get_user_key(request, response)

    try:
        # Get performance context
        quiz_history = db_pg.get_quiz_history(user_key, limit=10)
        performance_context = None

        if quiz_history:
            performance = analyze_performance(user_key, quiz_history)
            recent_quiz = quiz_history[0] if quiz_history else None

            performance_context = {
                "strengths": performance.get("strengths", []),
                "knowledge_gaps": performance.get("knowledge_gaps", []),
                "recent_score": (recent_quiz.get("score", 0) / recent_quiz.get("total", 1) * 100) if recent_quiz else None
            }

        # Generate feedback using Feedback Agent
        feedback_graph = create_feedback_graph()
        result = feedback_graph.invoke({
            "user_input": feedback_request.user_input,
            "performance_context": performance_context
        })

        # Log agent decision
        db_pg.log_agent_decision(
            user_id=user_key,
            agent_name="feedback_agent",
            decision_type="feedback_provided",
            input_data={"user_input": feedback_request.user_input, "sentiment": result["sentiment"]},
            output_data={"feedback_length": len(result["feedback"])},
            reasoning="Provided personalized motivational feedback"
        )

        return {
            "feedback": result["feedback"],
            "sentiment": result["sentiment"],
            "performance_included": performance_context is not None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate feedback: {str(e)}")


# --- Health check ---
@app.get("/")
@limiter.limit("60/minute")
def health(request: Request):
    redis_health = cache.cache_health_check()
    return {
        "status": "ok",
        "adaptive_agents": "online",
        "redis": redis_health.get("status", "unknown"),
        "cache_available": cache.is_redis_available()
    }


@app.get("/health/cache")
@limiter.limit("30/minute")
def cache_health(request: Request):
    """Detailed cache health check"""
    return cache.cache_health_check()

# --- Mermaid Interaction ---
