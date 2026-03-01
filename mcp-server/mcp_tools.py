"""
MCP Protocol Tools for Cookidoo API Integration.

Exposes Cookidoo operations as MCP tools using the fastmcp library,
enabling Databricks agents and other MCP clients to discover and call
these tools via the Model Context Protocol (SSE transport).

This module runs alongside the REST API (server.py) and provides
the same functionality through the MCP protocol.
"""

import logging
import os
from typing import Dict, List, Optional

from fastmcp import FastMCP

# Import cookidoo-api
try:
    from cookidoo_api import Cookidoo

    COOKIDOO_AVAILABLE = True
except ImportError:
    COOKIDOO_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="cookidoo-mcp",
    description=(
        "MCP server for Cookidoo recipe platform. Provides tools for "
        "searching, retrieving, modifying, and saving recipes, as well as "
        "managing shopping lists via the Cookidoo API."
    ),
)


# ---------------------------------------------------------------------------
# Session-level client management
# ---------------------------------------------------------------------------

_client_cache: Dict[str, "Cookidoo"] = {}


def _get_client(
    email: Optional[str] = None, password: Optional[str] = None
) -> "Cookidoo":
    """
    Return an authenticated Cookidoo client, using cached session if available.

    Credentials fall back to environment variables when not provided.

    Args:
        email: Cookidoo account email (optional, falls back to env).
        password: Cookidoo account password (optional, falls back to env).

    Returns:
        Authenticated Cookidoo client instance.

    Raises:
        RuntimeError: If cookidoo-api is not installed.
        ValueError: If credentials are missing.
    """
    if not COOKIDOO_AVAILABLE:
        raise RuntimeError(
            "cookidoo-api is not installed. Run: pip install cookidoo-api"
        )

    email = email or os.getenv("COOKIDOO_EMAIL")
    password = password or os.getenv("COOKIDOO_PASSWORD")

    if not email or not password:
        raise ValueError(
            "Cookidoo credentials required. Provide email/password or set "
            "COOKIDOO_EMAIL and COOKIDOO_PASSWORD environment variables."
        )

    cache_key = email
    if cache_key in _client_cache:
        return _client_cache[cache_key]

    client = Cookidoo()
    client.login(email, password)
    _client_cache[cache_key] = client
    logger.info(f"Authenticated Cookidoo client for {email[:3]}***")
    return client


# ---------------------------------------------------------------------------
# MCP Tools – Discovery, Retrieval, Modification, Shopping
# ---------------------------------------------------------------------------


@mcp.tool()
def search_recipes(query: str, limit: int = 20) -> List[Dict]:
    """
    Search for recipes on the Cookidoo platform.

    Args:
        query: Natural language search query (e.g. "vegan pasta", "quick chicken dinner").
        limit: Maximum number of results to return (default 20).

    Returns:
        List of recipe summaries with id, title, description, and tags.
    """
    try:
        client = _get_client()
        results = client.search_recipes(query)
        return results[:limit] if results else []
    except Exception as exc:
        logger.error(f"search_recipes failed: {exc}")
        return [{"error": str(exc)}]


@mcp.tool()
def get_recipe(recipe_id: str) -> Dict:
    """
    Retrieve full details for a specific Cookidoo recipe.

    Args:
        recipe_id: The unique Cookidoo recipe identifier.

    Returns:
        Complete recipe including title, ingredients, steps, nutritional info.
    """
    try:
        client = _get_client()
        return client.get_recipe(recipe_id)
    except Exception as exc:
        logger.error(f"get_recipe failed for {recipe_id}: {exc}")
        return {"error": str(exc)}


@mcp.tool()
def save_recipe(recipe_data: Dict) -> Dict:
    """
    Save a new or modified recipe to Cookidoo's 'My Recipes' collection.

    Args:
        recipe_data: Recipe dictionary containing at minimum title, ingredients, and steps.

    Returns:
        Confirmation with saved recipe id and status.
    """
    try:
        client = _get_client()
        result = client.create_recipe(recipe_data)
        return {"status": "saved", "result": result}
    except Exception as exc:
        logger.error(f"save_recipe failed: {exc}")
        return {"error": str(exc)}


