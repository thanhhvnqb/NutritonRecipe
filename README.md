# Recipe Cost & Nutrition API

A FastAPI-based backend service that calculates total cost and nutritional values for recipes and provides ingredient substitution suggestions based on nutritional similarity.

## 🗄️ Database Support

This application now supports **PostgreSQL** as the primary database backend, with automatic fallback to SQLite for testing. For detailed PostgreSQL setup instructions, see [README_POSTGRESQL.md](README_POSTGRESQL.md).

## Features

- 🍳 **Recipe Management**: Create and retrieve recipes with detailed ingredient information
- 💰 **Cost Calculation**: Automatic cost calculation based on ingredient quantities and prices
- 🥗 **Nutrition Analysis**: Comprehensive nutritional analysis per recipe
- 🔄 **Ingredient Substitution**: ML-powered ingredient substitution suggestions based on nutritional similarity
- 🐳 **Docker Support**: Containerized deployment with GPU support
- 🧪 **Comprehensive Testing**: Unit tests with high coverage
- 🚀 **CI/CD Pipeline**: GitHub Actions for automated testing and deployment

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/thanhhvnqb/NutritionRecipe
   cd recipe-api
   ```

2. **Place your CSV files**
   ```bash
   # Make sure you have the CSV files in the folder sample-data:
   # - ingredients.csv
   # - recipes.csv
   ```

3. **Start the service**
  ```bash
  docker compose up
  ```

4. **Access the API**
   - API: http://localhost:8000
   - Interactive Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Database Portability

The PostgreSQL and Redis data are now stored in local directories within the project folder, making it easy to move your database to another PC.

### Database Storage Location
- **PostgreSQL data**: `./data/postgres/`
- **Redis data**: `./data/redis/`

### Moving Database to Another PC

1. **Stop the services**
   ```bash
   docker compose down
   ```

2. **Copy the entire project folder** (including the `data/` directory) to the new PC
   ```bash
   # On source PC
   tar -czf NutritionRecipe-project.tar.gz /path/to/NutritionRecipe-assessment/

   # Transfer to new PC and extract
   tar -xzf NutritionRecipe-project.tar.gz
   ```

3. **Start services on the new PC**
   ```bash
   cd NutritionRecipe-assessment
   docker compose up
   ```

**Alternative: Use the migration script**
```bash
# Package the entire project (includes stopping/starting services)
./migrate_database.sh package

# Transfer the generated .tar.gz file to the new PC and extract
tar -xzf NutritionRecipe_migration_YYYYMMDD_HHMMSS.tar.gz
```

### Database Management Script

A helper script `migrate_database.sh` is provided for common database operations:

```bash
# Create a database backup
./migrate_database.sh backup

# Restore from a backup
./migrate_database.sh restore backup_20231201_143022.sql

# Package entire project for migration
./migrate_database.sh package

# Reset database (WARNING: destroys all data)
./migrate_database.sh reset

# Show help
./migrate_database.sh help
```

### Backup Database
```bash
# Create a backup
docker compose exec postgres pg_dump -U postgres NutritionRecipe > backup.sql

