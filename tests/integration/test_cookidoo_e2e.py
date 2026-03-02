"""
End-to-end tests against the real Cookidoo API.

These tests use the ``cookidoo-api`` library **and** the custom
``CookidooCustomRecipeClient`` to talk directly to Cookidoo.
They require valid credentials in ``.env`` and are only executed when
you opt in via the ``e2e`` marker.

Usage
-----
Run **all** e2e tests (in the recommended order)::

    pytest -m e2e -v

Run individual tests by keyword::

    pytest -m e2e -v -k test_get_recipe_details
    pytest -m e2e -v -k test_create
    pytest -m e2e -v -k cleanup

Run everything **except** cleanup (keep the test recipe around)::

    pytest -m "e2e and not e2e_cleanup" -v

Run **only** cleanup (delete any leftover test recipes from previous runs)::

    pytest -m e2e_cleanup -v

Test order
----------
Tests are ordered so that create runs before update, update before
read-back, and cleanup runs last.  ``pytest-ordering`` is NOT required
— we use explicit ``order`` marks only as hints and the tests are
designed to be safe to run individually.

The ``TEST_RECIPE_ID`` constant is the base Cookidoo recipe used for
read-only tests and import tests.  Change it if it becomes unavailable.
"""

import pytest
from cookidoo_api import (
    Cookidoo,
    CookidooShoppingRecipeDetails,
)

from backend.services.cookidoo_custom_recipes import CookidooCustomRecipeClient

# All async tests in this module share a single event loop so the
# module-scoped aiohttp.ClientSession works correctly.
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.asyncio(loop_scope="module"),
]

# A well-known, public Cookidoo recipe used as the source for
# "copy existing recipe" tests.  Replace if it goes away.
TEST_RECIPE_ID = "r412661"
TEST_RECIPE_NAME = "Buttermilk Mashed Potatoes"

# Prefix used to identify test-created recipes for cleanup.
# Matches anything starting with ``[E2E`` — catches both ``[E2E]`` and
# ``[E2E-TEST]`` prefixes from current and previous test runs.
_CLEANUP_PREFIX = "[E2E"

# Prefix added to custom recipe titles created by tests.
TEST_PREFIX = "[E2E-TEST]"


# ── 1. Read-only tests ────────────────────────────────────────────────────


class TestGetRecipe:
    """Read-only operations — safe to run at any time."""

    async def test_get_recipe_details(self, cookidoo_client: Cookidoo):
        """Fetch full recipe details for a known recipe ID."""
        recipe = await cookidoo_client.get_recipe_details(TEST_RECIPE_ID)

        assert isinstance(recipe, CookidooShoppingRecipeDetails)
        assert recipe.id == TEST_RECIPE_ID
        assert recipe.name  # non-empty title
        assert recipe.serving_size > 0
        assert len(recipe.ingredients) > 0
        print(f"\n  Recipe: {recipe.name}")
        print(f"  Servings: {recipe.serving_size}")
        print(f"  Ingredients: {len(recipe.ingredients)}")
        print(f"  Difficulty: {recipe.difficulty}")

    async def test_get_collections(self, cookidoo_client: Cookidoo):
        """List the user's managed collections."""
        collections = await cookidoo_client.get_managed_collections()

        assert isinstance(collections, list)
        print(f"\n  Managed collections: {len(collections)}")
        for c in collections[:5]:
            print(f"    - {c.name} ({len(c.chapters)} chapters)")

    async def test_get_custom_collections(self, cookidoo_client: Cookidoo):
        """List the user's custom collections and the recipes within each."""
        collections = await cookidoo_client.get_custom_collections()

        assert isinstance(collections, list)
        print(f"\n  Custom collections: {len(collections)}")
        total_recipes = 0
        for coll in collections:
            recipe_count = sum(len(ch.recipes) for ch in coll.chapters)
            total_recipes += recipe_count
            print(f"\n    [{coll.name}] ({recipe_count} recipes)")
            for chapter in coll.chapters:
                if chapter.name:
                    print(f"      Chapter: {chapter.name}")
                for recipe in chapter.recipes:
                    time_str = f" ({recipe.total_time // 60} min)" if recipe.total_time else ""
                    print(f"        - {recipe.name}{time_str}")
        print(f"\n  Total recipes across all custom collections: {total_recipes}")

    async def test_get_created_recipes(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
    ):
        """List all user-created (custom) recipes."""
        listing = await custom_recipe_client.list_all()
        items = listing.get("items", listing.get("createdRecipes", []))

        print(f"\n  Created recipes: {len(items)}")
        for item in items:
            rid = item.get("recipeId", item.get("id", "?"))
            content = item.get("recipeContent", {})
            name = content.get("name", "(untitled)")
            image = content.get("image", "")
            has_image = "img" if image and "placeholder" not in image else "   "
            print(f"    [{has_image}] {name}  ({rid})")

    async def test_get_user_info(self, cookidoo_client: Cookidoo):
        """Retrieve authenticated user information."""
        info = await cookidoo_client.get_user_info()

        assert info is not None
        print(f"\n  User info retrieved successfully")

    async def test_get_subscription(self, cookidoo_client: Cookidoo):
        """Check the user's active subscription."""
        subscription = await cookidoo_client.get_active_subscription()

        assert subscription is not None
        print(f"\n  Subscription: {subscription}")


