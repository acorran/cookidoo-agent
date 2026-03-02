"""
Dependency injection for FastAPI endpoints.
"""

from functools import lru_cache
from ..services.recipe_service import RecipeService
from ..services.chat_service import ChatService
from ..services.shopping_service import ShoppingService
from ..services.cookidoo_service import CookidooService

# Module-level reference set during app startup lifespan.
_cookidoo_service: CookidooService | None = None


def set_cookidoo_service(service: CookidooService) -> None:
    """Called from lifespan to register the singleton."""
    global _cookidoo_service
    _cookidoo_service = service


def get_cookidoo_service() -> CookidooService:
    """FastAPI dependency that returns the live CookidooService."""
    if _cookidoo_service is None or not _cookidoo_service.is_connected:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Cookidoo service is not connected. Check credentials.",
        )
    return _cookidoo_service


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
