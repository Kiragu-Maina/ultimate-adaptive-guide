"""
Database Initialization Script

Creates all tables in PostgreSQL database from SQLAlchemy models.
Run this once to set up the database schema.

Usage:
    python init_db.py
"""

import os
from sqlalchemy import create_engine
from db_models import Base, User, UserProfile, TopicMastery, QuizHistory, LearningJourney, AgentDecision, EngagementMetrics

# Database connection
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://adaptive_user:adaptive_pass@postgres:5432/adaptive_learning"
)

# For local testing, you might use:
# DATABASE_URL = "postgresql://adaptive_user:adaptive_pass@localhost:5433/adaptive_learning"

print(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

try:
    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)  # echo=True shows SQL statements

    print("\n" + "="*60)
    print("Creating all tables from SQLAlchemy models...")
    print("="*60 + "\n")

    # Create all tables
    Base.metadata.create_all(engine)

    print("\n" + "="*60)
    print("✅ SUCCESS: All tables created successfully!")
    print("="*60 + "\n")

    # Show created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("Created tables:")
    for table in tables:
        print(f"  ✓ {table}")

        # Show columns for each table
        columns = inspector.get_columns(table)
        for column in columns:
            col_type = str(column['type'])
            nullable = "NULL" if column['nullable'] else "NOT NULL"
            print(f"      - {column['name']}: {col_type} {nullable}")
        print()

    print("Database initialization complete! 🎉")

except Exception as e:
    print(f"\n❌ ERROR: Database initialization failed!")
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("1. Ensure PostgreSQL is running (docker compose up)")
    print("2. Check DATABASE_URL environment variable")
    print("3. Verify database credentials")
    exit(1)
