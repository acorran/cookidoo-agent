# Databricks notebook source
# MAGIC %md
# MAGIC # Databricks MCP Client Integration
# MAGIC
# MAGIC This notebook demonstrates connecting to the Cookidoo MCP server
# MAGIC from Databricks using both patterns:
# MAGIC
# MAGIC | Pattern | Description | Cost | Use Case |
# MAGIC |---------|-------------|------|----------|
# MAGIC | **A – REST** | Databricks → MCP REST API (port 8001) | Low (HTTP calls only) | Batch sync, simple operations |
# MAGIC | **B – MCP Protocol** | Databricks → MCP SSE endpoint (port 8002) | Low (HTTP calls only) | AI Agent tool use, Databricks AI showcase |
# MAGIC
# MAGIC Both patterns connect to the **same MCP server** running in a Docker container
# MAGIC (Azure Container Apps). No additional Databricks compute cost beyond the
# MAGIC notebook cluster.
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - MCP server running (Docker container or Azure Container Apps)
# MAGIC - Azure Key Vault scope with `cookidoo-email`, `cookidoo-password`
# MAGIC - Secret `mcp-server-url` in scope `cookidoo-mcp`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Install Dependencies

# COMMAND ----------

# MAGIC %pip install httpx fastmcp mcp pydantic requests

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Configuration

# COMMAND ----------

import os
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_client")

# Configuration – update scope names to match your setup
KEY_VAULT_SCOPE = "cookidoo-secrets"
MCP_SCOPE = "cookidoo-mcp"

# Retrieve MCP server URL from Databricks secrets.
# In Azure, this is the internal FQDN of the Container App, e.g.:
#   https://mcp-server.internal.<region>.azurecontainerapps.io
# Stored by: scripts/deploy_azure_infrastructure.py
try:
    MCP_SERVER_URL = dbutils.secrets.get(scope=MCP_SCOPE, key="mcp-server-url")
    print(f"✓ MCP Server URL: {MCP_SERVER_URL}")
except Exception:
    # Fallback for local testing with Docker
    MCP_SERVER_URL = "http://localhost:8001"
    print(f"⚠ Using fallback MCP URL: {MCP_SERVER_URL}")

# SSE endpoint (same host, different port for MCP protocol).
# In Azure Container Apps, both ports are exposed via the same internal FQDN
# if configured with additional TCP ports, or use the REST API only.
try:
    MCP_SSE_URL = dbutils.secrets.get(scope=MCP_SCOPE, key="mcp-sse-url")
except Exception:
    # Derive from REST URL by swapping port, or use same base if no separate port
    MCP_SSE_URL = MCP_SERVER_URL.replace(":8001", ":8002")

print(f"  MCP REST endpoint: {MCP_SERVER_URL}")
print(f"  MCP SSE endpoint:  {MCP_SSE_URL}")
print()
print("Note: In Azure, both endpoints are reachable because Databricks")
print("uses VNet injection into the same VNet as Azure Container Apps.")
print("See: scripts/deploy_azure_infrastructure.py for networking setup.")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Pattern A: REST API Integration
# MAGIC
# MAGIC Simple HTTP calls to the MCP server's REST endpoints.
# MAGIC This is the **cost-optimal default** – no additional Databricks
# MAGIC infrastructure required.

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.1 – Authenticate via REST

# COMMAND ----------

import requests


