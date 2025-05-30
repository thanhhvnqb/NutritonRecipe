#!/usr/bin/env python3
"""
PostgreSQL Database Initialization Script for NutritionRecipe Assessment

This script helps initialize the PostgreSQL database with the required tables.
Make sure PostgreSQL is running and the database exists before running this
script.
"""

import logging
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (  # noqa: E402, E501, isort:skip
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    SQLALCHEMY_DATABASE_URL,
    Base,
)  # noqa: E402, E501, isort:skip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    # Connect to PostgreSQL server (not to a specific database)
    server_url = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@"  # noqa: E501
        f"{DB_HOST}:{DB_PORT}/postgres"  # noqa: E501
    )

    try:
        # Use autocommit=True to avoid transaction blocks for CREATE DATABASE
        engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": DB_NAME},
            )

            if not result.fetchone():
                # Database doesn't exist, create it
                # No need for COMMIT since we're in autocommit mode
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
                logger.info(f"Database '{DB_NAME}' created successfully")
            else:
                logger.info(f"Database '{DB_NAME}' already exists")

    except OperationalError as e:
        logger.error(f"Failed to connect to PostgreSQL server: {e}")
        logger.error(
            "Please ensure PostgreSQL is running and "
            "credentials are correct"  # noqa: E501
        )
        return False
    except ProgrammingError as e:
        logger.error(f"Failed to create database: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

    return True


def create_tables():
    """Create all tables defined in the models"""
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)

        # Test connection to the specific database
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
        return True

    except OperationalError as e:
        logger.error(f"Failed to connect to database '{DB_NAME}': {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


def main():
    """Main initialization function"""
    logger.info("Starting PostgreSQL database initialization...")
    logger.info(f"Database: {DB_NAME}")
    logger.info(f"Host: {DB_HOST}:{DB_PORT}")
    logger.info(f"User: {DB_USER}")

    # Step 1: Create database if it doesn't exist
    if not create_database_if_not_exists():
        logger.error("Failed to create/verify database. Exiting.")
        sys.exit(1)

    # Step 2: Create tables
    if not create_tables():
        logger.error("Failed to create tables. Exiting.")
        sys.exit(1)

    logger.info("PostgreSQL database initialization completed successfully!")
    logger.info(
        "You can now start the application with: "  # noqa: E501
        "uvicorn main:app --reload"
    )


if __name__ == "__main__":
    main()
