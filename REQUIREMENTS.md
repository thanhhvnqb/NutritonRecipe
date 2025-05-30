We've created this basic test to allow you to demonstrate your skills outside the pressure of an interview.

We expect this should take a senior developer 2 - 3 hours to complete. And another 1 - 2 for the optional add-ons. 

We dont want you spending more than 4 hours on this. If you are unable to complete within this time, please submit what you have completed with details of how you would have finished or optimised it if you had more time.

---

## Assignment

We would like you to design a small backend service to: 

1. Calculate total cost and nutritional values for recipes
2. Provide a simple API using **FastAPI**
3. Find substitute ingredients based on similarity

---

## What's Provided?

A very simple database containing ingredients with nutrition information and recipes which use these ingredients.

The CSVs include:

- **Ingredient** — Contains ingredient details including nutrition, cost, and supplier
- **Nutrition** — A model to store nutritional values per 100g
- **RecipeIngredient** — Links ingredients to recipes with quantities
- **Recipe** — Contains a list of ingredients with their quantities

---

## Task 1: Cost & Nutrition API

Using **FastAPI**, build the following endpoints:

### `POST /recipes/`
- Create a new recipe.

### `GET /recipes/{id}/`
- Returns:
  - Recipe details
  - Total cost (based on quantity and ingredient cost)
  - Total nutrition (calculated by scaling `nutrition_per_100g` based on quantity used)

Example logic:
 python
total_cost = sum(ingredient.cost_per_gram * quantity for each ingredient)
nutrition = {
  "calories": sum(ingredient.nutrition["calories"] * quantity / 100 for each),
  ...
}

## Task 2: Suggest Ingredient Substitutes

### Add a basic substitute suggestion endpoint:
- **GET /ingredients/{id}/substitutes/**
  - Return 2-3 possible substitutes for an ingredient based on a similar nutrition profile (e.g., similar name, brand, calories or macros).
  - You can use any ML techniques to get the best matches. **Use of any LLM API is strictly prohibited**
  - (Optional) Create a test with one of the recipes utilizing this API

### Optional Add-ons:
- Docker support (with GPU resource enabled)
- Unit tests
- GitHub Actions CI

### **Submission Guidelines**
- Submit your code via GitHub or as a zip archive.
- Include a README with instructions to run your solution.
- Docker is optional but encouraged.
- Include basic tests if time allows.# NutritionRecipe
