import difflib
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import torch
import torch.nn.functional as F
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import Ingredient as DBIngredient
from database import Recipe as DBRecipe
from database import RecipeIngredient as DBRecipeIngredient
from database import get_db, get_redis, init_db, is_redis_connected

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for ML features
ingredient_features: Optional[torch.Tensor] = None
text_model: Optional[SentenceTransformer] = None
ingredient_names: Optional[List[str]] = None
ingredient_name_embeddings: Optional[torch.Tensor] = None

# Check if we're in test environment
IS_TESTING = (
    os.getenv("TESTING", "false").lower() == "true"
    or "pytest" in sys.modules
    or "test" in sys.argv[0]
    if sys.argv
    else False
)


# Initialize rate limiter with conditional limits
def get_rate_limit_key(request: Request):
    """Custom key function that returns None during testing to disable rate limiting"""  # noqa: E501
    if IS_TESTING:
        return None  # Disable rate limiting during tests
    return get_remote_address(request)


limiter = Limiter(key_func=get_rate_limit_key)


# Custom rate limit exceeded handler
async def rate_limit_exceeded_handler(
    request: Request, exc: Exception
) -> Response:  # noqa: E501
    """Custom handler for rate limit exceeded exceptions"""
    # Cast to RateLimitExceeded for proper access to attributes
    rate_limit_exc = exc if isinstance(exc, RateLimitExceeded) else None

    if rate_limit_exc:
        detail = rate_limit_exc.detail
        retry_after = (
            str(rate_limit_exc.retry_after)
            if hasattr(rate_limit_exc, "retry_after")
            else "60"
        )
    else:
        detail = "Rate limit exceeded"
        retry_after = "60"

    response = Response(
        content=f"Rate limit exceeded: {detail}",
        status_code=429,
        headers={"Retry-After": retry_after},
    )
    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and load ML features on startup"""
    init_db()

    # Try to load ML features with retry mechanism
    import time

    max_retries = 3
    for attempt in range(max_retries):
        try:
            load_ml_features()
            if ingredient_features is not None:
                logger.info("ML features loaded successfully on startup")
                break
            else:
                logger.warning(
                    f"ML features not loaded on attempt {attempt + 1}"  # noqa: E501
                )
        except Exception as e:
            logger.warning(
                f"Failed to load ML features on attempt {attempt + 1}: {e}"  # noqa: E501
            )

        if attempt < max_retries - 1:
            time.sleep(1)  # Wait 1 second before retry

    if ingredient_features is None:
        logger.warning(
            "ML features could not be loaded during startup, "
            "they will be loaded on demand"  # noqa: E501
        )

    yield


app = FastAPI(
    title="Recipe Cost & Nutrition API",
    description="A FastAPI service to calculate recipe costs, "
    "nutrition, and suggest ingredient substitutes",  # noqa: E501
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class NutritionInfo(BaseModel):
    energy: float = Field(..., description="Energy in kcal per 100g")
    carb: float = Field(..., description="Carbohydrates in g per 100g")
    protein: float = Field(..., description="Protein in g per 100g")
    fat: float = Field(..., description="Fat in g per 100g")
    sugar: float = Field(..., description="Sugar in g per 100g")
    water: float = Field(..., description="Water in g per 100g")
    fiber: float = Field(..., description="Fiber in g per 100g")


class Ingredient(BaseModel):
    id: str
    ingredient_name: str
    nutrition: NutritionInfo
    cost_per_gram: float
    supplier_name: str


class RecipeIngredient(BaseModel):
    ingredient_id: str
    quantity_in_grams: int = Field(
        ..., gt=0, description="Quantity in grams (must be positive)"
    )


class ResponseRecipeIngredient(BaseModel):
    ingredient_id: str
    ingredient_name: str
    quantity_in_grams: int


class Recipe(BaseModel):
    recipe_name: str = Field(
        ..., min_length=1, description="Recipe name cannot be empty"
    )
    ingredients: List[RecipeIngredient] = Field(
        ..., min_length=1, description="Must have at least one ingredient"
    )
    recipe_type: Optional[str] = None
    cuisine: Optional[str] = None


class RecipeResponse(BaseModel):
    recipe_id: int
    recipe_name: str
    recipe_type: Optional[str] = None
    cuisine: Optional[str] = None
    ingredients: List[ResponseRecipeIngredient]
    total_cost: float
    total_nutrition: NutritionInfo


class IngredientSubstitute(BaseModel):
    ingredient_id: str
    ingredient_name: str
    similarity_score: float
    nutrition: NutritionInfo
    cost_per_gram: float
    supplier_name: str


def load_ml_features() -> None:
    """Load and prepare ML features for similarity calculation"""
    global ingredient_features, text_model, ingredient_names, ingredient_name_embeddings  # noqa: E501

    try:
        db = next(get_db())
        ingredients = db.query(DBIngredient).all()

        if not ingredients:
            logger.warning("No ingredients found in database")
            ingredient_features = None
            text_model = None
            ingredient_names = None
            ingredient_name_embeddings = None
            return

        # Prepare features for similarity calculation
        nutrition_features = [
            "energy",
            "carb",
            "protein",
            "fat",
            "sugar",
            "fiber",
        ]  # noqa: E501
        feature_data = [
            [getattr(ing, feat) for feat in nutrition_features]  # noqa: E501
            for ing in ingredients
        ]
        ingredient_features = torch.tensor(feature_data, dtype=torch.float32)

        # Normalize nutritional features
        ingredient_features = F.normalize(ingredient_features, p=2, dim=1)

        # Initialize sentence transformer model for text similarity
        text_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Store ingredient names for reference
        ingredient_names = [ing.ingredient_name for ing in ingredients]

        # Pre-compute name embeddings for efficiency
        ingredient_name_embeddings = text_model.encode(
            ingredient_names, convert_to_tensor=True
        )
        ingredient_name_embeddings = F.normalize(
            ingredient_name_embeddings, p=2, dim=1
        )  # noqa: E501

        logger.info(
            f"ML features loaded and preprocessed successfully for "  # noqa: E501
            f"{len(ingredients)} ingredients"  # noqa: E501
        )

    except Exception as e:
        logger.error(f"Error loading ML features: {e}")
        # Set to None on error to indicate features are not available
        ingredient_features = None
        text_model = None
        ingredient_names = None
        ingredient_name_embeddings = None
    finally:
        if "db" in locals():
            db.close()


def convert_ingredient_id(ingredient_id: str) -> str:
    """Convert ingredient ID from ing_XXX format to just number"""
    if ingredient_id.startswith("ing_"):
        return str(int(ingredient_id[4:]))  # Remove 'ing_' prefix
    return ingredient_id


async def get_ingredient_by_id(
    db: Session, ingredient_id: str
) -> Optional[Dict[str, Any]]:
    """Get ingredient by ID with Redis caching"""
    redis_client = await get_redis()
    if redis_client:
        try:
            # Try to get from Redis cache
            cache_key = f"ingredient:{ingredient_id}"
            cached_data = await redis_client.get(cache_key)

            if cached_data:
                logger.debug(f"Ingredient {ingredient_id} retrieved from cache")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(
                f"Redis cache read failed for ingredient {ingredient_id}: {e}"
            )
            # Continue to database fallback

    # If not in cache, get from database
    formatted_id = (
        f"ing_{ingredient_id.zfill(3)}"  # noqa: E501
        if ingredient_id.isdigit()
        else ingredient_id
    )
    ingredient = (
        db.query(DBIngredient)
        .filter(DBIngredient.id == formatted_id)
        .first()  # noqa: E501
    )

    if not ingredient:
        return None

    # Convert to dict and cache
    ingredient_dict = {
        "id": ingredient.id,
        "ingredient_name": ingredient.ingredient_name,
        "energy": ingredient.energy,
        "carb": ingredient.carb,
        "protein": ingredient.protein,
        "fat": ingredient.fat,
        "sugar": ingredient.sugar,
        "water": ingredient.water,
        "fiber": ingredient.fiber,
        "cost_per_gram": ingredient.cost_per_gram,
        "supplier_name": ingredient.supplier_name,
    }

    # Cache for 1 hour if Redis is available
    if redis_client:
        try:
            await redis_client.setex(
                cache_key, 3600, json.dumps(ingredient_dict)  # noqa: E501
            )
            logger.debug(f"Ingredient {ingredient_id} cached successfully")
        except Exception as e:
            logger.warning(
                f"Redis cache write failed for ingredient {ingredient_id}: {e}"
            )
            # Continue without caching

    return ingredient_dict


async def calculate_recipe_nutrition_and_cost(
    db: Session,
    recipe_ingredients: List[RecipeIngredient] | List[ResponseRecipeIngredient],
) -> tuple[float, NutritionInfo]:
    """Calculate total cost and nutrition for a recipe"""
    total_cost = 0.0
    total_nutrition = {
        "energy": 0.0,
        "carb": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "sugar": 0.0,
        "water": 0.0,
        "fiber": 0.0,
    }

    for recipe_ingredient in recipe_ingredients:
        ingredient_id = recipe_ingredient.ingredient_id
        ingredient = await get_ingredient_by_id(db, ingredient_id)
        if not ingredient:
            raise HTTPException(
                status_code=404,
                detail=f"Ingredient {ingredient_id} not found",
            )

        quantity_grams = recipe_ingredient.quantity_in_grams

        # Calculate cost
        cost = ingredient["cost_per_gram"] * quantity_grams
        total_cost += cost

        # Calculate nutrition (scale from per 100g to actual quantity)
        scaling_factor = quantity_grams / 100.0
        for nutrient in total_nutrition.keys():
            total_nutrition[nutrient] += ingredient[nutrient] * scaling_factor

    return total_cost, NutritionInfo(**total_nutrition)


async def find_similar_ingredients(
    db: Session, ingredient_id: str, top_k: int = 3
) -> List[IngredientSubstitute]:
    """Find similar ingredients based on nutritional profile and name similarity"""  # noqa: E501
    # If ML features aren't loaded, try to load them on demand
    if ingredient_features is None or text_model is None:
        logger.info("ML features not loaded, attempting to load on demand")
        load_ml_features()

    # If still not loaded, return empty list
    if (
        ingredient_features is None
        or text_model is None
        or ingredient_name_embeddings is None
    ):
        logger.warning(
            "ML features could not be loaded, returning empty substitutes list"  # noqa: E501
        )
        return []

    # Get all ingredients
    ingredients = db.query(DBIngredient).all()
    if not ingredients:
        return []

    # Find the index of the target ingredient
    target_idx = None
    target_ingredient = None
    for i, ing in enumerate(ingredients):
        if ing.id == ingredient_id:
            target_idx = i
            target_ingredient = ing
            break

    if target_idx is None or target_ingredient is None:
        return []

    # Get target features for nutritional similarity
    target_nutritional_features = ingredient_features[target_idx].unsqueeze(0)

    # Normalize features for better cosine similarity
    target_nutritional_features = F.normalize(
        target_nutritional_features, p=2, dim=1
    )  # noqa: E501
    all_nutritional_features = F.normalize(ingredient_features, p=2, dim=1)

    # Calculate nutritional similarity using cosine similarity
    nutritional_similarities = F.cosine_similarity(
        target_nutritional_features, all_nutritional_features, dim=1
    )

    # Calculate text similarity using pre-computed embeddings
    target_name_embedding = ingredient_name_embeddings[target_idx].unsqueeze(0)

    # Calculate semantic similarity with all ingredients at once
    semantic_similarities = F.cosine_similarity(
        target_name_embedding, ingredient_name_embeddings, dim=1
    )

    # Also calculate simple text similarity as fallback
    target_name = target_ingredient.ingredient_name.lower()
    string_similarities_list: List[float] = []

    for ing in ingredients:
        string_sim = difflib.SequenceMatcher(
            None, target_name, ing.ingredient_name.lower()
        ).ratio()
        string_similarities_list.append(string_sim)

    string_similarities = torch.tensor(string_similarities_list)

    # Combine semantic and string similarity
    text_similarities = 0.7 * semantic_similarities + 0.3 * string_similarities

    # Combine nutritional and text similarities with weights
    # 60% weight for nutritional similarity, 40% for text similarity
    combined_similarities = (
        0.6 * nutritional_similarities + 0.4 * text_similarities
    )  # noqa: E501

    # Get top similar ingredients (excluding the ingredient itself)
    similar_indices = torch.argsort(combined_similarities, descending=True)[
        1 : top_k + 1
    ]  # noqa: E501

    substitutes = []
    for idx in similar_indices:
        ingredient = ingredients[idx]
        nutrition = NutritionInfo(
            energy=ingredient.energy,
            carb=ingredient.carb,
            protein=ingredient.protein,
            fat=ingredient.fat,
            sugar=ingredient.sugar,
            water=ingredient.water,
            fiber=ingredient.fiber,
        )

        substitute = IngredientSubstitute(
            ingredient_id=ingredient.id,
            ingredient_name=ingredient.ingredient_name,
            similarity_score=float(combined_similarities[idx]),
            nutrition=nutrition,
            cost_per_gram=ingredient.cost_per_gram,
            supplier_name=ingredient.supplier_name,
        )
        substitutes.append(substitute)

    return substitutes


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Recipe Cost & Nutrition API", "version": "1.0.0"}


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    ingredients_count = db.query(DBIngredient).count()
    recipes_count = db.query(DBRecipe).count()
    redis_connected = await is_redis_connected()
    return {
        "status": "healthy",
        "ingredients_count": ingredients_count,
        "recipes_count": recipes_count,
        "redis_connected": redis_connected,
    }


@app.get("/redis/status")
async def redis_status():
    """Check Redis connection status"""
    try:
        redis_client = await get_redis()
        if redis_client is None:
            return {
                "connected": False,
                "status": "Redis client not initialized",
                "error": "Connection failed during initialization",
            }

        # Test the connection with ping
        await redis_client.ping()

        # Get some Redis info if possible
        try:
            info = await redis_client.info()
            return {
                "connected": True,
                "status": "Redis is connected and responsive",
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", "unknown"),
            }
        except Exception:
            # If info fails but ping works, still consider it connected
            return {
                "connected": True,
                "status": "Redis is connected (limited info available)",
            }

    except Exception as e:
        return {
            "connected": False,
            "status": "Redis connection failed",
            "error": str(e),
        }


@app.post("/recipes/", response_model=RecipeResponse)
@limiter.limit("10/minute")
async def create_recipe(
    request: Request, recipe: Recipe, db: Session = Depends(get_db)
):
    """Create a new recipe and return its details with cost and nutrition"""
    try:
        # Calculate cost and nutrition
        total_cost, total_nutrition = await calculate_recipe_nutrition_and_cost(
            db, recipe.ingredients
        )

        # Create new recipe
        db_recipe = DBRecipe(
            recipe_name=recipe.recipe_name,
            recipe_type=recipe.recipe_type,
            cuisine=recipe.cuisine,
        )
        db.add(db_recipe)
        db.flush()  # Get the recipe ID

        # Create recipe ingredients
        response_ingredients = []
        for ingredient in recipe.ingredients:
            ingredient_id = ingredient.ingredient_id
            # Use the ingredient ID as-is, let get_ingredient_by_id handle formatting  # noqa: E501
            ingredient_data = await get_ingredient_by_id(db, ingredient_id)
            if not ingredient_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ingredient {ingredient_id} not found",
                )

            # For database storage, we need to ensure it's in the correct format
            db_ingredient_id = (
                f"ing_{ingredient_id.zfill(3)}"
                if ingredient_id.isdigit()
                else ingredient_id
            )

            db_recipe_ingredient = DBRecipeIngredient(
                recipe_id=db_recipe.id,
                ingredient_id=db_ingredient_id,
                quantity_in_grams=ingredient.quantity_in_grams,
            )
            db.add(db_recipe_ingredient)

            response_ingredient = ResponseRecipeIngredient(
                ingredient_id=convert_ingredient_id(
                    db_ingredient_id
                ),  # Convert for response display
                ingredient_name=ingredient_data["ingredient_name"],
                quantity_in_grams=ingredient.quantity_in_grams,
            )
            response_ingredients.append(response_ingredient)

        db.commit()
        db.refresh(db_recipe)  # Refresh to ensure ID is properly resolved

        response = RecipeResponse(
            recipe_id=int(db_recipe.id),
            recipe_name=str(db_recipe.recipe_name),
            recipe_type=(
                str(db_recipe.recipe_type) if db_recipe.recipe_type else None
            ),  # noqa: E501
            cuisine=str(db_recipe.cuisine) if db_recipe.cuisine else None,  # noqa: E501
            ingredients=response_ingredients,
            total_cost=round(total_cost, 2),
            total_nutrition=total_nutrition,
        )
        logger.info(f"Created recipe: {response} with total cost: {total_cost}")

        return response
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating recipe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recipes/{recipe_id}/", response_model=RecipeResponse)
@limiter.limit("30/minute")
async def get_recipe(
    request: Request, recipe_id: int, db: Session = Depends(get_db)
):  # noqa: E501
    """Get recipe details with cost and nutrition"""
    try:
        # Try to get from Redis cache
        redis_client = await get_redis()
        if redis_client:
            try:
                cache_key = f"recipe:{recipe_id}"
                cached_data = await redis_client.get(cache_key)

                if cached_data:
                    logger.info(f"Recipe {recipe_id} retrieved from cache")
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(
                    f"Redis cache read failed for recipe {recipe_id}: {e}"  # noqa: E501
                )
                # Continue to database fallback
        else:
            logger.info("Redis not connected, using database directly")

        # If not in cache, get from database
        recipe = db.query(DBRecipe).filter(DBRecipe.id == recipe_id).first()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Get recipe ingredients
        recipe_ingredients = []
        for ri in recipe.ingredients:
            ingredient_data = await get_ingredient_by_id(db, ri.ingredient_id)
            if not ingredient_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ingredient {ri.ingredient_id} not found",
                )

            recipe_ingredient = ResponseRecipeIngredient(
                ingredient_id=ri.ingredient_id,
                ingredient_name=ingredient_data["ingredient_name"],
                quantity_in_grams=ri.quantity_in_grams,
            )
            recipe_ingredients.append(recipe_ingredient)

        # Calculate cost and nutrition
        total_cost, total_nutrition = await calculate_recipe_nutrition_and_cost(
            db, recipe_ingredients
        )

        response = RecipeResponse(
            recipe_id=int(recipe.id),
            recipe_name=str(recipe.recipe_name),
            recipe_type=(
                str(recipe.recipe_type) if recipe.recipe_type else None
            ),  # noqa: E501
            cuisine=str(recipe.cuisine) if recipe.cuisine else None,  # noqa: E501
            ingredients=recipe_ingredients,
            total_cost=round(total_cost, 2),
            total_nutrition=total_nutrition,
        )

        # Cache for 1 hour if Redis is available
        if redis_client:
            try:
                cache_key = f"recipe:{recipe_id}"
                await redis_client.setex(
                    cache_key, 3600, json.dumps(response.model_dump())
                )
                logger.info(f"Recipe {recipe_id} cached successfully")
            except Exception as e:
                logger.warning(
                    f"Redis cache write failed for recipe {recipe_id}: {e}"  # noqa: E501
                )
                # Continue without caching

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe {recipe_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/ingredients/{ingredient_id}/substitutes/",
    response_model=List[IngredientSubstitute],
)
@limiter.limit("20/minute")
async def get_ingredient_substitutes(
    request: Request,
    ingredient_id: str,
    limit: int = 3,
    db: Session = Depends(get_db),
):
    """Get ingredient substitutes based on nutritional similarity"""
    try:
        # Convert the input ID to match the format in the DataFrame
        formatted_id = (
            f"ing_{ingredient_id.zfill(3)}"
            if ingredient_id.isdigit()
            else ingredient_id
        )

        # Check if ingredient exists
        ingredient = await get_ingredient_by_id(db, formatted_id)
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")

        # Find similar ingredients
        substitutes = await find_similar_ingredients(
            db, formatted_id, top_k=limit
        )  # noqa: E501

        # Convert IDs in substitutes to just numbers
        for substitute in substitutes:
            substitute.ingredient_id = convert_ingredient_id(
                substitute.ingredient_id
            )  # noqa: E501

        return substitutes

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding substitutes for {ingredient_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ingredients/", response_model=List[Ingredient])
@limiter.limit("50/minute")
async def list_ingredients(
    request: Request,
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    """List all ingredients with pagination"""
    try:
        ingredients = db.query(DBIngredient).offset(skip).limit(limit).all()
        ingredients_list = []

        for ingredient in ingredients:
            nutrition = NutritionInfo(
                energy=float(ingredient.energy),
                carb=float(ingredient.carb),
                protein=float(ingredient.protein),
                fat=float(ingredient.fat),
                sugar=float(ingredient.sugar),
                water=float(ingredient.water),
                fiber=float(ingredient.fiber),
            )

            ingredient_model = Ingredient(
                id=convert_ingredient_id(str(ingredient.id)),
                ingredient_name=str(ingredient.ingredient_name),
                nutrition=nutrition,
                cost_per_gram=float(ingredient.cost_per_gram),
                supplier_name=str(ingredient.supplier_name),
            )
            ingredients_list.append(ingredient_model)

        return ingredients_list

    except Exception as e:
        logger.error(f"Error listing ingredients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recipes/", response_model=List[Dict[str, Any]])
@limiter.limit("50/minute")
async def list_recipes(
    request: Request,
    limit: int = 20,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    """List all recipes with basic info"""
    try:
        recipes = db.query(DBRecipe).offset(skip).limit(limit).all()
        return [
            {
                "recipe_id": recipe.id,
                "recipe_name": recipe.recipe_name,
                "recipe_type": recipe.recipe_type,
                "cuisine": recipe.cuisine,
            }
            for recipe in recipes
        ]

    except Exception as e:
        logger.error(f"Error listing recipes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def check_redis_connectivity() -> tuple[bool, Optional[str]]:
    """
    Check if Redis is connected and responsive.

    Returns:
        tuple: (is_connected: bool, error_message: Optional[str])
    """
    try:
        redis_client = await get_redis()
        if redis_client is None:
            return False, "Redis client not initialized"

        await redis_client.ping()
        return True, None
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
