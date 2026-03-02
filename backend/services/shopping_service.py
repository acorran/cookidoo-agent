"""
Shopping list service for generating and managing shopping lists.
"""

import logging
from typing import List, Dict, Optional
import uuid
from ..models.shopping import ShoppingListRequest, ShoppingList, ShoppingListItem, IngredientCategory
from ..models.recipe import Recipe
from ..services.recipe_service import RecipeService
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class ShoppingService:
    """Service for shopping list operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.recipe_service = RecipeService()
    
    async def generate_shopping_list(
        self,
        recipe_ids: List[str],
        serving_adjustments: Optional[Dict[str, int]] = None,
        group_by_category: bool = True,
        consolidate_duplicates: bool = True
    ) -> ShoppingList:
        """
        Generate a consolidated shopping list from multiple recipes.
        
        Args:
            recipe_ids: List of recipe IDs
            serving_adjustments: Optional serving size adjustments per recipe
            group_by_category: Whether to organize by category
            consolidate_duplicates: Whether to combine duplicate ingredients
            
        Returns:
            ShoppingList with all items
        """
        try:
            logger.info(f"Generating shopping list for {len(recipe_ids)} recipes")
            
            # Fetch all recipes
            recipes = []
            for recipe_id in recipe_ids:
                recipe = await self.recipe_service.get_recipe(recipe_id)
                if not recipe:
                    logger.warning(f"Recipe {recipe_id} not found, skipping")
                    continue
                
                # Scale if serving adjustment specified
                if serving_adjustments and recipe_id in serving_adjustments:
                    target_servings = serving_adjustments[recipe_id]
                    recipe = await self.recipe_service.scale_recipe(recipe_id, target_servings)
                
                recipes.append(recipe)
            
            # Consolidate ingredients
            items = self._consolidate_ingredients(recipes, consolidate_duplicates)
            
            # Categorize if requested
            if group_by_category:
                items = self._categorize_ingredients(items)
            
            # Create shopping list
            shopping_list = ShoppingList(
                id=f"list_{uuid.uuid4().hex[:12]}",
                name=f"Shopping List for {len(recipes)} Recipes",
                items=items,
                recipe_count=len(recipes)
            )
            
            logger.info(f"Generated shopping list with {len(items)} items")
            return shopping_list
            
        except Exception as e:
            logger.error(f"Error generating shopping list: {str(e)}", exc_info=True)
            raise
    
    def _consolidate_ingredients(
        self,
        recipes: List[Recipe],
        consolidate: bool
    ) -> List[ShoppingListItem]:
        """Consolidate ingredients from multiple recipes."""
        
        ingredient_map = {}
        
        for recipe in recipes:
            for ingredient in recipe.ingredients:
                key = ingredient.name.lower()
                
                if consolidate and key in ingredient_map:
                    # Add to existing ingredient
                    existing = ingredient_map[key]
                    
                    # Only consolidate if units match
                    if existing.unit == ingredient.unit:
                        existing.quantity += ingredient.quantity
                        existing.source_recipes.append(recipe.id)
                    else:
                        # Different units, create separate entry
                        key_with_unit = f"{key}_{ingredient.unit}"
                        ingredient_map[key_with_unit] = ShoppingListItem(
                            ingredient_name=ingredient.name,
                            quantity=ingredient.quantity,
                            unit=ingredient.unit,
                            source_recipes=[recipe.id]
                        )
                else:
                    # New ingredient
                    ingredient_map[key] = ShoppingListItem(
                        ingredient_name=ingredient.name,
                        quantity=ingredient.quantity,
                        unit=ingredient.unit,
                        source_recipes=[recipe.id]
                    )
        
        return list(ingredient_map.values())
    
    def _categorize_ingredients(
        self,
        items: List[ShoppingListItem]
    ) -> List[ShoppingListItem]:
        """Categorize ingredients for better organization."""
        
        # Simple categorization logic (can be enhanced with ML)
        produce_keywords = ['onion', 'tomato', 'lettuce', 'carrot', 'potato', 'pepper', 'garlic']
        dairy_keywords = ['milk', 'cheese', 'butter', 'cream', 'yogurt']
        meat_keywords = ['chicken', 'beef', 'pork', 'turkey', 'lamb']
        seafood_keywords = ['fish', 'salmon', 'shrimp', 'tuna', 'cod']
        spice_keywords = ['salt', 'pepper', 'cumin', 'paprika', 'oregano', 'basil']
        
        for item in items:
            name_lower = item.ingredient_name.lower()
            
            if any(keyword in name_lower for keyword in produce_keywords):
                item.category = IngredientCategory.PRODUCE
            elif any(keyword in name_lower for keyword in dairy_keywords):
                item.category = IngredientCategory.DAIRY
            elif any(keyword in name_lower for keyword in meat_keywords):
                item.category = IngredientCategory.MEAT
            elif any(keyword in name_lower for keyword in seafood_keywords):
                item.category = IngredientCategory.SEAFOOD
            elif any(keyword in name_lower for keyword in spice_keywords):
                item.category = IngredientCategory.SPICES
            else:
                item.category = IngredientCategory.PANTRY
        
        # Sort by category
        return sorted(items, key=lambda x: x.category.value)
    
    async def get_shopping_list(self, list_id: str) -> Optional[ShoppingList]:
        """
        Retrieve a saved shopping list.
        
        Args:
            list_id: Shopping list identifier
            
        Returns:
            ShoppingList or None if not found
        """
        try:
            logger.info(f"Retrieving shopping list: {list_id}")
            
            # TODO: Query from Databricks
            # Placeholder
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving shopping list: {str(e)}", exc_info=True)
            raise
    
    async def update_item_status(
        self,
        list_id: str,
        item_index: int,
        checked: bool
    ):
        """
        Update the checked status of a shopping list item.
        
        Args:
            list_id: Shopping list ID
            item_index: Index of item in list
            checked: Whether item is checked
        """
        try:
            logger.info(f"Updating item {item_index} in list {list_id} to checked={checked}")
            
            # TODO: Update in Databricks
            
        except Exception as e:
            logger.error(f"Error updating item status: {str(e)}", exc_info=True)
            raise
