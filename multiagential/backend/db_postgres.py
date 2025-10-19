"""
PostgreSQL database operations for Adaptive Learning Platform
Uses SQLAlchemy ORM with async support
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import create_engine, select, update, delete, and_, desc, func
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from db_models import (
    Base, User, UserProfile, Progress, TopicMastery, QuizHistory,
    LearningJourney, CourseEnrollment, ModuleProgress, Quiz,
    AgentDecision, EngagementMetrics
)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://adaptive_user:adaptive_pass@localhost:5432/adaptive_learning")

# Create engine
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized with all tables")


@contextmanager
def get_db():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# ==================== USER MANAGEMENT ====================

def create_user(user_id: str):
    """Create a new user"""
    with get_db() as db:
        user = User(id=user_id)
        db.add(user)


def get_user(user_id: str) -> bool:
    """Check if user exists"""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        return user is not None


# ==================== USER PROFILE ====================

def create_user_profile(user_id: str, profile_data: Dict):
    """
    Create user profile from onboarding
    Called by Learner Profiler Agent
    """
    with get_db() as db:
        profile = UserProfile(
            user_id=user_id,
            interests=profile_data.get("interests", []),
            skill_level=profile_data.get("skill_level", "beginner"),
            learning_goals=profile_data.get("learning_goals", []),
            time_commitment=profile_data.get("time_commitment", 5),
            learning_style=profile_data.get("learning_style", "mixed")
        )
        db.add(profile)


def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile"""
    with get_db() as db:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return None

        return {
            "user_id": profile.user_id,
            "interests": profile.interests,
            "skill_level": profile.skill_level,
            "learning_goals": profile.learning_goals,
            "time_commitment": profile.time_commitment,
            "learning_style": profile.learning_style
        }


def update_user_profile(user_id: str, updates: Dict):
    """Update user profile"""
    with get_db() as db:
        db.query(UserProfile).filter(UserProfile.user_id == user_id).update(updates)


# ==================== PROGRESS TRACKING ====================

def update_progress(user_id: str, topic: str):
    """Update user's current topic"""
    with get_db() as db:
        progress = db.query(Progress).filter(Progress.user_id == user_id).first()
        if progress:
            progress.current_topic = topic
            progress.updated_at = datetime.now()
        else:
            progress = Progress(user_id=user_id, current_topic=topic)
            db.add(progress)


def get_progress(user_id: str) -> Optional[str]:
    """Get user's current topic"""
    with get_db() as db:
        progress = db.query(Progress).filter(Progress.user_id == user_id).first()
        return progress.current_topic if progress else None


# ==================== TOPIC MASTERY ====================

def update_topic_mastery(user_id: str, topic: str, score: float, difficulty: str = "medium"):
    """
    Update topic mastery based on quiz performance
    Called by Performance Analyzer Agent
    """
    with get_db() as db:
        mastery = db.query(TopicMastery).filter(
            and_(TopicMastery.user_id == user_id, TopicMastery.topic == topic)
        ).first()

        if mastery:
            # Update existing mastery with weighted average
            old_score = mastery.mastery_score
            attempts = mastery.attempts
            # Weighted: give more weight to recent performance
            new_score = (old_score * attempts + score * 2) / (attempts + 2)
            mastery.mastery_score = min(100, new_score)
            mastery.attempts += 1
            mastery.last_attempted = datetime.now()

            # Update skill level based on mastery
            if mastery.mastery_score >= 80:
                mastery.skill_level = "advanced"
            elif mastery.mastery_score >= 50:
                mastery.skill_level = "intermediate"
            else:
                mastery.skill_level = "beginner"
        else:
            # Create new mastery record
            skill_level = "advanced" if score >= 80 else "intermediate" if score >= 50 else "beginner"
            mastery = TopicMastery(
                user_id=user_id,
                topic=topic,
                skill_level=skill_level,
                mastery_score=score,
                attempts=1,
                last_attempted=datetime.now()
            )
            db.add(mastery)


def get_topic_mastery(user_id: str, topic: str) -> Optional[Dict]:
    """Get mastery level for a specific topic"""
    with get_db() as db:
        mastery = db.query(TopicMastery).filter(
            and_(TopicMastery.user_id == user_id, TopicMastery.topic == topic)
        ).first()

        if not mastery:
            return None

        return {
            "topic": mastery.topic,
            "skill_level": mastery.skill_level,
            "mastery_score": mastery.mastery_score,
            "attempts": mastery.attempts,
            "last_attempted": mastery.last_attempted.isoformat() if mastery.last_attempted else None
        }


