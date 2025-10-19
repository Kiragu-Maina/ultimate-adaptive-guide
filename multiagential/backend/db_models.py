"""
SQLAlchemy models for the Adaptive Learning Platform
Using PostgreSQL for persistence
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User table"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    progress = relationship("Progress", back_populates="user", uselist=False)
    quiz_history = relationship("QuizHistory", back_populates="user")
    topic_mastery = relationship("TopicMastery", back_populates="user")
    learning_journey = relationship("LearningJourney", back_populates="user")
    course_enrollments = relationship("CourseEnrollment", back_populates="user")
    module_progress = relationship("ModuleProgress", back_populates="user")


class UserProfile(Base):
    """User profile with interests, goals, and learning preferences"""
    __tablename__ = "user_profiles"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    interests = Column(JSON)  # ["Programming", "Data Science", ...]
    skill_level = Column(String)  # "beginner", "intermediate", "advanced"
    learning_goals = Column(JSON)  # ["career_change", "skill_upgrade", ...]
    time_commitment = Column(Integer)  # hours per week
    learning_style = Column(String)  # "visual", "reading", "interactive", "video"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="profile")


class Progress(Base):
    """User progress tracking"""
    __tablename__ = "progress"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    current_topic = Column(String)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="progress")


class TopicMastery(Base):
    """Topic-specific mastery tracking"""
    __tablename__ = "topic_mastery"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    topic = Column(String, primary_key=True)
    skill_level = Column(String)  # "beginner", "intermediate", "advanced"
    mastery_score = Column(Float, default=0.0)  # 0-100
    attempts = Column(Integer, default=0)
    last_attempted = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="topic_mastery")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_mastery', 'user_id', 'mastery_score'),
    )


class QuizHistory(Base):
    """Quiz performance history"""
    __tablename__ = "quiz_history"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    topic = Column(String)
    difficulty = Column(String)  # "easy", "medium", "hard"
    score = Column(Integer)
    total_questions = Column(Integer)
    time_spent = Column(Integer)  # seconds
    questions_data = Column(JSON)  # Detailed question/answer data
    completed_at = Column(DateTime, default=func.now())

    # Relationship
    user = relationship("User", back_populates="quiz_history")

    # Indexes
    __table_args__ = (
        Index('idx_user_topic_quiz', 'user_id', 'topic'),
        Index('idx_completed_at', 'completed_at'),
    )


class LearningJourney(Base):
    """Personalized learning journey/path for each user"""
    __tablename__ = "learning_journeys"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    topic = Column(String, primary_key=True)
    position = Column(Integer)  # Order in the journey
    status = Column(String)  # "locked", "available", "in_progress", "completed", "skipped"
    unlock_conditions = Column(JSON)  # Prerequisites and conditions
    description = Column(Text)  # Description of what this topic covers
    estimated_hours = Column(Integer)  # Estimated time to complete
    prerequisites = Column(JSON)  # List of prerequisite topics
    recommended_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    agent_reasoning = Column(Text)  # Why this was recommended by Journey Architect

    # Relationship
    user = relationship("User", back_populates="learning_journey")

    # Indexes
    __table_args__ = (
        Index('idx_user_position', 'user_id', 'position'),
        Index('idx_status', 'status'),
    )


class CourseEnrollment(Base):
    """Course enrollments"""
    __tablename__ = "course_enrollments"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    course_id = Column(String, primary_key=True)
    enrolled_at = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime, default=func.now())
    last_module_id = Column(String)

    # Relationship
    user = relationship("User", back_populates="course_enrollments")


class ModuleProgress(Base):
    """Module completion tracking"""
    __tablename__ = "module_progress"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    course_id = Column(String, primary_key=True)
    module_id = Column(String, primary_key=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)

    # Relationship
    user = relationship("User", back_populates="module_progress")


class Quiz(Base):
    """Temporary quiz storage"""
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True)
    questions = Column(JSON)
    created_at = Column(DateTime, default=func.now())


class AgentDecision(Base):
    """Audit log of agent decisions for transparency and debugging"""
    __tablename__ = "agent_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    agent_name = Column(String)  # "learner_profiler", "journey_architect", etc.
    decision_type = Column(String)  # "profile_created", "path_adjusted", "difficulty_changed"
    input_data = Column(JSON)  # What the agent received
    output_data = Column(JSON)  # What the agent decided
    reasoning = Column(Text)  # Agent's reasoning
    confidence = Column(Float)  # Confidence score if applicable
    created_at = Column(DateTime, default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_user_agent', 'user_id', 'agent_name'),
        Index('idx_created_at_agent', 'created_at'),
    )


class EngagementMetrics(Base):
    """User engagement tracking for adaptive pacing"""
    __tablename__ = "engagement_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    session_start = Column(DateTime)
    session_end = Column(DateTime)
    topics_viewed = Column(JSON)  # List of topics
    quizzes_taken = Column(Integer, default=0)
    avg_score = Column(Float)
    interaction_count = Column(Integer, default=0)  # Clicks, hovers, etc.

    # Indexes
    __table_args__ = (
        Index('idx_user_session', 'user_id', 'session_start'),
    )
