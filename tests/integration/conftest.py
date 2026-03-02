"""
Shared fixtures for integration / end-to-end tests.

These tests hit the real Cookidoo API and require valid credentials
in the .env file (COOKIDOO_EMAIL, COOKIDOO_PASSWORD, etc.).

They are gated behind the ``e2e`` pytest marker so they never run
accidentally during normal ``pytest`` invocations.  Run them with:

    pytest -m e2e -v              # all e2e tests
    pytest -m e2e -v -k search    # only the search test
    pytest -m e2e -v -k cleanup   # only the cleanup test
"""

import os
import pytest
import pytest_asyncio
import aiohttp
from dotenv import load_dotenv

from cookidoo_api import (
    Cookidoo,
    CookidooConfig,
    CookidooLocalizationConfig,
)
from backend.services.cookidoo_custom_recipes import CookidooCustomRecipeClient

# Load .env from project root
load_dotenv()


def _missing_credentials() -> bool:
    """Return True when Cookidoo credentials are absent."""
    return not os.getenv("COOKIDOO_EMAIL") or not os.getenv("COOKIDOO_PASSWORD")


@pytest.fixture(scope="module")
def cookidoo_config() -> CookidooConfig:
    """Build a CookidooConfig from environment variables."""
    if _missing_credentials():
        pytest.skip("COOKIDOO_EMAIL / COOKIDOO_PASSWORD not set in .env")

    localization = CookidooLocalizationConfig(
        country_code=os.getenv("COOKIDOO_COUNTRY_CODE", "us"),
        language=os.getenv("COOKIDOO_LANGUAGE", "en-US"),
        url=os.getenv(
            "COOKIDOO_URL",
            "https://cookidoo.thermomix.com/foundation/en-US",
        ),
    )
    return CookidooConfig(
        localization=localization,
        email=os.getenv("COOKIDOO_EMAIL", ""),
        password=os.getenv("COOKIDOO_PASSWORD", ""),
    )


# Module-scoped session so we share connections across all tests.
_aiohttp_session: aiohttp.ClientSession | None = None


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def cookidoo_client(cookidoo_config: CookidooConfig) -> Cookidoo:
    """
    Return an authenticated Cookidoo client that lives for the entire
    test module (avoids repeated logins).
    """
    global _aiohttp_session
    _aiohttp_session = aiohttp.ClientSession()
    client = Cookidoo(_aiohttp_session, cookidoo_config)
    await client.login()
    yield client
    await _aiohttp_session.close()
    _aiohttp_session = None


@pytest.fixture(scope="module")
def custom_recipe_client(cookidoo_client: Cookidoo) -> CookidooCustomRecipeClient:
    """Custom recipe client that bypasses library bugs.

    Uses the same ``aiohttp.ClientSession`` and authenticated
    ``Cookidoo`` instance as :func:`cookidoo_client`.
    """
    assert _aiohttp_session is not None, "Session not initialised"
    return CookidooCustomRecipeClient(_aiohttp_session, cookidoo_client)


# Storage for recipe IDs created during the session so the cleanup
# test can delete them.
_created_custom_recipe_ids: list[str] = []


@pytest.fixture(scope="module")
def created_recipe_ids() -> list[str]:
    """Mutable list that tests append custom-recipe IDs to for cleanup."""
    return _created_custom_recipe_ids
