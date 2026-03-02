"""
Shopping list API endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from ..models.shopping import ShoppingListRequest, ShoppingList
from ..services.shopping_service import ShoppingService
from ..utils.dependencies import get_shopping_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/shopping-list/generate", response_model=ShoppingList)
async def generate_shopping_list(
    request: ShoppingListRequest,
    shopping_service: ShoppingService = Depends(get_shopping_service)
):
    """
    Generate a consolidated shopping list from multiple recipes.
    
    Intelligently combines ingredients, adjusts quantities, and
    organizes by category for efficient shopping.
    
    Args:
        request: Shopping list request with recipe IDs and options
        
    Returns:
        ShoppingList: Organized shopping list
    """
    try:
        logger.info(f"Generating shopping list for {len(request.recipe_ids)} recipes")
        
        shopping_list = await shopping_service.generate_shopping_list(
            recipe_ids=request.recipe_ids,
            serving_adjustments=request.serving_adjustments,
            group_by_category=request.group_by_category,
            consolidate_duplicates=request.consolidate_duplicates
        )
        
        logger.info(f"Generated shopping list with {len(shopping_list.items)} items")
        return shopping_list
        
    except ValueError as e:
        logger.warning(f"Invalid shopping list request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating shopping list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopping-list/{list_id}", response_model=ShoppingList)
async def get_shopping_list(
    list_id: str,
    shopping_service: ShoppingService = Depends(get_shopping_service)
):
    """
    Retrieve a saved shopping list.
    
    Args:
        list_id: Shopping list ID
        
    Returns:
        ShoppingList: The requested shopping list
    """
    try:
        shopping_list = await shopping_service.get_shopping_list(list_id)
        if not shopping_list:
            raise HTTPException(status_code=404, detail="Shopping list not found")
        return shopping_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving shopping list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/shopping-list/{list_id}/item/{item_index}/check")
async def toggle_item_checked(
    list_id: str,
    item_index: int,
    checked: bool,
    shopping_service: ShoppingService = Depends(get_shopping_service)
):
    """
    Mark a shopping list item as checked or unchecked.
    
    Args:
        list_id: Shopping list ID
        item_index: Index of the item in the list
        checked: Whether the item is checked
        
    Returns:
        Success message
    """
    try:
        await shopping_service.update_item_status(list_id, item_index, checked)
        return {"success": True, "message": "Item status updated"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating item status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
