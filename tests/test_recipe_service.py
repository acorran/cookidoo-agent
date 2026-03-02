"""
Unit tests for recipe service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.services.recipe_service import RecipeService
from backend.models.recipe import (
    Recipe,
    Ingredient,
    CookingStep,
)


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    mock = Mock()
    mock.mcp_server_url = "http://localhost:8001"
    mock.mcp_timeout = 30.0
    mock.databricks_host = "https://test.databricks.com"
    mock.databricks_token = "test_token"
    with patch('backend.services.recipe_service.get_settings', return_value=mock):
        yield mock


@pytest.fixture
def sample_recipe():
    """Sample recipe for testing."""
    return Recipe(
        id="test-recipe-001",
        title="Test Pasta",
        description="A simple test pasta recipe",
        servings=4,
        prep_time_minutes=15,
        cook_time_minutes=20,
        total_time_minutes=35,
        difficulty="easy",
        ingredients=[
            Ingredient(name="pasta", quantity=500, unit="g"),
            Ingredient(name="tomato sauce", quantity=2, unit="cups"),
            Ingredient(name="parmesan", quantity=50, unit="g")
        ],
        steps=[
            CookingStep(step_number=1, instruction="Boil water", duration_minutes=5),
            CookingStep(step_number=2, instruction="Cook pasta", duration_minutes=10),
            CookingStep(step_number=3, instruction="Add sauce", duration_minutes=5)
        ],
        source="cookidoo",
        tags=["italian", "pasta", "easy"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def recipe_service(mock_settings):
    """Recipe service instance for testing."""
    return RecipeService()


class TestRecipeService:
    """Test suite for RecipeService."""
    
    @pytest.mark.asyncio
    async def test_get_recipe_success(self, recipe_service, sample_recipe):
        """Test successful recipe retrieval."""
        with patch.object(recipe_service.mcp_client, 'get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: sample_recipe.model_dump(mode='json')
            )
            
            result = await recipe_service.get_recipe("test-recipe-001")
            
            assert result.id == "test-recipe-001"
            assert result.title == "Test Pasta"
            assert len(result.ingredients) == 3
    
    @pytest.mark.asyncio
    async def test_get_recipe_not_found(self, recipe_service):
        """Test recipe not found scenario."""
        with patch.object(recipe_service.mcp_client, 'get') as mock_get:
            mock_get.return_value = Mock(status_code=404)
            
            result = await recipe_service.get_recipe("nonexistent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_scale_recipe(self, recipe_service, sample_recipe):
        """Test recipe scaling functionality."""
        with patch.object(recipe_service.mcp_client, 'get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: sample_recipe.model_dump(mode='json')
            )
            scaled = await recipe_service.scale_recipe("test-recipe-001", 8)
        
        assert scaled.servings == 8
        assert scaled.ingredients[0].quantity == 1000  # 500g * 2
        assert scaled.ingredients[1].quantity == 4  # 2 cups * 2
    
    @pytest.mark.asyncio
    async def test_modify_recipe_placeholder(self, recipe_service, sample_recipe):
        """Test recipe modification (placeholder implementation)."""
        with patch.object(recipe_service.mcp_client, 'get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: sample_recipe.model_dump(mode='json')
            )
            result = await recipe_service.modify_recipe(
                recipe_id="test-recipe-001",
                modification_prompt="Make it vegan",
            )
        
        # Since it's a placeholder, check basic structure
        assert result.original_recipe is not None
        assert result.modified_recipe is not None
        assert result.success is True
    
    def test_ingredient_scaling(self):
        """Test individual ingredient scaling logic."""
        ingredient = Ingredient(name="flour", quantity=2.5, unit="cups")
        
        # Scale factor of 2
        scaled_qty = ingredient.quantity * 2
        assert scaled_qty == 5.0
        
        # Scale factor of 0.5
        scaled_qty = ingredient.quantity * 0.5
        assert scaled_qty == 1.25


class TestRecipeModel:
    """Test Recipe model validation."""
    
    def test_recipe_creation(self, sample_recipe):
        """Test creating a recipe with valid data."""
        assert sample_recipe.id == "test-recipe-001"
        assert sample_recipe.servings > 0
        assert len(sample_recipe.ingredients) > 0
    
    def test_recipe_validation_servings(self):
        """Test servings validation."""
        with pytest.raises(ValueError):
            Recipe(
                id="test",
                title="Test",
                description="Test",
                servings=0,  # Invalid
                prep_time_minutes=10,
                cook_time_minutes=10,
                total_time_minutes=20,
                difficulty="easy",
                ingredients=[],
                steps=[]
            )
    
    def test_ingredient_validation(self):
        """Test ingredient quantity validation."""
        with pytest.raises(ValueError):
            Ingredient(name="test", quantity=-1, unit="g")  # Negative quantity
    
    def test_cooking_step_ordering(self, sample_recipe):
        """Test cooking steps are properly ordered."""
        steps = sample_recipe.steps
        for i, step in enumerate(steps):
            assert step.step_number == i + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