# ── 2. Custom-recipe CRUD tests ────────────────────────────────────────


class TestCustomRecipeCRUD:
    """Full CRUD cycle covering both creation modes.

    Uses ``CookidooCustomRecipeClient`` which bypasses known bugs in
    the ``cookidoo-api`` library around locale handling and missing
    fields in blank recipes.

    Tests run in order:
      1. Create a brand-new blank recipe
      2. Update it with full content
      3. Read it back and verify
      4. Copy an existing Cookidoo recipe (with image)
      5. Tweak the imported copy
      6. Read the tweaked copy back
      7. Verify both appear in the listing
    """

    # ── A: Create from scratch ─────────────────────────────────────

    async def test_create_new_custom_recipe(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """Create a brand-new custom recipe from scratch."""
        data = await custom_recipe_client.create_blank(
            f"{TEST_PREFIX} New Recipe"
        )

        assert "recipeId" in data
        assert data["recipeId"]  # non-empty
        content = data.get("recipeContent", {})
        print(f"\n  Created new blank recipe")
        print(f"  ID:   {data['recipeId']}")
        print(f"  Name: {content.get('name', 'N/A')}")

        created_recipe_ids.append(data["recipeId"])

    async def test_update_new_recipe(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """PATCH the blank recipe with full content (ingredients, steps, times)."""
        if not created_recipe_ids:
            pytest.skip("No custom recipe was created in this session")

        recipe_id = created_recipe_ids[-1]
        updated = await custom_recipe_client.update(
            recipe_id,
            name=f"{TEST_PREFIX} Updated New Recipe",
            ingredients=[
                "500 g flour",
                "2 eggs",
                "250 ml milk",
                "1 pinch salt",
            ],
            instructions=[
                "Combine flour and salt in the mixing bowl.",
                "Add eggs and milk, mix 30 sec/speed 4.",
                "Let the batter rest for 15 minutes.",
                "Cook portions in a hot pan until golden.",
            ],
            serving_size=4,
            prep_time=600,   # 10 min
            cook_time=1200,  # 20 min
            total_time=1800,  # 30 min
        )

        assert isinstance(updated, dict)
        content = updated.get("recipeContent", updated)
        print(f"\n  Updated recipe {recipe_id}")
        print(f"  Name:         {content.get('name', 'N/A')}")
        print(f"  Ingredients:  {len(content.get('ingredients', []))}")
        print(f"  Instructions: {len(content.get('instructions', []))}")

    async def test_read_back_new_recipe(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """GET the new recipe back and verify the updated content."""
        if not created_recipe_ids:
            pytest.skip("No custom recipe was created in this session")

        recipe_id = created_recipe_ids[-1]
        data = await custom_recipe_client.get(recipe_id)
        content = data.get("recipeContent", data)

        assert f"{TEST_PREFIX} Updated New Recipe" in content.get("name", "")

        ingredients = (
            content.get("recipeIngredient")
            or content.get("ingredients", [])
        )
        instructions = (
            content.get("recipeInstructions")
            or content.get("instructions", [])
        )
        assert len(ingredients) == 4, f"Expected 4 ingredients, got {len(ingredients)}"
        assert len(instructions) == 4, f"Expected 4 instructions, got {len(instructions)}"

        recipe_yield = content.get("recipeYield") or content.get("yield", {})
        assert recipe_yield.get("value") == 4

        assert content.get("prepTime") is not None
        assert content.get("totalTime") is not None

        print(f"\n  Read back: {content.get('name')}")
        print(f"  Ingredients:  {ingredients}")
        print(f"  Instructions: {instructions}")
        print(f"  Yield:  {recipe_yield}")
        print(f"  Prep:   {content.get('prepTime')}")
        print(f"  Total:  {content.get('totalTime')}")

    # ── B: Copy an existing Cookidoo recipe ────────────────────────

    async def test_copy_existing_recipe(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """Copy an existing Cookidoo recipe as a custom recipe.

        Uses client-side import (fetch source data, create blank, PATCH)
        to work around the broken server-side ``recipeUrl`` import.

        Copies the full recipe content **including the image URL**
        from the source recipe ``{TEST_RECIPE_ID}`` ({TEST_RECIPE_NAME}).
        """
        import aiohttp as _aiohttp

        print(f"\n  Copying source recipe {TEST_RECIPE_ID} ({TEST_RECIPE_NAME})")

        try:
            data = await custom_recipe_client.copy_recipe(
                TEST_RECIPE_ID,
                serving_size=2,
                name_prefix=f"{TEST_PREFIX} [ImageTest] ",
            )
        except _aiohttp.ClientResponseError as exc:
            if exc.status in (404, 429):
                pytest.skip(
                    f"Recipe data endpoint returned {exc.status} for "
                    f"{TEST_RECIPE_ID}: {exc.message}"
                )
            raise

        assert "recipeId" in data
        content = data.get("recipeContent", {})

        # The copy should have the recipe name and image
        assert content.get("name"), "Copied recipe has no name"
        image = content.get("image", "")
        has_image = bool(image) and "placeholder" not in image

        # The copy should include the image from the source recipe
        assert has_image, (
            f"Expected image to be copied from {TEST_RECIPE_ID}, "
            f"but got: {image!r}"
        )
        assert "prod/img/customer-recipe/" in image, (
            f"Image path should be a Cloudinary customer-recipe path, "
            f"got: {image!r}"
        )

        print(f"  Created custom copy")
        print(f"  ID:     {data['recipeId']}")
        print(f"  Name:   {content.get('name')}")
        print(f"  Source: {TEST_RECIPE_ID}")
        print(f"  Image:  {'yes' if has_image else 'no'}")
        print(f"  Ingredients:  {len(content.get('recipeIngredient', []))}")
        print(f"  Instructions: {len(content.get('recipeInstructions', []))}")

        created_recipe_ids.append(data["recipeId"])

    async def test_upload_image_standalone(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """Upload an image to a custom recipe.

        If the ``TEST_IMAGE_PATH`` environment variable points to an image
        file, that file is used.  Otherwise a solid-colour JPEG is
        generated with Pillow.

        Creates a recipe, uploads the image, PATCHes the recipe with the
        Cloudinary path, and verifies the image is stored.
        """
        import os
        import pathlib

        image_file = os.environ.get("TEST_IMAGE_PATH", "")
        if image_file and pathlib.Path(image_file).is_file():
            p = pathlib.Path(image_file)
            jpeg_bytes = p.read_bytes()
            filename = p.name
            print(f"\n  Using image file: {p}  ({len(jpeg_bytes)} bytes)")
        else:
            import io
            from PIL import Image

            img = Image.new("RGB", (200, 200), color=(30, 100, 200))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            jpeg_bytes = buf.getvalue()
            filename = "test_blue.jpg"
            if image_file:
                print(f"\n  WARNING: TEST_IMAGE_PATH={image_file!r} not found, using generated image")
            else:
                print(f"\n  No TEST_IMAGE_PATH set, using generated 200x200 blue JPEG")
        assert len(jpeg_bytes) > 100, "Image is too small"

        # Create a blank recipe
        blank = await custom_recipe_client.create_blank(
            f"{TEST_PREFIX} [ImageTest] Upload Test"
        )
        recipe_id = blank["recipeId"]
        created_recipe_ids.append(recipe_id)

        # Upload the image
        image_path = await custom_recipe_client.upload_image(
            jpeg_bytes, filename=filename
        )
        assert image_path, "upload_image returned empty path"
        assert image_path.startswith("prod/img/customer-recipe/"), (
            f"Unexpected image path prefix: {image_path}"
        )
        assert image_path.endswith(".jpg"), f"Expected .jpg extension: {image_path}"

        # PATCH the recipe with the image
        await custom_recipe_client.update(
            recipe_id,
            name=f"{TEST_PREFIX} [ImageTest] Upload Test",
            image=image_path,
        )

        # Read back and verify
        data = await custom_recipe_client.get(recipe_id)
        content = data.get("recipeContent", {})
        stored_image = content.get("image", "")

        # The stored image is a full CDN URL, should contain our path
        assert "customer-recipe" in stored_image, (
            f"Expected customer-recipe in stored image: {stored_image}"
        )

        print(f"\n  Recipe: {recipe_id}")
        print(f"  Uploaded image path: {image_path}")
        print(f"  Stored image URL:    {stored_image[:80]}...")
        print(f"  JPEG size:           {len(jpeg_bytes)} bytes")

    async def test_tweak_imported_recipe(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """Update the imported copy — proves tweaking existing custom recipes works."""
        if len(created_recipe_ids) < 2:
            pytest.skip("Imported recipe not available (rate-limited or skipped)")

        recipe_id = created_recipe_ids[-1]  # the imported one
        updated = await custom_recipe_client.update(
            recipe_id,
            name=f"{TEST_PREFIX} Tweaked Mashed Potatoes",
            ingredients=[
                "1 kg potatoes, peeled and cubed",
                "100 ml buttermilk",
                "50 g butter",
                "1 tsp garlic powder",
                "salt and pepper to taste",
            ],
            instructions=[
                "Place potatoes in mixing bowl, cook 18 min/212°F/speed 1.",
                "Add buttermilk, butter, garlic powder, salt and pepper.",
                "Mix 15 sec/speed 5. Scrape down sides.",
                "Mix further 10 sec/speed 7 until smooth.",
                "Serve hot with a knob of butter on top.",
            ],
            serving_size=6,
            prep_time=600,
            cook_time=1080,
            total_time=1680,
        )

        content = updated.get("recipeContent", updated)
        print(f"\n  Tweaked imported recipe {recipe_id}")
        print(f"  New name:  {content.get('name')}")
        print(f"  Servings:  6")
        print(f"  Ingredients:  {len(content.get('ingredients', []))}")
        print(f"  Instructions: {len(content.get('instructions', []))}")

    async def test_read_back_tweaked_recipe(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """Verify the tweaked imported recipe reads back correctly."""
        if len(created_recipe_ids) < 2:
            pytest.skip("Imported recipe not available (rate-limited or skipped)")

        recipe_id = created_recipe_ids[-1]
        data = await custom_recipe_client.get(recipe_id)
        content = data.get("recipeContent", data)

        assert "Tweaked" in content.get("name", "")

        ingredients = (
            content.get("recipeIngredient")
            or content.get("ingredients", [])
        )
        instructions = (
            content.get("recipeInstructions")
            or content.get("instructions", [])
        )
        assert len(ingredients) == 5
        assert len(instructions) == 5

        recipe_yield = content.get("recipeYield") or content.get("yield", {})
        assert recipe_yield.get("value") == 6

        print(f"\n  Read back tweaked recipe: {content.get('name')}")
        print(f"  Ingredients:  {ingredients}")
        print(f"  Yield: {recipe_yield}")

    # ── C: Listing ──────────────────────────────────────────────────

    async def test_list_includes_test_recipes(
        self,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """The listing endpoint should include all test recipes."""
        if not created_recipe_ids:
            pytest.skip("No custom recipes were created in this session")

        listing = await custom_recipe_client.list_all()
        items = listing.get("items", listing.get("createdRecipes", []))
        ids = [
            item.get("recipeId", item.get("id"))
            for item in items
        ]

        print(f"\n  Listing contains {len(ids)} custom recipes total")
        for rid in created_recipe_ids:
            found = rid in ids
            status = "✓" if found else "✗ MISSING"
            print(f"    {rid}: {status}")
            assert found, f"Recipe {rid} not found in listing"


# ── 3. Shopping list tests ───────────────────────────────────────────


class TestShoppingList:
    """Shopping list operations."""

    async def test_get_shopping_list_recipes(self, cookidoo_client: Cookidoo):
        """Get recipes currently on the shopping list."""
        recipes = await cookidoo_client.get_shopping_list_recipes()

        assert isinstance(recipes, list)
        print(f"\n  Recipes on shopping list: {len(recipes)}")
        for r in recipes[:5]:
            print(f"    - {r.name}")

    async def test_get_ingredient_items(self, cookidoo_client: Cookidoo):
        """Get ingredient items from the shopping list."""
        items = await cookidoo_client.get_ingredient_items()

        assert isinstance(items, list)
        print(f"\n  Ingredient items: {len(items)}")
        for item in items[:5]:
            print(f"    - {item.name}")


# ── 4. Cleanup (runs last) ──────────────────────────────────────────


@pytest.mark.e2e_cleanup
class TestCleanup:
    """
    Remove any custom recipes created during this test session.

    Always lists **all** custom recipes so you can see what's in your
    account, then highlights which ones are in scope for deletion
    (names starting with ``[E2E``).  When run interactively (``-s``),
    prompts for confirmation before deleting.
    """

    async def test_delete_test_recipes(
        self,
        request: pytest.FixtureRequest,
        custom_recipe_client: CookidooCustomRecipeClient,
        created_recipe_ids: list[str],
    ):
        """Delete all custom recipes matching the test prefix.

        1. Lists every custom recipe in the account.
        2. Marks which ones are in scope for deletion.
        3. Prompts for confirmation (when using ``-s``).
        4. Deletes only the marked recipes.
        """
        # ── Fetch all custom recipes ───────────────────────────────
        listing = await custom_recipe_client.list_all()
        items = listing.get("items", listing.get("createdRecipes", []))

        # Build a full inventory with delete flag
        all_recipes: list[tuple[str, str, bool]] = []  # (id, name, to_delete)
        session_ids = set(created_recipe_ids)

        for item in items:
            content = item.get("recipeContent", {})
            name = content.get("name", "(unnamed)")
            rid = item.get("recipeId", item.get("id", ""))
            in_session = rid in session_ids
            matches_prefix = name.startswith(_CLEANUP_PREFIX)
            to_delete = in_session or matches_prefix
            all_recipes.append((rid, name, to_delete))

        # Also flag any session IDs that weren't in the listing
        # (shouldn't happen, but be safe)
        listed_ids = {r[0] for r in all_recipes}
        for rid in session_ids:
            if rid not in listed_ids:
                all_recipes.append((rid, "(from session, not in listing)", True))

        # ── Display full inventory ─────────────────────────────────
        delete_count = sum(1 for _, _, d in all_recipes if d)
        keep_count = len(all_recipes) - delete_count

        print(f"\n  All custom recipes ({len(all_recipes)} total):")
        print(f"  {'-' * 58}")
        for rid, name, to_delete in all_recipes:
            marker = ">> DELETE" if to_delete else "   keep  "
            print(f"    {marker}  {rid}  {name}")
        print(f"  {'-' * 58}")
        print(f"  {delete_count} to delete, {keep_count} to keep")

        if delete_count == 0:
            print(f"\n  No test recipes found (looked for prefix '{_CLEANUP_PREFIX}')")
            pytest.skip(
                f"No test recipes to clean up "
                f"(prefix '{_CLEANUP_PREFIX}' not found in {len(all_recipes)} recipes)"
            )

        # ── Confirm ────────────────────────────────────────────────
        # pytest's capturemanager.is_globally_capturing() returns True
        # when stdout IS captured (no -s), False when -s is used.
        capture = request.config.pluginmanager.getplugin("capturemanager")
        capturing = capture is not None and capture.is_globally_capturing()

        if not capturing:
            print()
            answer = input("  Proceed with deletion? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                pytest.skip("Deletion cancelled by user")
        else:
            print("\n  (auto-confirmed - pass -s to get an interactive prompt)")

        # ── Delete ─────────────────────────────────────────────────
        deleted = []
        errors = []
        for rid, name, to_delete in all_recipes:
            if not to_delete:
                continue
            try:
                await custom_recipe_client.delete(rid)
                deleted.append(rid)
                print(f"    [ok] deleted  {rid}  {name}")
            except Exception as exc:
                errors.append((rid, str(exc)))
                print(f"    [!!] failed  {rid}  {name}  - {exc}")

        created_recipe_ids.clear()

        assert len(errors) == 0, f"Failed to delete: {errors}"
        assert len(deleted) > 0
        print(f"\n  Cleaned up {len(deleted)} test recipe(s)")