def get_all_topic_mastery(user_id: str) -> List[Dict]:
    """Get all topic mastery records for a user"""
    with get_db() as db:
        masteries = db.query(TopicMastery).filter(TopicMastery.user_id == user_id).all()
        return [
            {
                "topic": m.topic,
                "skill_level": m.skill_level,
                "mastery_score": m.mastery_score,
                "attempts": m.attempts,
                "quizzes_taken": m.attempts  # Frontend expects this field
            }
            for m in masteries
        ]


# ==================== QUIZ HISTORY ====================

def store_quiz_history(user_id: str, quiz_data: Dict):
    """
    Store quiz performance history
    Called after quiz submission by Performance Analyzer
    """
    with get_db() as db:
        history = QuizHistory(
            id=quiz_data.get("quiz_id"),
            user_id=user_id,
            topic=quiz_data.get("topic"),
            difficulty=quiz_data.get("difficulty", "medium"),
            score=quiz_data.get("score"),
            total_questions=quiz_data.get("total_questions"),
            time_spent=quiz_data.get("time_spent", 0),
            questions_data=quiz_data.get("questions_data", {})
        )
        db.add(history)


def get_quiz_history(user_id: str, topic: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Get quiz history for a user"""
    with get_db() as db:
        query = db.query(QuizHistory).filter(QuizHistory.user_id == user_id)

        if topic:
            query = query.filter(QuizHistory.topic == topic)

        quizzes = query.order_by(desc(QuizHistory.completed_at)).limit(limit).all()

        return [
            {
                "quiz_id": q.id,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "score": q.score,
                "total_questions": q.total_questions,
                "percentage": (q.score / q.total_questions * 100) if q.total_questions > 0 else 0,
                "time_spent": q.time_spent,
                "completed_at": q.completed_at.isoformat()
            }
            for q in quizzes
        ]


# ==================== LEARNING JOURNEY ====================

def create_learning_journey(user_id: str, journey_data: List[Dict]):
    """
    Create personalized learning journey
    Called by Journey Architect Agent
    """
    with get_db() as db:
        # Clear existing journey
        db.query(LearningJourney).filter(LearningJourney.user_id == user_id).delete()

        # Create new journey
        for item in journey_data:
            journey_item = LearningJourney(
                user_id=user_id,
                topic=item["topic"],
                position=item["position"],
                status=item.get("status", "locked"),
                unlock_conditions=item.get("unlock_conditions", {}),
                description=item.get("description", ""),
                estimated_hours=item.get("estimated_hours", 10),
                prerequisites=item.get("prerequisites", []),
                agent_reasoning=item.get("reasoning", "")
            )
            db.add(journey_item)


def get_learning_journey(user_id: str) -> List[Dict]:
    """Get user's learning journey"""
    print(f"🗄️  DATABASE: Querying learning_journeys for user_id={user_id}")

    with get_db() as db:
        journey = db.query(LearningJourney).filter(
            LearningJourney.user_id == user_id
        ).order_by(LearningJourney.position).all()

        print(f"🗄️  DATABASE: Found {len(journey)} journey items")

        result = [
            {
                "topic": j.topic,
                "description": j.description or "",
                "estimated_hours": j.estimated_hours or 10,
                "prerequisites": j.prerequisites or [],
                "position": j.position,
                "status": j.status,
                "unlock_conditions": j.unlock_conditions,
                "reasoning": j.agent_reasoning,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None
            }
            for j in journey
        ]

        if result:
            print(f"🗄️  DATABASE: Returning journey with topics:")
            for item in result:
                print(f"    Position {item['position']}: {item['topic']}")
        else:
            print(f"🗄️  DATABASE: No journey found for this user")

        return result


def update_journey_status(user_id: str, topic: str, status: str):
    """Update status of a journey item"""
    with get_db() as db:
        journey_item = db.query(LearningJourney).filter(
            and_(LearningJourney.user_id == user_id, LearningJourney.topic == topic)
        ).first()

        if journey_item:
            journey_item.status = status
            if status == "in_progress" and not journey_item.started_at:
                journey_item.started_at = datetime.now()
            elif status == "completed":
                journey_item.completed_at = datetime.now()


# ==================== AGENT DECISIONS (Audit Log) ====================

def log_agent_decision(user_id: str, agent_name: str, decision_type: str,
                       input_data: Dict, output_data: Dict, reasoning: str = "",
                       confidence: float = None):
    """
    Log agent decision for transparency and debugging
    """
    with get_db() as db:
        decision = AgentDecision(
            user_id=user_id,
            agent_name=agent_name,
            decision_type=decision_type,
            input_data=input_data,
            output_data=output_data,
            reasoning=reasoning,
            confidence=confidence
        )
        db.add(decision)


def get_agent_decisions(user_id: str, agent_name: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """Get agent decision history"""
    with get_db() as db:
        query = db.query(AgentDecision).filter(AgentDecision.user_id == user_id)

        if agent_name:
            query = query.filter(AgentDecision.agent_name == agent_name)

        decisions = query.order_by(desc(AgentDecision.created_at)).limit(limit).all()

        return [
            {
                "agent_name": d.agent_name,
                "decision_type": d.decision_type,
                "reasoning": d.reasoning,
                "confidence": d.confidence,
                "created_at": d.created_at.isoformat()
            }
            for d in decisions
        ]


# ==================== QUIZ STORAGE (Temporary) ====================

def store_quiz(quiz_id: str, questions: List[Dict]):
    """Store quiz temporarily"""
    with get_db() as db:
        quiz = Quiz(id=quiz_id, questions=questions)
        db.add(quiz)


def get_quiz(quiz_id: str) -> Optional[List[Dict]]:
    """Retrieve quiz"""
    with get_db() as db:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        return quiz.questions if quiz else None


def delete_quiz(quiz_id: str):
    """Delete quiz"""
    with get_db() as db:
        db.query(Quiz).filter(Quiz.id == quiz_id).delete()


# ==================== COURSE MANAGEMENT (Existing) ====================

def enroll_user_in_course(user_id: str, course_id: str):
    """Enroll user in course"""
    with get_db() as db:
        enrollment = CourseEnrollment(user_id=user_id, course_id=course_id)
        db.merge(enrollment)


def update_course_access(user_id: str, course_id: str, module_id: Optional[str] = None):
    """Update course access time"""
    with get_db() as db:
        enrollment = db.query(CourseEnrollment).filter(
            and_(CourseEnrollment.user_id == user_id, CourseEnrollment.course_id == course_id)
        ).first()

        if enrollment:
            enrollment.last_accessed = datetime.now()
            if module_id:
                enrollment.last_module_id = module_id


def get_user_enrollments(user_id: str) -> List[Dict]:
    """Get user's course enrollments"""
    with get_db() as db:
        enrollments = db.query(CourseEnrollment).filter(
            CourseEnrollment.user_id == user_id
        ).order_by(desc(CourseEnrollment.last_accessed)).all()

        return [
            {
                "course_id": e.course_id,
                "enrolled_at": e.enrolled_at.isoformat(),
                "last_accessed": e.last_accessed.isoformat(),
                "last_module_id": e.last_module_id
            }
            for e in enrollments
        ]


def update_module_progress(user_id: str, course_id: str, module_id: str, completed: bool):
    """Update module progress"""
    with get_db() as db:
        progress = db.query(ModuleProgress).filter(
            and_(
                ModuleProgress.user_id == user_id,
                ModuleProgress.course_id == course_id,
                ModuleProgress.module_id == module_id
            )
        ).first()

        if progress:
            progress.completed = completed
            if completed:
                progress.completed_at = datetime.now()
        else:
            progress = ModuleProgress(
                user_id=user_id,
                course_id=course_id,
                module_id=module_id,
                completed=completed,
                completed_at=datetime.now() if completed else None
            )
            db.add(progress)


def get_course_progress(user_id: str, course_id: str) -> Dict[str, bool]:
    """Get module completion status for a course"""
    with get_db() as db:
        progress_records = db.query(ModuleProgress).filter(
            and_(ModuleProgress.user_id == user_id, ModuleProgress.course_id == course_id)
        ).all()

        return {p.module_id: p.completed for p in progress_records}


def get_user_course_summary(user_id: str) -> Dict:
    """Get summary of user's course activity"""
    with get_db() as db:
        # Total enrollments
        total_enrollments = db.query(func.count(CourseEnrollment.course_id)).filter(
            CourseEnrollment.user_id == user_id
        ).scalar()

        # Completed modules
        completed_modules = db.query(func.count(ModuleProgress.module_id)).filter(
            and_(ModuleProgress.user_id == user_id, ModuleProgress.completed == True)
        ).scalar()

        # Recent course
        recent = db.query(CourseEnrollment).filter(
            CourseEnrollment.user_id == user_id
        ).order_by(desc(CourseEnrollment.last_accessed)).first()

        return {
            "total_enrollments": total_enrollments or 0,
            "completed_modules": completed_modules or 0,
            "recent_course_id": recent.course_id if recent else None,
            "recent_module_id": recent.last_module_id if recent else None
        }