def mcp_rest_authenticate() -> str:
    """
    Authenticate with Cookidoo via MCP REST API.

    Returns:
        Access token string.
    """
    email = dbutils.secrets.get(scope=KEY_VAULT_SCOPE, key="cookidoo-email")
    password = dbutils.secrets.get(scope=KEY_VAULT_SCOPE, key="cookidoo-password")

    response = requests.post(
        f"{MCP_SERVER_URL}/auth/token",
        json={"username": email, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print("✓ REST authentication successful")
    return token


rest_token = mcp_rest_authenticate()

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.2 – Search Recipes via REST

# COMMAND ----------


def mcp_rest_search(query: str, token: str, limit: int = 5) -> list:
    """Search recipes via MCP REST API."""
    response = requests.get(
        f"{MCP_SERVER_URL}/api/recipes/search",
        params={"q": query, "limit": limit},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["results"]


results = mcp_rest_search("pasta", rest_token, limit=5)

print(f"✓ Found {len(results)} recipes via REST")
for i, r in enumerate(results, 1):
    print(f"  {i}. {r.get('title', r.get('name', 'Unknown'))}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### A.3 – Sync Recipes to Delta Lake via REST

# COMMAND ----------

from pyspark.sql import Row


def sync_recipes_to_delta(token: str, query: str = "all") -> int:
    """
    Fetch recipes from MCP REST API and write to Delta bronze table.

    Args:
        token: MCP auth token.
        query: Search query (use 'all' for full sync).

    Returns:
        Number of recipes synced.
    """
    recipes = mcp_rest_search(query, token, limit=100)

    if not recipes:
        print("⚠ No recipes to sync")
        return 0

    rows = []
    for recipe in recipes:
        rows.append(
            Row(
                recipe_id=recipe.get("recipe_id", recipe.get("id", "")),
                title=recipe.get("title", recipe.get("name", "")),
                description=recipe.get("description", ""),
                raw_json=json.dumps(recipe),
                source="cookidoo_mcp_rest",
                ingestion_timestamp=datetime.utcnow(),
            )
        )

    df = spark.createDataFrame(rows)

    df.write.format("delta").mode("append").saveAsTable(
        "cookidoo_agent.staging.recipes_bronze"
    )

    print(f"✓ Synced {len(rows)} recipes to cookidoo_agent.staging.recipes_bronze")
    return len(rows)


# Uncomment to run sync:
# count = sync_recipes_to_delta(rest_token, query="pasta")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Pattern B: MCP Protocol Integration (SSE Transport)
# MAGIC
# MAGIC Connect to the MCP server using the **Model Context Protocol** natively.
# MAGIC This is the pattern to showcase Databricks AI capabilities – agents can
# MAGIC discover and call MCP tools automatically.

# COMMAND ----------

# MAGIC %md
# MAGIC ### B.1 – Connect to MCP Server via SSE

# COMMAND ----------

import httpx
import asyncio


async def discover_mcp_tools(sse_url: str) -> dict:
    """
    Connect to the MCP server's SSE endpoint and discover available tools.

    Args:
        sse_url: MCP server SSE URL (e.g. http://mcp-server:8002).

    Returns:
        Dictionary of discovered tools and their schemas.
    """
    # The fastmcp SSE endpoint exposes tool discovery
    async with httpx.AsyncClient(timeout=30.0) as client:
        # List available tools via MCP protocol
        response = await client.get(f"{sse_url}/tools/list")
        tools = response.json()
        return tools


try:
    tools = asyncio.run(discover_mcp_tools(MCP_SSE_URL))
    print(f"✓ Discovered {len(tools.get('tools', []))} MCP tools:")
    for tool in tools.get("tools", []):
        print(f"  - {tool['name']}: {tool.get('description', '')[:80]}")
except Exception as e:
    print(f"⚠ MCP SSE discovery failed (server may not be running): {e}")
    print("  This is expected if the MCP server SSE port (8002) is not exposed")

# COMMAND ----------

# MAGIC %md
# MAGIC ### B.2 – Call MCP Tools Directly

# COMMAND ----------


async def call_mcp_tool(sse_url: str, tool_name: str, arguments: dict) -> dict:
    """
    Call an MCP tool on the remote server.

    Args:
        sse_url: MCP server SSE URL.
        tool_name: Name of the tool to call.
        arguments: Tool arguments dictionary.

    Returns:
        Tool execution result.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{sse_url}/tools/call",
            json={
                "name": tool_name,
                "arguments": arguments,
            },
        )
        response.raise_for_status()
        return response.json()


# Example: Search recipes via MCP protocol
try:
    result = asyncio.run(
        call_mcp_tool(
            MCP_SSE_URL,
            "search_recipes",
            {"query": "risotto", "limit": 3},
        )
    )
    print(f"✓ MCP tool 'search_recipes' returned:")
    print(json.dumps(result, indent=2, default=str)[:500])
except Exception as e:
    print(f"⚠ MCP tool call failed: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### B.3 – Use MCP Tools with Databricks AI Agent
# MAGIC
# MAGIC This is the **showcase pattern**: register MCP tools as agent tools
# MAGIC so a Databricks-hosted LLM agent can call them during conversations.

# COMMAND ----------

# MAGIC %md
# MAGIC #### Option 1: Mosaic AI Agent Framework with MCP Tools
# MAGIC
# MAGIC Databricks Mosaic AI Agent Framework supports external tool servers.
# MAGIC Register the MCP server so agents can discover and call its tools.

# COMMAND ----------


def create_agent_with_mcp_tools():
    """
    Create a Databricks AI agent that uses MCP tools for Cookidoo operations.

    This demonstrates the Mosaic AI Agent Framework's ability to integrate
    with external MCP tool servers.
    """
    try:
        from databricks.agents import Agent, AgentConfig
        from databricks.agents.tools import MCPToolServer

        # Register MCP server as a tool provider
        mcp_tool_server = MCPToolServer(
            name="cookidoo-mcp",
            url=MCP_SSE_URL,
            description=(
                "Cookidoo recipe platform tools: search recipes, get recipe "
                "details, modify recipes, manage shopping lists."
            ),
        )

        # Create agent configuration
        config = AgentConfig(
            model_serving_endpoint="cookidoo-agent-primary",  # Claude Sonnet 4.5
            tool_servers=[mcp_tool_server],
            instructions=(
                "You are a helpful cooking assistant. Use the cookidoo-mcp tools "
                "to search for recipes, retrieve recipe details, and help users "
                "modify recipes. Always be specific about ingredients and steps."
            ),
        )

        agent = Agent(config=config)
        print("✓ Agent created with MCP tool server")
        print(f"  Model: cookidoo-agent-primary")
        print(f"  MCP Server: {MCP_SSE_URL}")
        return agent

    except ImportError:
        print("⚠ databricks.agents not available on this cluster")
        print("  Install: %pip install databricks-agents")
        print("  Or use a Databricks Runtime with ML support")
        return None
    except Exception as e:
        print(f"⚠ Agent creation failed: {e}")
        return None


agent = create_agent_with_mcp_tools()

# COMMAND ----------

# MAGIC %md
# MAGIC #### Option 2: LangChain Agent with MCP Tools (Alternative)
# MAGIC
# MAGIC If the Mosaic AI Agent SDK is not available, use LangChain with
# MAGIC HTTP-based tool wrappers.

# COMMAND ----------


def create_langchain_mcp_tools() -> list:
    """
    Create LangChain-compatible tools that call the MCP server.

    Returns:
        List of LangChain Tool objects.
    """
    try:
        from langchain.tools import Tool

        tools = [
            Tool(
                name="search_cookidoo_recipes",
                description=(
                    "Search for recipes on Cookidoo. Input: JSON with 'query' "
                    "(string) and optional 'limit' (int)."
                ),
                func=lambda input_str: asyncio.run(
                    call_mcp_tool(
                        MCP_SSE_URL,
                        "search_recipes",
                        (
                            json.loads(input_str)
                            if isinstance(input_str, str)
                            else input_str
                        ),
                    )
                ),
            ),
            Tool(
                name="get_cookidoo_recipe",
                description=(
                    "Get full details of a Cookidoo recipe. Input: JSON with "
                    "'recipe_id' (string)."
                ),
                func=lambda input_str: asyncio.run(
                    call_mcp_tool(
                        MCP_SSE_URL,
                        "get_recipe",
                        (
                            json.loads(input_str)
                            if isinstance(input_str, str)
                            else input_str
                        ),
                    )
                ),
            ),
            Tool(
                name="modify_cookidoo_recipe",
                description=(
                    "Modify a Cookidoo recipe. Input: JSON with 'recipe_id' "
                    "(string) and 'modifications' (dict with changes)."
                ),
                func=lambda input_str: asyncio.run(
                    call_mcp_tool(
                        MCP_SSE_URL,
                        "modify_recipe",
                        (
                            json.loads(input_str)
                            if isinstance(input_str, str)
                            else input_str
                        ),
                    )
                ),
            ),
            Tool(
                name="save_cookidoo_recipe",
                description=(
                    "Save a recipe to Cookidoo. Input: JSON with recipe data."
                ),
                func=lambda input_str: asyncio.run(
                    call_mcp_tool(
                        MCP_SSE_URL,
                        "save_recipe",
                        (
                            json.loads(input_str)
                            if isinstance(input_str, str)
                            else input_str
                        ),
                    )
                ),
            ),
        ]

        print(f"✓ Created {len(tools)} LangChain MCP tools")
        for t in tools:
            print(f"  - {t.name}")
        return tools

    except ImportError:
        print("⚠ LangChain not available. Install: %pip install langchain")
        return []


lc_tools = create_langchain_mcp_tools()

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## 3. Comparison Summary

# COMMAND ----------

print("=" * 70)
print(" MCP Integration Patterns – Summary")
print("=" * 70)
print()
print("Pattern A: REST API (Default – Cost Optimal)")
print("  ├─ Endpoint:    {}/api/recipes/...".format(MCP_SERVER_URL))
print("  ├─ Auth:        Bearer token via /auth/token")
print("  ├─ Transport:   HTTP/JSON")
print("  ├─ Cost:        Cluster compute only (no extra infra)")
print("  └─ Best for:    Batch sync, scheduled jobs, simple queries")
print()
print("Pattern B: MCP Protocol (Showcase – Databricks AI)")
print("  ├─ Endpoint:    {}".format(MCP_SSE_URL))
print("  ├─ Auth:        Environment variables on MCP server")
print("  ├─ Transport:   SSE (Model Context Protocol)")
print("  ├─ Cost:        Cluster compute only (no extra infra)")
print("  └─ Best for:    AI agent tool use, Mosaic AI, demos")
print()
print("Both patterns connect to the SAME MCP server in Docker.")
print("No additional Databricks cost beyond notebook cluster.")
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Next Steps
# MAGIC
# MAGIC 1. **Deploy MCP server** with SSE port exposed (8001 REST + 8002 SSE)
# MAGIC 2. **Store MCP URL** in Databricks secrets: `databricks secrets put-secret cookidoo-mcp mcp-server-url`
# MAGIC 3. **Run Pattern A** cells above to verify REST connectivity
# MAGIC 4. **Run Pattern B** cells to verify MCP protocol connectivity
# MAGIC 5. **Create AI Agent** using Mosaic AI or LangChain with MCP tools
# MAGIC 6. **Schedule sync job** using Pattern A for daily recipe refresh
