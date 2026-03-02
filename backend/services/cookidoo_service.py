"""
Cookidoo connection manager for the backend.

Manages the lifecycle of an authenticated ``cookidoo-api`` client and
the custom-recipe wrapper.  Initialise once at application startup with
:meth:`connect`, use throughout the request lifecycle, and call
:meth:`disconnect` on shutdown.

Usage (in FastAPI lifespan)::

    service = CookidooService(settings)
    await service.connect()
    yield
    await service.disconnect()
"""

from __future__ import annotations

import logging
import os
from typing import Any

import aiohttp
from cookidoo_api import (
    Cookidoo,
    CookidooConfig,
    CookidooLocalizationConfig,
)

from .cookidoo_custom_recipes import CookidooCustomRecipeClient

logger = logging.getLogger(__name__)


class CookidooService:
    """Singleton-style service managing a shared Cookidoo session.

    Parameters
    ----------
    email : str
        Cookidoo account email.
    password : str
        Cookidoo account password.
    country_code : str
        Two-letter country code (default ``"us"``).
    language : str
        Full locale code (default ``"en-US"``).
    """

    def __init__(
        self,
        email: str,
        password: str,
        country_code: str = "us",
        language: str = "en-US",
    ) -> None:
        self._email = email
        self._password = password
        self._country_code = country_code
        self._language = language

        self._session: aiohttp.ClientSession | None = None
        self._cookidoo: Cookidoo | None = None
        self._custom_client: CookidooCustomRecipeClient | None = None
        self._connected = False

    # ── lifecycle ──────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Create session, authenticate, and build sub-clients."""
        if self._connected:
            logger.warning("CookidooService already connected")
            return

        localization = CookidooLocalizationConfig(
            country_code=self._country_code,
            language=self._language,
            url=f"https://cookidoo.thermomix.com/foundation/{self._language}",
        )
        cfg = CookidooConfig(
            localization=localization,
            email=self._email,
            password=self._password,
        )

        self._session = aiohttp.ClientSession()
        self._cookidoo = Cookidoo(self._session, cfg)
        await self._cookidoo.login()
        self._custom_client = CookidooCustomRecipeClient(
            self._session, self._cookidoo
        )
        self._connected = True
        logger.info("CookidooService connected and authenticated")

    async def disconnect(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._connected = False
        logger.info("CookidooService disconnected")

    # ── public accessors ───────────────────────────────────────────────

    @property
    def client(self) -> Cookidoo:
        """Return the authenticated ``Cookidoo`` instance."""
        assert self._cookidoo is not None, "CookidooService not connected"
        return self._cookidoo

    @property
    def custom_recipes(self) -> CookidooCustomRecipeClient:
        """Return the custom-recipe wrapper."""
        assert self._custom_client is not None, "CookidooService not connected"
        return self._custom_client

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ── high-level helpers used by API endpoints ───────────────────────

    async def get_collections(self) -> list[dict[str, Any]]:
        """Return custom collections with their recipes.

        Each item in the returned list has the shape::

            {
                "id": "...",
                "name": "Pasta",
                "description": "...",
                "recipes": [
                    {"id": "...", "name": "Mac and Cheese", "total_time_minutes": 20}
                ]
            }
        """
        collections = await self.client.get_custom_collections()
        result: list[dict[str, Any]] = []
        for coll in collections:
            recipes = []
            for chapter in coll.chapters:
                for recipe in chapter.recipes:
                    total_min = None
                    if recipe.total_time:
                        # total_time is an ISO-8601 duration like "PT20M"
                        total_min = _parse_iso_duration_minutes(recipe.total_time)
                    recipes.append({
                        "id": recipe.id,
                        "name": recipe.name,
                        "total_time_minutes": total_min,
                    })
            result.append({
                "id": coll.id,
                "name": coll.name,
                "description": getattr(coll, "description", ""),
                "recipes": recipes,
            })
        return result

    async def get_created_recipes(self) -> list[dict[str, Any]]:
        """Return all user-created (custom) recipes.

        Each item has the shape::

            {
                "id": "...",
                "name": "Guac",
                "has_image": true,
                "image_url": "...",
                "total_time_minutes": 15
            }
        """
        data = await self.custom_recipes.list_all()
        items = data.get("items") or data.get("createdRecipes") or []
        result: list[dict[str, Any]] = []
        for item in items:
            content = item.get("recipeContent", {})
            recipe_id = item.get("recipeId", "")
            name = content.get("name", "(untitled)")
            image = content.get("image", "")
            total_time = content.get("totalTime")

            total_min = None
            if total_time:
                total_min = _parse_iso_duration_minutes(total_time)

            # Build thumbnail URL if image exists
            image_url = _resolve_image_url(image, "t_web320")

            result.append({
                "id": recipe_id,
                "name": name,
                "has_image": bool(image_url),
                "image_url": image_url,
                "total_time_minutes": total_min,
            })
        return result

    async def get_recipe_detail(self, recipe_id: str) -> dict[str, Any] | None:
        """Get full detail for a single created recipe."""
        try:
            data = await self.custom_recipes.get(recipe_id)
            if not data:
                return None
            content = data.get("recipeContent", {})
            image = content.get("image", "")
            image_url = _resolve_image_url(image, "t_web640_2x")
            return {
                "id": data.get("recipeId", recipe_id),
                "name": content.get("name", ""),
                "image_url": image_url,
                "ingredients": content.get("ingredients", []),
                "instructions": content.get("instructions", []),
                "tools": content.get("tools", []),
                "yield": content.get("yield", {}),
                "prep_time_seconds": content.get("prepTime"),
                "cook_time_seconds": content.get("cookTime"),
                "total_time_seconds": content.get("totalTime"),
            }
        except Exception:
            logger.exception("Error fetching recipe %s", recipe_id)
            return None


def _resolve_image_url(image: str, transformation: str) -> str:
    """Build a displayable image URL from the recipe image field.

    The ``image`` value can be:
    - A full URL with ``{transformation}`` placeholder
    - A bare path like ``prod/img/customer-recipe/abc.jpg``
    - A placeholder URL from the pattern library (not a real image)
    - Empty string (no image)

    Returns a resolved URL or ``""`` if no image.
    """
    if not image:
        return ""
    # Discard pattern-library placeholder images
    if "placeholder" in image or "patternlib" in image:
        return ""
    if "{transformation}" in image:
        # Customer recipe images on ugc.assets.tmecosys.com don't support
        # named transformations — just strip the placeholder entirely.
        return image.replace("{transformation}/", "")
    if image.startswith("http"):
        return image
    # Bare path — prepend CDN base (no transformation for customer uploads)
    return (
        f"https://ugc.assets.tmecosys.com/image/upload/{image}"
    )


def _parse_iso_duration_minutes(value: Any) -> int | None:
    """Best-effort parse of ISO-8601 duration or seconds integer to minutes.

    Handles:
    - ``"PT20M"`` → 20
    - ``"PT1H30M"`` → 90
    - ``1200`` (seconds) → 20
    - ``"1200"`` (seconds string) → 20
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return max(1, round(value / 60))
    s = str(value).strip()
    if s.startswith("PT") or s.startswith("P"):
        import re

        hours = 0
        minutes = 0
        h_match = re.search(r"(\d+)H", s)
        m_match = re.search(r"(\d+)M", s)
        if h_match:
            hours = int(h_match.group(1))
        if m_match:
            minutes = int(m_match.group(1))
        total = hours * 60 + minutes
        return total if total > 0 else None
    # Try as raw seconds
    try:
        sec = int(s)
        return max(1, round(sec / 60))
    except ValueError:
        return None
