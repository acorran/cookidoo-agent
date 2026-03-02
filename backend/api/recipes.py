"""
Recipe API endpoints for modification, generation, and retrieval.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from ..models.recipe import (
    Recipe,
    RecipeModificationRequest,
    RecipeModificationResponse
)
from ..services.recipe_service import RecipeService
from ..services.cookidoo_service import CookidooService
from ..utils.dependencies import get_recipe_service, get_cookidoo_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Cookidoo live endpoints ──────────────────────────────────────────
# These must come BEFORE the /recipes/{recipe_id} wildcard route
# so FastAPI doesn't capture "collections" or "created" as a recipe_id.


@router.get("/recipes/collections")
async def get_collections(
    cookidoo: CookidooService = Depends(get_cookidoo_service),
):
    """
    List all custom collections with their recipes.

    Returns a list of collections, each containing its recipes
    with id, name, and total_time_minutes.
    """
    try:
        collections = await cookidoo.get_collections()
        total = sum(len(c["recipes"]) for c in collections)
        return {
            "collections": collections,
            "total_recipes": total,
        }
    except Exception as e:
        logger.error(f"Error fetching collections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recipes/created")
async def get_created_recipes(
    cookidoo: CookidooService = Depends(get_cookidoo_service),
):
    """
    List all user-created (custom) recipes.

    Returns recipes with id, name, has_image, image_url, total_time_minutes.
    """
    try:
        recipes = await cookidoo.get_created_recipes()
        return {"recipes": recipes, "count": len(recipes)}
    except Exception as e:
        logger.error(f"Error fetching created recipes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recipes/created/{recipe_id}")
async def get_created_recipe_detail(
    recipe_id: str,
    cookidoo: CookidooService = Depends(get_cookidoo_service),
):
    """
    Get full detail for a single created recipe.
    """
    try:
        detail = await cookidoo.get_recipe_detail(recipe_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recipe {recipe_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Generic recipe endpoints (wildcard must come after fixed paths) ──


@router.get("/recipes/{recipe_id}", response_model=Recipe)
async def get_recipe(
    recipe_id: str,
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    Retrieve a recipe by ID from Cookidoo.
    
    Args:
        recipe_id: Cookidoo recipe ID
        
    Returns:
        Recipe: Complete recipe information
    """
    try:
        recipe = await recipe_service.get_recipe(recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return recipe
    except Exception as e:
        logger.error(f"Error retrieving recipe {recipe_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recipes/search")
async def search_recipes(
    query: str = Query(..., min_length=2, description="Search query"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    dietary_restrictions: Optional[List[str]] = Query(None, description="Filter by dietary restrictions"),
    max_results: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    Search for recipes based on query and filters.
    
    Args:
        query: Search text
        tags: Optional tag filters
        dietary_restrictions: Optional dietary filters
        max_results: Maximum number of results
        
    Returns:
        List of matching recipes
    """
    try:
        recipes = await recipe_service.search_recipes(
            query=query,
            tags=tags,
            dietary_restrictions=dietary_restrictions,
            max_results=max_results
        )
        return {"results": recipes, "count": len(recipes)}
    except Exception as e:
        logger.error(f"Error searching recipes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recipes/modify", response_model=RecipeModificationResponse)
async def modify_recipe(
    request: RecipeModificationRequest,
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    Modify an existing recipe based on natural language instructions.
    
    This endpoint uses the LLM agent to intelligently modify recipes
    while maintaining structural integrity and culinary principles.
    
    Args:
        request: Recipe modification request with ID and instructions
        
    Returns:
        RecipeModificationResponse: Original and modified recipes with change notes
    """
    try:
        logger.info(f"Modifying recipe {request.recipe_id}: {request.modification_prompt}")
        
        result = await recipe_service.modify_recipe(
            recipe_id=request.recipe_id,
            modification_prompt=request.modification_prompt,
            preserve_servings=request.preserve_servings,
            dietary_restrictions=request.dietary_restrictions
        )
        
        logger.info(f"Successfully modified recipe {request.recipe_id}")
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid modification request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error modifying recipe: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recipes/save")
async def save_recipe(
    recipe: Recipe,
    save_to_cookidoo: bool = Query(True, description="Save to 'My Cookidoo Recipes'"),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    Save a recipe to the user's collection.
    
    Args:
        recipe: Recipe to save
        save_to_cookidoo: Whether to save to Cookidoo platform
        
    Returns:
        Success message with recipe ID
    """
    try:
        result = await recipe_service.save_recipe(
            recipe=recipe,
            save_to_cookidoo=save_to_cookidoo
        )
        
        return {
            "success": True,
            "recipe_id": result["recipe_id"],
            "message": "Recipe saved successfully",
            "saved_to_cookidoo": result.get("saved_to_cookidoo", False)
        }
        
    except Exception as e:
        logger.error(f"Error saving recipe: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recipes/{recipe_id}/scale")
async def scale_recipe(
    recipe_id: str,
    target_servings: int = Query(..., ge=1, le=100, description="Desired number of servings"),
    recipe_service: RecipeService = Depends(get_recipe_service)
):
    """
    Scale a recipe to a different number of servings.
    
    Args:
        recipe_id: Recipe ID to scale
        target_servings: Target number of servings
        
    Returns:
        Scaled recipe
    """
    try:
        scaled_recipe = await recipe_service.scale_recipe(recipe_id, target_servings)
        return scaled_recipe
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error scaling recipe: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