@mcp.tool()
def get_shopping_list() -> List[Dict]:
    """
    Retrieve the current shopping list from Cookidoo.

    Returns:
        List of shopping list items with ingredient names, quantities, and units.
    """
    try:
        client = _get_client()
        return client.get_shopping_list()
    except Exception as exc:
        logger.error(f"get_shopping_list failed: {exc}")
        return [{"error": str(exc)}]


@mcp.tool()
def get_collections() -> List[Dict]:
    """
    List all recipe collections for the authenticated Cookidoo user.

    Returns:
        List of collection names and recipe counts.
    """
    try:
        client = _get_client()
        return client.get_collections()
    except Exception as exc:
        logger.error(f"get_collections failed: {exc}")
        return [{"error": str(exc)}]


@mcp.tool()
def modify_recipe(
    recipe_id: str,
    modifications: Dict,
) -> Dict:
    """
    Retrieve a recipe, apply modifications, and return the updated version.

    This does NOT save the recipe automatically – call save_recipe() to persist.

    Args:
        recipe_id: The original recipe ID to modify.
        modifications: Dictionary of changes to apply. Supported keys:
            - title (str): New recipe title.
            - servings (int): New serving count (ingredients scale automatically).
            - add_ingredients (list[dict]): Ingredients to add.
            - remove_ingredients (list[str]): Ingredient names to remove.
            - replace_ingredients (dict[str, dict]): Map of old name -> new ingredient.
            - add_steps (list[str]): Steps to append.
            - add_tags (list[str]): Tags to add.

    Returns:
        Modified recipe dictionary ready for save_recipe().
    """
    try:
        client = _get_client()
        recipe = client.get_recipe(recipe_id)

        if not recipe or "error" in recipe:
            return {"error": f"Recipe {recipe_id} not found"}

        # Apply modifications
        if "title" in modifications:
            recipe["title"] = modifications["title"]

        if "servings" in modifications:
            original_servings = recipe.get("servings", 1)
            new_servings = modifications["servings"]
            scale_factor = new_servings / max(original_servings, 1)
            recipe["servings"] = new_servings

            # Scale ingredient quantities
            for ing in recipe.get("ingredients", []):
                if "quantity" in ing and ing["quantity"]:
                    ing["quantity"] = round(ing["quantity"] * scale_factor, 2)

        if "add_ingredients" in modifications:
            recipe.setdefault("ingredients", []).extend(
                modifications["add_ingredients"]
            )

        if "remove_ingredients" in modifications:
            names_to_remove = {n.lower() for n in modifications["remove_ingredients"]}
            recipe["ingredients"] = [
                ing
                for ing in recipe.get("ingredients", [])
                if ing.get("name", "").lower() not in names_to_remove
            ]

        if "replace_ingredients" in modifications:
            for old_name, new_ing in modifications["replace_ingredients"].items():
                for i, ing in enumerate(recipe.get("ingredients", [])):
                    if ing.get("name", "").lower() == old_name.lower():
                        recipe["ingredients"][i] = new_ing

        if "add_steps" in modifications:
            steps = recipe.setdefault("steps", [])
            start_num = max((s.get("step_number", 0) for s in steps), default=0)
            for j, instruction in enumerate(modifications["add_steps"], start=1):
                steps.append(
                    {
                        "step_number": start_num + j,
                        "instruction": instruction,
                    }
                )

        if "add_tags" in modifications:
            recipe.setdefault("tags", []).extend(modifications["add_tags"])

        recipe["_modified"] = True
        recipe["_original_id"] = recipe_id
        return recipe

    except Exception as exc:
        logger.error(f"modify_recipe failed for {recipe_id}: {exc}")
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# MCP Resources – contextual data for LLM agents
# ---------------------------------------------------------------------------


@mcp.resource("cookidoo://status")
def server_status() -> str:
    """Return MCP server health and capability summary."""
    return (
        "Cookidoo MCP Server v1.0.0\n"
        f"cookidoo-api available: {COOKIDOO_AVAILABLE}\n"
        "Tools: search_recipes, get_recipe, save_recipe, "
        "modify_recipe, get_shopping_list, get_collections\n"
        "Transports: SSE (port 8002), REST (port 8001)"
    )


# ---------------------------------------------------------------------------
# Entry point – run MCP server over SSE transport
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("MCP_SSE_PORT", "8002"))
    logger.info(f"Starting MCP SSE server on port {port}")
    mcp.run(transport="sse", port=port)
