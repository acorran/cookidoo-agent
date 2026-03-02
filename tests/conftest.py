"""
Test configuration and fixtures.
"""

import pytest
import os
from typing import Generator


def pytest_deselected(items):
    """Print deselected tests so it's clear what was skipped."""
    if not items:
        return
    terminal = items[0].config.pluginmanager.get_plugin("terminalreporter")
    if terminal is None:
        return
    terminal.write_line("")
    terminal.write_line(
        f"  {len(items)} deselected:", bold=True, yellow=True,
    )
    for item in items:
        terminal.write_line(f"    - {item.nodeid}", yellow=True)
    terminal.write_line("")


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
