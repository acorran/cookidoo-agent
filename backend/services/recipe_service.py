"""
Recipe service for handling recipe operations.
"""

import logging
from typing import List, Optional
import httpx
from models.recipe import Recipe, RecipeModificationRequest, RecipeModificationResponse
from config.settings import get_settings

logger = logging.getLogger(__name__)


class RecipeService:
    """Service for recipe-related operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.mcp_client = httpx.AsyncClient(
            base_url=self.settings.mcp_server_url,
            timeout=self.settings.mcp_timeout
        )
    
    async def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """
        Retrieve a recipe by ID.
        
        Args:
            recipe_id: Recipe identifier
            
        Returns:
            Recipe object or None if not found
        """
        try:
            # TODO: Fetch from Databricks or MCP server
            logger.info(f"Fetching recipe: {recipe_id}")
            
            # Placeholder implementation
            response = await self.mcp_client.get(f"/api/recipes/{recipe_id}")
            
            if response.status_code == 200:
                recipe_data = response.json()
                return Recipe(**recipe_data)
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Error fetching recipe {recipe_id}: {str(e)}", exc_info=True)
            raise
    
    async def search_recipes(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        dietary_restrictions: Optional[List[str]] = None,
        max_results: int = 20
    ) -> List[Recipe]:
        """
        Search for recipes.
        
        Args:
            query: Search query text
            tags: Optional tag filters
            dietary_restrictions: Optional dietary filters
            max_results: Maximum number of results
            
        Returns:
            List of matching recipes
        """
        try:
            logger.info(f"Searching recipes: {query}")
            
            # TODO: Implement vector search in Databricks
            # For now, use MCP server search
            params = {
                "q": query,
                "limit": max_results
            }
            if tags:
                params["tags"] = ",".join(tags)
            if dietary_restrictions:
                params["dietary"] = ",".join(dietary_restrictions)
            
            response = await self.mcp_client.get("/api/recipes/search", params=params)
            response.raise_for_status()
            
            recipes_data = response.json()["results"]
            return [Recipe(**r) for r in recipes_data]
            
        except Exception as e:
            logger.error(f"Error searching recipes: {str(e)}", exc_info=True)
            raise
    
    async def modify_recipe(
        self,
        recipe_id: str,
        modification_prompt: str,
        preserve_servings: bool = True,
        dietary_restrictions: Optional[List[str]] = None
    ) -> RecipeModificationResponse:
        """
        Modify a recipe using LLM.
        
        Args:
            recipe_id: Original recipe ID
            modification_prompt: Natural language modification request
            preserve_servings: Whether to keep original servings
            dietary_restrictions: Apply dietary filters
            
        Returns:
            RecipeModificationResponse with original and modified recipes
        """
        try:
            logger.info(f"Modifying recipe {recipe_id}: {modification_prompt}")
            
            # Step 1: Get original recipe
            original_recipe = await self.get_recipe(recipe_id)
            if not original_recipe:
                raise ValueError(f"Recipe {recipe_id} not found")
            
            # Step 2: Call AgentBricks to modify recipe
            # TODO: Implement AgentBricks integration
            # For now, create a placeholder modified recipe
            
            modified_recipe = original_recipe.copy(deep=True)
            modified_recipe.id = f"modified_{recipe_id}"
            modified_recipe.title = f"{original_recipe.title} (Modified)"
            
            modifications_applied = [
                f"Applied modification: {modification_prompt}"
            ]
            
            return RecipeModificationResponse(
                original_recipe=original_recipe,
                modified_recipe=modified_recipe,
                modifications_applied=modifications_applied,
                modification_notes=f"Recipe modified based on: {modification_prompt}",
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error modifying recipe: {str(e)}", exc_info=True)
            raise
    
    async def save_recipe(
        self,
        recipe: Recipe,
        save_to_cookidoo: bool = True
    ) -> dict:
        """
        Save a recipe to Databricks and optionally to Cookidoo.
        
        Args:
            recipe: Recipe to save
            save_to_cookidoo: Whether to save to Cookidoo platform
            
        Returns:
            Dictionary with save results
        """
        try:
            logger.info(f"Saving recipe: {recipe.title}")
            
            # TODO: Save to Databricks
            # TODO: Optionally save to Cookidoo via MCP
            
            result = {
                "recipe_id": recipe.id or f"saved_{recipe.title.replace(' ', '_')}",
                "saved_to_databricks": True,
                "saved_to_cookidoo": False
            }
            
            if save_to_cookidoo:
                # Call MCP server to save to Cookidoo
                response = await self.mcp_client.post(
                    "/api/recipes/save",
                    json=recipe.dict()
                )
                if response.status_code == 200:
                    result["saved_to_cookidoo"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error saving recipe: {str(e)}", exc_info=True)
            raise
    
    async def scale_recipe(self, recipe_id: str, target_servings: int) -> Recipe:
        """
        Scale a recipe to different serving size.
        
        Args:
            recipe_id: Recipe to scale
            target_servings: Desired number of servings
            
        Returns:
            Scaled recipe
        """
        try:
            logger.info(f"Scaling recipe {recipe_id} to {target_servings} servings")
            
            recipe = await self.get_recipe(recipe_id)
            if not recipe:
                raise ValueError(f"Recipe {recipe_id} not found")
            
            if recipe.servings == target_servings:
                return recipe
            
            # Calculate scaling factor
            scale_factor = target_servings / recipe.servings
            
            # Scale ingredients
            scaled_recipe = recipe.copy(deep=True)
            scaled_recipe.servings = target_servings
            
            for ingredient in scaled_recipe.ingredients:
                ingredient.quantity = ingredient.quantity * scale_factor
            
            return scaled_recipe
            
        except Exception as e:
            logger.error(f"Error scaling recipe: {str(e)}", exc_info=True)
            raise
