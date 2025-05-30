import logging
import os

import pandas as pd
from sqlalchemy import text

from database import RecipeIngredient  # noqa: E501
from database import Ingredient, Recipe, SessionLocal, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_ingredient_id_to_string(ingredient_id):
    """Convert numeric ingredient ID to string format (ing_XXX)"""
    if isinstance(ingredient_id, (int, float)):
        return f"ing_{int(ingredient_id):03d}"
    elif isinstance(ingredient_id, str) and ingredient_id.isdigit():
        return f"ing_{int(ingredient_id):03d}"
    else:
        return ingredient_id


def reset_recipe_sequence(db):
    """Reset the PostgreSQL sequence for recipe IDs to avoid conflicts"""
    try:
        # Check if we're using SQLite (testing mode)
        if os.getenv("TESTING", "false").lower() == "true":
            logger.info(
                "Using SQLite in testing mode - skipping sequence reset"  # noqa: E501
            )
            return

        # Check database dialect to ensure we're using PostgreSQL
        dialect_name = db.bind.dialect.name
        if dialect_name != "postgresql":
            logger.info(
                f"Database dialect is {dialect_name} - skipping PostgreSQL "  # noqa: E501
                "sequence reset"  # noqa: E501
            )
            return

        # Get the maximum recipe ID from the database
        max_id_result = db.execute(
            text("SELECT MAX(id) FROM recipes")
        ).fetchone()  # noqa: E501
        max_id = max_id_result[0] if max_id_result and max_id_result[0] else 0

        # Reset the sequence to start from max_id + 1
        db.execute(
            text(f"SELECT setval('recipes_id_seq', {max_id}, true)")  # noqa: E501
        )
        db.commit()
        logger.info(f"Reset recipe sequence to start from {max_id + 1}")
    except Exception as e:
        logger.warning(f"Could not reset recipe sequence: {e}")


def load_initial_data():
    """Load data from CSV files into SQLite database"""
    # Initialize database
    init_db()

    # Create database session
    db = SessionLocal()

    try:
        # Load ingredients
        ingredients_path = "sample-data/ingredients.csv"
        ingredients_df = pd.read_csv(ingredients_path)

        # Load recipes
        recipes_path = "sample-data/recipes.csv"
        recipes_df = pd.read_csv(recipes_path)

        # Load ingredients into database (check if exists first)
        for _, row in ingredients_df.iterrows():
            existing_ingredient = (
                db.query(Ingredient).filter(Ingredient.id == row["id"]).first()
            )
            if not existing_ingredient:
                ingredient = Ingredient(
                    id=row["id"],
                    ingredient_name=row["ingredient_name"],
                    energy=row["energy"],
                    carb=row["carb"],
                    protein=row["protein"],
                    fat=row["fat"],
                    sugar=row["sugar"],
                    water=row["water"],
                    fiber=row["fiber"],
                    cost_per_gram=row["cost_per_gram"],
                    supplier_name=row["supplier_name"],
                )
                db.add(ingredient)

        # Load recipes into database (check if exists first)
        unique_recipes = recipes_df.drop_duplicates("recipe_id")
        for _, row in unique_recipes.iterrows():
            existing_recipe = (
                db.query(Recipe).filter(Recipe.id == row["recipe_id"]).first()
            )
            if not existing_recipe:
                recipe = Recipe(
                    id=row["recipe_id"],
                    recipe_name=row["recipe_name"],
                    recipe_type=row["recipe_type"],
                    cuisine=row["cuisine"],
                )
                db.add(recipe)

        # Load recipe ingredients (check if exists first)
        for _, row in recipes_df.iterrows():
            # Convert numeric ingredient_id to proper string format
            formatted_ingredient_id = convert_ingredient_id_to_string(
                row["ingredient_id"]
            )

            existing_recipe_ingredient = (
                db.query(RecipeIngredient)
                .filter(
                    RecipeIngredient.recipe_id == row["recipe_id"],
                    RecipeIngredient.ingredient_id == formatted_ingredient_id,
                )
                .first()
            )
            if not existing_recipe_ingredient:
                recipe_ingredient = RecipeIngredient(
                    recipe_id=row["recipe_id"],
                    ingredient_id=formatted_ingredient_id,
                    quantity_in_grams=row["quantity_in_grams"],
                )
                db.add(recipe_ingredient)

        # Commit all changes
        db.commit()

        # Reset the recipe sequence to avoid ID conflicts
        reset_recipe_sequence(db)

        logger.info("Data loaded successfully!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error loading data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_initial_data()
