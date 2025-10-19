"""
Database Migration: Add description, estimated_hours, and prerequisites to learning_journeys table

This migration adds the missing fields required for the frontend journey display.
"""

import os
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://adaptive_user:adaptive_pass@postgres:5432/adaptive_learning"
)

print(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

try:
    # Create engine
    engine = create_engine(DATABASE_URL)

    print("\n" + "="*60)
    print("Running migration: Add journey fields")
    print("="*60 + "\n")

    with engine.connect() as conn:
        # Check if columns already exist
        check_columns = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'learning_journeys'
            AND column_name IN ('description', 'estimated_hours', 'prerequisites')
        """)

        existing_columns = [row[0] for row in conn.execute(check_columns)]

        print(f"Existing columns: {existing_columns}")

        # Add description column if it doesn't exist
        if 'description' not in existing_columns:
            print("Adding 'description' column...")
            conn.execute(text("""
                ALTER TABLE learning_journeys
                ADD COLUMN description TEXT
            """))
            conn.commit()
            print("✓ Added 'description' column")
        else:
            print("✓ 'description' column already exists")

        # Add estimated_hours column if it doesn't exist
        if 'estimated_hours' not in existing_columns:
            print("Adding 'estimated_hours' column...")
            conn.execute(text("""
                ALTER TABLE learning_journeys
                ADD COLUMN estimated_hours INTEGER DEFAULT 10
            """))
            conn.commit()
            print("✓ Added 'estimated_hours' column")
        else:
            print("✓ 'estimated_hours' column already exists")

        # Add prerequisites column if it doesn't exist
        if 'prerequisites' not in existing_columns:
            print("Adding 'prerequisites' column...")
            conn.execute(text("""
                ALTER TABLE learning_journeys
                ADD COLUMN prerequisites JSON
            """))
            conn.commit()
            print("✓ Added 'prerequisites' column")
        else:
            print("✓ 'prerequisites' column already exists")

    print("\n" + "="*60)
    print("✅ Migration completed successfully!")
    print("="*60 + "\n")

except Exception as e:
    print(f"\n❌ ERROR: Migration failed!")
    print(f"Error: {e}")
    exit(1)
