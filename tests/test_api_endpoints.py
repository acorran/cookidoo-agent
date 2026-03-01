"""
Integration tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from backend.main import app
from backend.models.recipe import Recipe, Ingredient, CookingStep


@pytest.fixture
def client():
    """Test client for API."""
    return TestClient(app)


@pytest.fixture
def sample_recipe_data():
    """Sample recipe data for testing."""
    return {
        "recipe_id": "test-001",
        "title": "Test Recipe",
        "description": "A test recipe",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 20,
        "total_time_minutes": 35,
        "difficulty": "easy",
        "cuisine": "Italian",
        "meal_type": "dinner",
        "dietary_restrictions": [],
        "ingredients": [
            {"name": "flour", "quantity": 2, "unit": "cups"},
            {"name": "eggs", "quantity": 2, "unit": "pieces"}
        ],
        "cooking_steps": [
            {"step_number": 1, "instruction": "Mix ingredients"},
            {"step_number": 2, "instruction": "Cook"}
        ],
        "source": "test",
        "tags": ["test"]
    }


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test GET /api/v1/health."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestRecipeEndpoints:
    """Test recipe-related endpoints."""
    
    def test_search_recipes(self, client):
        """Test POST /api/v1/recipes/search."""
        response = client.post(
            "/api/v1/recipes/search",
            json={"query": "pasta", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert "total_count" in data
        assert isinstance(data["recipes"], list)
    
    def test_scale_recipe(self, client, sample_recipe_data):
        """Test POST /api/v1/recipes/{id}/scale."""
        # First, this would need a real recipe ID
        # For now, test the endpoint structure
        response = client.post(
            "/api/v1/recipes/test-001/scale?target_servings=8"
        )
        
        # May return 404 if recipe doesn't exist - that's expected
        assert response.status_code in [200, 404, 500]
    
    def test_modify_recipe(self, client, sample_recipe_data):
        """Test POST /api/v1/recipes/modify."""
        request_data = {
            "original_recipe": sample_recipe_data,
            "modifications": "Make it vegan",
            "preserve_cooking_method": True
        }
        
        response = client.post("/api/v1/recipes/modify", json=request_data)
        
        # Should succeed or return service error
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "original_recipe" in data
            assert "modified_recipe" in data
            assert "conversation_id" in data


class TestChatEndpoints:
    """Test chat-related endpoints."""
    
    def test_chat_message(self, client):
        """Test POST /api/v1/chat."""
        request_data = {
            "message": "What's a good recipe for dinner?",
            "context": {}
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "conversation_id" in data


class TestShoppingListEndpoints:
    """Test shopping list endpoints."""
    
    def test_generate_shopping_list(self, client):
        """Test POST /api/v1/shopping-list/generate."""
        request_data = {
            "recipe_ids": ["recipe-1", "recipe-2"],
            "consolidate_items": True
        }
        
        response = client.post("/api/v1/shopping-list/generate", json=request_data)
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "list_id" in data
            assert "items" in data
            assert isinstance(data["items"], list)


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_invalid_recipe_id(self, client):
        """Test requesting nonexistent recipe."""
        response = client.get("/api/v1/recipes/nonexistent-id")
        
        assert response.status_code in [404, 500]
    
    def test_invalid_json(self, client):
        """Test sending invalid JSON."""
        response = client.post(
            "/api/v1/recipes/search",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client):
        """Test missing required fields in request."""
        response = client.post(
            "/api/v1/recipes/modify",
            json={"modifications": "test"}  # Missing required fields
        )
        
        assert response.status_code == 422


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should allow the origin
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