# Restore from backup (if needed)
docker compose exec -T postgres psql -U postgres NutritionRecipe < backup.sql
```

### Reset Database
```bash
# To start fresh, remove the data directories
docker compose down
rm -rf data/postgres data/redis
mkdir -p data/postgres data/redis
docker compose up
```

### Local Development

1. **Install Python 3.12**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Recipe Management

#### Create Recipe
```http
POST /recipes/
```

**Request Body:**
```json
{
  "recipe_name": "Delicious Pasta",
  "recipe_type": "Main Course",
  "cuisine": "Italian",
  "ingredients": [
    {
      "ingredient_id": "1",
      "quantity_in_grams": 20
    },
    {
      "ingredient_id": "4",
      "quantity_in_grams": 200
    }
  ]
}
```
> **Note:** The `ingredient_id` must be provided as a string. It can be in either format:
> - Simple numeric format: `"1"`, `"42"`
> - Prefixed format: `"ing_001"`, `"ing_042"`
> The API will normalize and return just the numeric portion in responses.

**Response:**
```json
{
  "recipe_id": 90,
  "recipe_name": "Delicious Pasta",
  "recipe_type": "Main Course",
  "cuisine": "Italian",
  "ingredients": [...],
  "total_cost": 1.28,
  "total_nutrition": {
    "energy": 709.84,
    "carb": 147.02,
    "protein": 27.68,
    "fat": 5.1,
    "sugar": 1.28,
    "water": 32.32,
    "fiber": 21.82
  }
}
```

#### Get Recipe
```http
GET /recipes/{recipe_id}/
```

### Ingredient Management

#### List Ingredients
```http
GET /ingredients/?limit=50&skip=0
```

#### Get Ingredient Substitutes
```http
GET /ingredients/{ingredient_id}/substitutes/?limit=3
```

**Response:**
```json
[
  {
    "ingredient_id": "ing_025",
    "ingredient_name": "White Onion",
    "similarity_score": 0.8765,
    "nutrition": {
      "energy": 40.0,
      "carb": 9.34,
      "protein": 1.1,
      "fat": 0.1,
      "sugar": 4.24,
      "water": 89.11,
      "fiber": 1.7
    },
    "cost_per_gram": 0.0045,
    "supplier_name": "Local Farms"
  }
]
```

### Other Endpoints

#### List All Recipes
```http
GET /recipes/?limit=20&skip=0
```

#### Health Check
```http
GET /health
```

## GPU Support

The system includes GPU support for enhanced ML operations. To enable GPU support:

1. **Ensure NVIDIA Docker runtime is installed**
   ```bash
   # Install nvidia-docker2
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

2. **Uncomment GPU configuration in docker-compose.yml**
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   environment:
     - NVIDIA_VISIBLE_DEVICES=all
     - NVIDIA_DRIVER_CAPABILITIES=compute,utility
   ```

3. **Start with GPU support**
   ```bash
   docker compose up --build
   ```

## Testing

### Local Testing
```bash
# Run tests locally (requires local setup)
pytest test_main.py -v

# With coverage report
pytest test_main.py --cov=main --cov-report=html --cov-report=term-missing

# Watch mode for development
pytest-watch -- test_main.py -v
```

### Docker Compose Testing (Recommended)

The tests have been modified to work with Docker Compose, using real PostgreSQL and Redis services instead of mocks. This provides more accurate testing conditions.

```bash
# Run tests in Docker Compose environment
make test-docker

# Or using docker compose directly
docker compose -f docker-compose.yml -f docker-compose.test.yml up --build recipe-api-test

# Run tests with clean environment (removes volumes)
make test-docker-clean

# View test logs
make test-docker-logs

# Stop test services
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v
```

#### Test Environment Configuration

The Docker test environment uses:
- **PostgreSQL**: `nutritionrecipe_test` database on port 5433
- **Redis**: Test Redis instance on port 6380
- **Environment Variables**: `TESTING=true`, `ENVIRONMENT=test`
- **Service Coordination**: Automatic waiting for services to be ready
- **Data Isolation**: Separate volumes for test data

#### Test Features

The test suite includes:
- **Service Health Checks**: Automatic waiting for PostgreSQL and Redis
- **Real Database Testing**: Uses actual PostgreSQL instead of mocks
- **Redis Caching Tests**: Tests with real Redis caching layer
- **Data Initialization**: Automatic loading of test data
- **Concurrent Testing**: Multi-threaded request testing
- **Error Scenarios**: Network failures and edge cases

### Test Coverage
The test suite covers:
- ✅ API endpoint functionality
- ✅ Recipe creation and retrieval
- ✅ Cost and nutrition calculations
- ✅ Ingredient substitution algorithms
- ✅ Redis caching functionality
- ✅ Database connection handling
- ✅ Error handling scenarios
- ✅ Input validation and edge cases
- ✅ Pagination and filtering
- ✅ Concurrent request handling
- ✅ Integration tests with real services

### Legacy Docker Testing
```bash
# For backward compatibility - testing within running containers
docker compose exec recipe-api pytest test_main.py -v
```

## Architecture

### Technology Stack
- **FastAPI**: Modern, fast web framework for building APIs
- **Pandas**: Data manipulation and analysis
- **Scikit-learn**: Machine learning for ingredient similarity
- **Pydantic**: Data validation using Python type hints
- **Docker**: Containerization
- **Nginx**: Reverse proxy (production)

### ML Algorithm for Substitution
The ingredient substitution system uses a sophisticated multi-modal approach:

1. **Nutritional Similarity (60% weight)**
   - Features: energy, carb, protein, fat, sugar, fiber
   - Normalization: L2 normalization for better cosine similarity
   - Method: Cosine similarity between nutritional feature vectors

2. **Text Similarity (40% weight)**
   - Semantic Similarity (70% of text weight)
     - Uses SentenceTransformer "all-MiniLM-L6-v2" model
     - Pre-computed embeddings for efficiency
     - Cosine similarity between name embeddings
   - String Similarity (30% of text weight)
     - Uses difflib's SequenceMatcher
     - Fallback for semantic matching
     - Helps with exact name matches

3. **Combined Scoring**
   - Weighted combination of nutritional and text similarities
   - Excludes the ingredient itself from results
   - Returns top-K most similar ingredients
   - Each substitute includes similarity score and full nutritional profile

The system is optimized for:
- Fast retrieval using pre-computed embeddings
- Balanced consideration of both nutritional and semantic similarity
- Robust handling of edge cases and missing data

### Data Models

#### Ingredient
```python
{
  "id": "ing_001",
  "ingredient_name": "Organic Garlic",
  "nutrition": {
    "energy": 149.2,
    "carb": 33.1,
    "protein": 6.4,
    "fat": 0.5,
    "sugar": 1.0,
    "water": 58.6,
    "fiber": 2.1
  },
  "cost_per_gram": 0.0321,
  "supplier_name": "Pure Provisions"
}
```

#### Recipe
```python
{
  "recipe_id": 1,
  "recipe_name": "Hearty Vegetable Soup",
  "recipe_type": "Soup",
  "cuisine": "Italian",
  "ingredients": [...],
  "total_cost": 2.45,
  "total_nutrition": {...}
}
```

## Production Deployment

### Using Docker Compose with Production Profile
```bash
# Start with production services (nginx, redis)
docker compose --profile production up -d

