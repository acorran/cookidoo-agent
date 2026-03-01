"""
Dependency injection for FastAPI endpoints.
"""

from functools import lru_cache
from services.recipe_service import RecipeService
from services.chat_service import ChatService
from services.shopping_service import ShoppingService


@lru_cache()
def get_recipe_service() -> RecipeService:
    """Get or create RecipeService instance."""
    return RecipeService()


@lru_cache()
def get_chat_service() -> ChatService:
    """Get or create ChatService instance."""
    return ChatService()


@lru_cache()
def get_shopping_service() -> ShoppingService:
    """Get or create ShoppingService instance."""
    return ShoppingService()
