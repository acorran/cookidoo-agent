"""
Test configuration and fixtures.
"""

import pytest
import os
from typing import Generator


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["MCP_SERVER_URL"] = "http://localhost:8001"
    os.environ["DATABRICKS_WORKSPACE_URL"] = "https://test.databricks.com"
    os.environ["DATABRICKS_TOKEN"] = "test_token"
    os.environ["AZURE_KEY_VAULT_URL"] = "https://test-vault.vault.azure.net/"


@pytest.fixture
def anyio_backend():
    """Configure async test backend."""
    return "asyncio"