# Access via nginx reverse proxy
curl http://localhost/health
```

## Monitoring and Logging

### Health Checks
- Application health: `GET /health`
- Docker health checks configured
- Nginx proxy health monitoring

### Logging
- Structured logging with Python logging module
- Request/response logging
- Error tracking and monitoring

## Performance Considerations

### Caching Strategy
- Ingredient data cached in memory on startup
- Redis caching for production (optional)
- Similarity calculations cached

### Optimization
- Vectorized operations using NumPy
- Efficient DataFrame operations with Pandas
- Minimal memory footprint for ML models

## Security

### Security Features
- Non-root Docker user
- Security headers via Nginx
- Input validation with Pydantic
- CORS configuration
- Dependency vulnerability scanning

### Security Headers
```
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'self'
```

### Development Workflow
```bash
# Install dev dependencies
pip install -r requirements.txt

# Run linting
black --check --diff main.py test_main.py
isort --check-only --diff main.py test_main.py
flake8 main.py test_main.py --extend-ignore=E203,W503
mypy main.py --ignore-missing-imports

# Run tests
pytest test_main.py -v --cov=main
```

## API Documentation

When the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Common Issues

1. **CSV files not found**
   ```bash
   # Ensure CSV files are in the correct location
   ls -la sample-data/ingredients.csv sample-data/recipes.csv
   ```

2. **Docker build fails**
   ```bash
   # Clean Docker cache
   docker system prune -a
   docker compose build --no-cache
   ```

3. **Permission errors**
   ```bash
   # Fix file permissions
   chmod 644 *.csv
   chmod 755 *.py
   ```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Include logs and error messages

## Database Configuration

The application uses different databases for testing and production environments:

### Testing Environment
- **Database**: SQLite (`test_nutrition_recipe.db`)
- **Trigger**: When `TESTING=true` environment variable is set or when running with pytest
- **Benefits**:
  - No external database setup required
  - Fast test execution
  - Automatic cleanup between test runs
  - Isolated test environment

### Production Environment
- **Database**: PostgreSQL
- **Configuration**: Via environment variables:
  - `DB_HOST`: Database host (default: localhost)
  - `DB_PORT`: Database port (default: 5432)
  - `DB_NAME`: Database name (default: NutritionRecipe)
  - `DB_USER`: Database username (default: postgres)
  - `DB_PASSWORD`: Database password (default: password)

### Environment Variables for Database Configuration

For production, set these environment variables:
```bash
export DB_HOST=your-postgres-host
export DB_PORT=5432
export DB_NAME=NutritionRecipe
export DB_USER=your-username
export DB_PASSWORD=your-password
```

For testing (automatically handled):
```bash
export TESTING=true
```