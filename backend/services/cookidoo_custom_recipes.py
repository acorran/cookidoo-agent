"""
Client for Cookidoo custom recipe CRUD operations.

The upstream ``cookidoo-api`` library's ``add_custom_recipe_from`` method
constructs a ``recipeUrl`` using the full locale (``en-US``) in the path,
but the Cookidoo import service resolves recipe data via the short language
code (``en``).  This mismatch causes a 404 on the US locale.

Additionally, the library's JSON parser for custom recipes requires
``totalTime`` and ``prepTime`` ISO-8601 durations, which are absent when a
recipe is created from scratch via ``recipeName``.

This module provides a lightweight wrapper around the raw Cookidoo
``created-recipes`` REST API that:

* Uses the correct ``recipeUrl`` format (short language code).
* Handles both *import* (copy from existing) and *scratch* (new recipe)
  creation modes.
* Parses responses robustly, tolerating missing optional fields.
* Supports full CRUD: create, read, update (PATCH), delete and list.

Usage
-----
::

    from backend.services.cookidoo_custom_recipes import CookidooCustomRecipeClient

    client = CookidooCustomRecipeClient(session, cookidoo)
    recipe = await client.create_from_recipe("r412661", serving_size=4)
    updated = await client.update(recipe["recipeId"], name="My version")
    await client.delete(recipe["recipeId"])

The ``Cookidoo`` instance is used only to obtain the authenticated headers
and the API endpoint.  The ``aiohttp.ClientSession`` is shared with the
caller so connections are reused.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import aiohttp
from cookidoo_api import Cookidoo

logger = logging.getLogger(__name__)

# ── Cloudinary upload constants ──────────────────────────────────────
# These are public identifiers for Cookidoo's Cloudinary bucket.
# Security is enforced by the per-request signature, not the API key.
_CLOUDINARY_API_KEY = "993585863591145"
_CLOUDINARY_CLOUD_NAME = "vorwerk-users-gc"
_CLOUDINARY_UPLOAD_URL = (
    f"https://{_CLOUDINARY_CLOUD_NAME}.api-fast-eu.cloudinary.com/"
    f"v1_1/{_CLOUDINARY_CLOUD_NAME}/image/upload"
)
_UPLOAD_PRESET = "prod-customer-recipe-signed"

# Transformation used when downloading source recipe images from the CDN.
# The source recipe API returns image URLs with a ``{transformation}``
# placeholder.  Only pre-defined named transformations work on the
# private CDN.  ``t_web640_2x`` gives a ~1280px image — a good balance
# of quality and file size for custom recipe images.
_IMAGE_DOWNLOAD_TRANSFORMATION = "t_web640_2x"


class CookidooCustomRecipeClient:
    """Thin wrapper for Cookidoo custom-recipe REST operations.

    Parameters
    ----------
    session
        A shared ``aiohttp.ClientSession``.
    cookidoo
        An authenticated ``Cookidoo`` instance (used for headers/endpoint).
    """

    def __init__(self, session: aiohttp.ClientSession, cookidoo: Cookidoo) -> None:
        self._session = session
        self._cookidoo = cookidoo

    # ── helpers ────────────────────────────────────────────────────────

    @property
    def _headers(self) -> dict[str, str]:
        """Return a copy of the authenticated API headers."""
        return {**self._cookidoo._api_headers}

    @property
    def _language(self) -> str:
        """Full locale code used for endpoint paths (e.g. ``en-US``)."""
        return self._cookidoo._cfg.localization.language

    @property
    def _short_language(self) -> str:
        """Short language code for recipe data paths (e.g. ``en``)."""
        return self._language.split("-")[0]

    @property
    def _base_url(self) -> str:
        """Base API URL (e.g. ``https://us.tmmobile.vorwerk-digital.com``)."""
        return str(self._cookidoo.api_endpoint)

    def _collection_url(self) -> str:
        """``/created-recipes/{language}``"""
        return f"{self._base_url}/created-recipes/{self._language}"

    def _item_url(self, recipe_id: str) -> str:
        """``/created-recipes/{language}/{recipe_id}``"""
        return f"{self._collection_url()}/{recipe_id}"

    def _recipe_data_url(self, cookidoo_recipe_id: str) -> str:
        """URL the import service fetches recipe data from.

        Uses the *short* language code so the mobile API can resolve it.
        """
        return (
            f"{self._base_url}/recipes/recipe/"
            f"{self._short_language}/{cookidoo_recipe_id}"
        )

    def _signature_url(self) -> str:
        """``/created-recipes/{language}/image/signature``"""
        return f"{self._collection_url()}/image/signature"

    @staticmethod
    def _extract_source_image_url(source: dict[str, Any]) -> str:
        """Extract a downloadable image URL from source recipe data.

        The source API returns image URLs in ``carouselAssets`` or
        ``descriptiveAssets`` with a ``{transformation}`` placeholder.
        We look for the first ``image`` type asset and substitute the
        placeholder with a high-quality named transformation.

        Returns
        -------
        str
            A resolved image URL, or ``""`` if no image is found.
        """
        for key in ("carouselAssets", "descriptiveAssets"):
            for asset in source.get(key, []):
                if asset.get("type") != "image":
                    continue
                # Prefer "portrait" for recipe card display, then "square"
                for variant in ("portrait", "square", "landscape"):
                    url_template = asset.get(variant, "")
                    if url_template and "{transformation}" in url_template:
                        return url_template.replace(
                            "{transformation}",
                            _IMAGE_DOWNLOAD_TRANSFORMATION,
                        )
        return ""

    # ── Image upload ───────────────────────────────────────────────────

    async def _get_image_signature(self, timestamp: int) -> str:
        """Request a Cloudinary upload signature from the Cookidoo backend.

        Parameters
        ----------
        timestamp
            Unix epoch seconds used to bind the signature.

        Returns
        -------
        str
            The hex signature string.
        """
        body = {"timestamp": timestamp, "format": "jpg", "source": "uw"}
        async with self._session.post(
            self._signature_url(),
            headers=self._headers,
            json=body,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["signature"]

    async def upload_image(
        self,
        image_bytes: bytes,
        filename: str = "recipe.jpg",
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload an image to Cookidoo's Cloudinary bucket.

        Parameters
        ----------
        image_bytes
            Raw image file bytes (JPEG or PNG).
        filename
            Filename hint for the upload.
        content_type
            MIME type of the image.

        Returns
        -------
        str
            The image path to use in PATCH (e.g.
            ``prod/img/customer-recipe/abc123.jpg``).

        Raises
        ------
        aiohttp.ClientResponseError
            On signature or upload failure.
        """
        ts = int(time.time())
        signature = await self._get_image_signature(ts)

        form = aiohttp.FormData()
        form.add_field(
            "file",
            image_bytes,
            filename=filename,
            content_type=content_type,
        )
        form.add_field("upload_preset", _UPLOAD_PRESET)
        form.add_field("source", "uw")
        form.add_field("signature", signature)
        form.add_field("timestamp", str(ts))
        form.add_field("api_key", _CLOUDINARY_API_KEY)

        logger.info("Uploading image (%d bytes) to Cloudinary", len(image_bytes))

        async with self._session.post(
            _CLOUDINARY_UPLOAD_URL, data=form
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error("Cloudinary upload failed: %s %s", resp.status, text)
                resp.raise_for_status()

            data = await resp.json()
            public_id = data["public_id"]
            fmt = data.get("format", "jpg")
            image_path = f"{public_id}.{fmt}"
            logger.info("Uploaded image: %s", image_path)
            return image_path

    async def download_and_upload_image(self, image_url: str) -> str:
        """Download an image from a URL and upload it to Cloudinary.

        Useful for copying a source recipe's image to a custom recipe.

        Parameters
        ----------
        image_url
            The source image URL (e.g. from the Cookidoo CDN).

        Returns
        -------
        str
            The uploaded image path for use in PATCH.
        """
        logger.info("Downloading image from %s", image_url)
        async with self._session.get(image_url) as resp:
            resp.raise_for_status()
            image_bytes = await resp.read()
            ct = resp.content_type or "image/jpeg"

        # Extract filename from URL or use a default
        url_path = image_url.split("?")[0]
        filename = url_path.rsplit("/", 1)[-1] or "recipe.jpg"
        # Ensure it has a sensible extension
        if "." not in filename:
            filename = f"{filename}.jpg"

        return await self.upload_image(image_bytes, filename=filename, content_type=ct)

    # ── CRUD ───────────────────────────────────────────────────────────

    async def create_from_recipe(
        self,
        cookidoo_recipe_id: str,
        serving_size: int | None = None,
    ) -> dict[str, Any]:
        """Import an existing Cookidoo recipe as a custom recipe.

        Parameters
        ----------
        cookidoo_recipe_id
            The ``r*`` Cookidoo recipe ID (e.g. ``r412661``).
        serving_size
            Optional serving-size override.

        Returns
        -------
        dict
            Raw JSON response from the API containing ``recipeId``,
            ``recipeContent``, etc.

        Raises
        ------
        aiohttp.ClientResponseError
            On HTTP errors (4xx, 5xx).
        """
        body: dict[str, Any] = {
            "recipeUrl": self._recipe_data_url(cookidoo_recipe_id),
        }
        if serving_size is not None:
            body["servingSize"] = serving_size

        logger.info(
            "Creating custom recipe from %s (servings=%s)",
            cookidoo_recipe_id,
            serving_size,
        )

        async with self._session.post(
            self._collection_url(),
            headers=self._headers,
            json=body,
        ) as resp:
            resp.raise_for_status()
            data: dict[str, Any] = await resp.json()
            logger.info("Created custom recipe %s", data.get("recipeId"))
            return data

    async def create_blank(self, name: str) -> dict[str, Any]:
        """Create a new blank custom recipe.

        Parameters
        ----------
        name
            The recipe name / title.

        Returns
        -------
        dict
            Raw JSON response.
        """
        body = {"recipeName": name}
        logger.info("Creating blank custom recipe: %s", name)

        async with self._session.post(
            self._collection_url(),
            headers=self._headers,
            json=body,
        ) as resp:
            resp.raise_for_status()
            data: dict[str, Any] = await resp.json()
            logger.info("Created blank custom recipe %s", data.get("recipeId"))
            return data

    async def get_source_recipe(self, cookidoo_recipe_id: str) -> dict[str, Any]:
        """Fetch the full recipe data for a Cookidoo catalogue recipe.

        Parameters
        ----------
        cookidoo_recipe_id
            The ``r*`` Cookidoo recipe id (e.g. ``r412661``).

        Returns
        -------
        dict
            Raw recipe JSON from the ``/recipes/recipe/`` endpoint.

        Raises
        ------
        aiohttp.ClientResponseError
            On HTTP errors.
        """
        url = self._recipe_data_url(cookidoo_recipe_id)
        async with self._session.get(url, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def copy_recipe(
        self,
        cookidoo_recipe_id: str,
        *,
        serving_size: int | None = None,
        name_prefix: str = "",
        copy_image: bool = True,
    ) -> dict[str, Any]:
        """Copy a Cookidoo catalogue recipe as a new custom recipe.

        This performs a **client-side import**: it fetches the source
        recipe data, creates a blank custom recipe, then PATCHes it with
        the extracted content (name, ingredients, steps, times, image).

        This bypasses the server-side ``recipeUrl`` import, which is
        currently broken (returns ``recipeDataMissing`` 404).

        Parameters
        ----------
        cookidoo_recipe_id
            The ``r*`` Cookidoo recipe id (e.g. ``r412661``).
        serving_size
            Override serving size.  If ``None``, uses the source recipe's
            default.
        name_prefix
            Optional prefix prepended to the recipe name.
        copy_image
            Whether to download the source recipe's image and upload it
            to Cloudinary.  Defaults to ``True``.

        Returns
        -------
        dict
            The full custom recipe JSON (from a follow-up GET).
        """
        # 1. Fetch source recipe data
        source = await self.get_source_recipe(cookidoo_recipe_id)
        title = source.get("title", cookidoo_recipe_id)

        # 2. Extract ingredients as formatted strings
        ingredients: list[str] = []
        for group in source.get("recipeIngredientGroups", []):
            for ing in group.get("recipeIngredients", []):
                qty = ing.get("quantity", {}).get("value", "")
                unit = ing.get("unitNotation", "")
                name_text = ing.get("ingredientNotation", "")
                prep = ing.get("preparation", "")
                parts = [str(qty), unit, name_text]
                if prep:
                    parts.append(prep)
                ingredients.append(" ".join(p for p in parts if p))

        # 3. Extract instructions as formatted strings (strip HTML tags)
        instructions: list[str] = []
        for group in source.get("recipeStepGroups", []):
            for step in group.get("recipeSteps", []):
                text = step.get("formattedText", "")
                text = re.sub(r"<[^>]+>", "", text)  # strip HTML tags
                if text:
                    instructions.append(text)

        # 4. Extract times
        times = {t["type"]: t["quantity"]["value"] for t in source.get("times", [])}
        active_time = times.get("activeTime")
        total_time = times.get("totalTime")

        # 5. Copy image — download source recipe image from the CDN and
        #    re-upload it to Cookidoo's Cloudinary bucket.  The source API
        #    returns image URLs with a ``{transformation}`` placeholder
        #    that must be replaced with a named transformation.
        image_path = ""
        if copy_image:
            img_url = self._extract_source_image_url(source)
            if img_url:
                try:
                    image_path = await self.download_and_upload_image(img_url)
                except Exception:
                    logger.warning(
                        "Failed to copy image for %s, continuing without",
                        cookidoo_recipe_id,
                        exc_info=True,
                    )

        # 6. Extract serving size
        ss = source.get("servingSize", {})
        servings = serving_size or (
            int(ss["quantity"]["value"]) if ss and "quantity" in ss else 4
        )

        # 7. Extract tools
        tools = source.get("thermomixVersions", ["TM6"])

        # 8. Create blank + patch
        recipe_name = f"{name_prefix}{title}" if name_prefix else title
        blank = await self.create_blank(recipe_name)
        new_id = blank["recipeId"]

        logger.info(
            "Client-side import of %s -> %s (%s)",
            cookidoo_recipe_id,
            new_id,
            recipe_name,
        )

        await self.update(
            new_id,
            name=recipe_name,
            ingredients=ingredients,
            instructions=instructions,
            serving_size=servings,
            tools=tools,
            prep_time=active_time,
            total_time=total_time,
            image=image_path,
        )

        # 9. Read back the full recipe to return consistent data
        return await self.get(new_id)

    async def get(self, recipe_id: str) -> dict[str, Any]:
        """Fetch a single custom recipe by its ULID.

        Parameters
        ----------
        recipe_id
            The custom recipe ULID (e.g. ``01KDH4EXTZE5WBVQB35QCQQBFQ``).

        Returns
        -------
        dict
            Full recipe JSON.
        """
        async with self._session.get(
            self._item_url(recipe_id),
            headers=self._headers,
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def list_all(self) -> dict[str, Any]:
        """List all custom recipes for the authenticated user.

        Returns
        -------
        dict
            JSON with ``meta`` and ``items`` keys.
        """
        async with self._session.get(
            self._collection_url(),
            headers=self._headers,
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def update(
        self,
        recipe_id: str,
        *,
        name: str,
        ingredients: list[str] | None = None,
        instructions: list[str] | None = None,
        serving_size: int = 4,
        tools: list[str] | None = None,
        prep_time: int | None = None,
        cook_time: int | None = None,
        total_time: int | None = None,
        image: str = "",
    ) -> dict[str, Any]:
        """Update a custom recipe via PATCH.

        The Cookidoo PATCH endpoint requires **all** fields in the request
        body.  Callers must therefore provide at least ``name``.  Omitted
        optional fields receive sensible defaults (empty lists, zero times).

        Parameters
        ----------
        recipe_id
            Custom recipe ULID.
        name
            Recipe name (required).
        ingredients
            List of ingredient strings (e.g. ``["1 cup flour", "2 eggs"]``).
        instructions
            List of instruction step strings.
        serving_size
            Number of servings (default 4).
        tools
            List of required tools (default ``["TM6"]``).
        prep_time
            Preparation time in seconds, or ``None``.
        cook_time
            Cooking time in seconds, or ``None``.
        total_time
            Total time in seconds, or ``None``.
        image
            Image URL, or empty string for the default placeholder.

        Returns
        -------
        dict
            Updated recipe JSON.
        """
        body: dict[str, Any] = {
            "name": name,
            "image": image,
            "isImageOwnedByUser": bool(image),
            "tools": tools or ["TM6"],
            "yield": {"value": serving_size, "unitText": "portion"},
            "prepTime": prep_time,
            "cookTime": cook_time,
            "totalTime": total_time,
            "ingredients": [
                {"type": "INGREDIENT", "text": text}
                for text in (ingredients or [])
            ],
            "instructions": [
                {"type": "STEP", "text": text}
                for text in (instructions or [])
            ],
        }

        logger.info("Updating custom recipe %s", recipe_id)

        async with self._session.patch(
            self._item_url(recipe_id),
            headers=self._headers,
            json=body,
        ) as resp:
            resp.raise_for_status()
            if resp.status == 204:
                return {}
            return await resp.json()

    async def delete(self, recipe_id: str) -> None:
        """Delete a custom recipe.

        Parameters
        ----------
        recipe_id
            Custom recipe ULID.
        """
        logger.info("Deleting custom recipe %s", recipe_id)
        async with self._session.delete(
            self._item_url(recipe_id),
            headers=self._headers,
        ) as resp:
            resp.raise_for_status()
        logger.info("Deleted custom recipe %s", recipe_id)
