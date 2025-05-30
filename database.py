import logging
import os
import sys
from typing import Optional

import redis.asyncio as redis
from dotenv import load_dotenv
from sqlalchemy import Column, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine if we're in testing mode
IS_TESTING = (
    os.getenv("TESTING", "false").lower() == "true"
    or "pytest" in sys.modules
    or "test" in sys.argv[0]
    if sys.argv
    else False
)

# Database configuration
if IS_TESTING:
    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test_nutrition_recipe.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    logger.info("Using SQLite database for testing: test_nutrition_recipe.db")
else:
    # Use PostgreSQL for production
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "NutritionRecipe")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

    # Construct PostgreSQL URL
    SQLALCHEMY_DATABASE_URL = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    logger.info(
        "Using PostgreSQL database for production: "  # noqa: E501
        f"{SQLALCHEMY_DATABASE_URL}"  # noqa: E501
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client: Optional[redis.Redis] = None


# Database Models
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(String, primary_key=True)
    ingredient_name = Column(String, index=True)
    energy = Column(Float)
    carb = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    sugar = Column(Float)
    water = Column(Float)
    fiber = Column(Float)
    cost_per_gram = Column(Float)
    supplier_name = Column(String)


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    recipe_name = Column(String, index=True)
    recipe_type = Column(String, nullable=True)
    cuisine = Column(String, nullable=True)
    ingredients = relationship("RecipeIngredient", back_populates="recipe")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    ingredient_id = Column(String, ForeignKey("ingredients.id"))
    quantity_in_grams = Column(Integer)
    recipe = relationship("Recipe", back_populates="ingredients")


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Redis dependency
async def get_redis():
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            # Test the connection
            await redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            redis_client = None
            return None

    # Check if existing connection is still alive
    try:
        await redis_client.ping()
        return redis_client
    except Exception as e:
        logger.error(f"Redis connection lost: {e}")
        redis_client = None
        return None


async def is_redis_connected():
    """Check if Redis is connected and responsive"""
    try:
        redis_client = await get_redis()
        if redis_client is None:
            return False
        await redis_client.ping()
        return True
    except Exception:
        return False


# Initialize database
def init_db():
    Base.metadata.create_all(bind=engine)
