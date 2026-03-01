# Databricks notebook source
# MAGIC %md
# MAGIC # MCP Recipe Sync Job
# MAGIC
# MAGIC Scheduled notebook that syncs recipes from Cookidoo via the MCP server
# MAGIC into Delta Lake bronze tables. Designed to run as a Databricks Job
# MAGIC (e.g. daily at 2 AM UTC).
# MAGIC
# MAGIC **Data flow:**
# MAGIC ```
# MAGIC MCP Server (REST) → This Notebook → cookidoo_agent.staging.recipes_bronze
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import json
import logging
import requests
from datetime import datetime
from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_sync")

# Configurable via job parameters
KEY_VAULT_SCOPE = (
    dbutils.widgets.get("key_vault_scope")
    if "key_vault_scope" in [w.name for w in dbutils.widgets.getAll()]
    else "cookidoo-secrets"
)
MCP_SCOPE = (
    dbutils.widgets.get("mcp_scope")
    if "mcp_scope" in [w.name for w in dbutils.widgets.getAll()]
    else "cookidoo-mcp"
)
TARGET_TABLE = (
    dbutils.widgets.get("target_table")
    if "target_table" in [w.name for w in dbutils.widgets.getAll()]
    else "cookidoo_agent.staging.recipes_bronze"
)

# Add widgets for job parameterization
dbutils.widgets.text("key_vault_scope", KEY_VAULT_SCOPE, "Key Vault Scope")
dbutils.widgets.text("mcp_scope", MCP_SCOPE, "MCP Secret Scope")
dbutils.widgets.text("target_table", TARGET_TABLE, "Target Delta Table")
dbutils.widgets.text("search_queries", "all", "Search Queries (comma-separated)")

search_queries_str = dbutils.widgets.get("search_queries")
SEARCH_QUERIES = [q.strip() for q in search_queries_str.split(",")]

print(f"Key Vault Scope: {KEY_VAULT_SCOPE}")
print(f"MCP Scope:       {MCP_SCOPE}")
print(f"Target Table:    {TARGET_TABLE}")
print(f"Search Queries:  {SEARCH_QUERIES}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. MCP Server Connection

# COMMAND ----------

# In Azure deployment, this is the Container Apps internal FQDN.
# Stored by scripts/deploy_azure_infrastructure.py during deployment.
try:
    MCP_SERVER_URL = dbutils.secrets.get(scope=MCP_SCOPE, key="mcp-server-url")
except Exception:
    # Fallback for local Docker development only
    MCP_SERVER_URL = "http://localhost:8001"

print(f"MCP Server: {MCP_SERVER_URL}")


def get_mcp_token() -> str:
    """Authenticate with MCP server and return bearer token."""
    email = dbutils.secrets.get(scope=KEY_VAULT_SCOPE, key="cookidoo-email")
    password = dbutils.secrets.get(scope=KEY_VAULT_SCOPE, key="cookidoo-password")

    resp = requests.post(
        f"{MCP_SERVER_URL}/auth/token",
        json={"username": email, "password": password},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


token = get_mcp_token()
print("✓ Authenticated with MCP server")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Fetch Recipes

# COMMAND ----------


def fetch_recipes(token: str, query: str, limit: int = 200) -> list:
    """
    Fetch recipes from MCP server via REST API.

    Args:
        token: Bearer auth token.
        query: Search query string.
        limit: Max results per query.

    Returns:
        List of recipe dicts.
    """
    try:
        resp = requests.get(
            f"{MCP_SERVER_URL}/api/recipes/search",
            params={"q": query, "limit": limit},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        resp.raise_for_status()
        recipes = resp.json().get("results", [])
        logger.info(f"Query '{query}': fetched {len(recipes)} recipes")
        return recipes
    except Exception as e:
        logger.error(f"Query '{query}' failed: {e}")
        return []


# Fetch recipes for all configured queries
all_recipes = []
seen_ids = set()

for query in SEARCH_QUERIES:
    recipes = fetch_recipes(token, query)
    for r in recipes:
        rid = r.get("recipe_id", r.get("id", ""))
        if rid and rid not in seen_ids:
            seen_ids.add(rid)
            all_recipes.append(r)

print(f"✓ Total unique recipes fetched: {len(all_recipes)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Write to Delta Lake

# COMMAND ----------

SCHEMA = StructType(
    [
        StructField("recipe_id", StringType(), False),
        StructField("title", StringType(), True),
        StructField("description", StringType(), True),
        StructField("raw_json", StringType(), True),
        StructField("source", StringType(), True),
        StructField("sync_query", StringType(), True),
        StructField("ingestion_timestamp", TimestampType(), True),
    ]
)


def write_to_delta(recipes: list, table: str) -> int:
    """
    Write fetched recipes to Delta bronze table.

    Args:
        recipes: List of recipe dicts.
        table: Fully qualified Delta table name.

    Returns:
        Number of rows written.
    """
    if not recipes:
        logger.warning("No recipes to write")
        return 0

    now = datetime.utcnow()
    rows = []

    for recipe in recipes:
        rows.append(
            Row(
                recipe_id=recipe.get("recipe_id", recipe.get("id", "")),
                title=recipe.get("title", recipe.get("name", "")),
                description=recipe.get("description", ""),
                raw_json=json.dumps(recipe),
                source="cookidoo_mcp_sync",
                sync_query=",".join(SEARCH_QUERIES),
                ingestion_timestamp=now,
            )
        )

    df = spark.createDataFrame(rows, schema=SCHEMA)

    # Merge to avoid duplicates (upsert on recipe_id)
    df.createOrReplaceTempView("incoming_recipes")

    spark.sql(
        f"""
        MERGE INTO {table} AS target
        USING incoming_recipes AS source
        ON target.recipe_id = source.recipe_id
        WHEN MATCHED THEN
            UPDATE SET
                title = source.title,
                description = source.description,
                raw_json = source.raw_json,
                source = source.source,
                sync_query = source.sync_query,
                ingestion_timestamp = source.ingestion_timestamp
        WHEN NOT MATCHED THEN
            INSERT *
    """
    )

    logger.info(f"Merged {len(rows)} recipes into {table}")
    return len(rows)


count = write_to_delta(all_recipes, TARGET_TABLE)
print(f"✓ Wrote {count} recipes to {TARGET_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Verify

# COMMAND ----------

row_count = spark.table(TARGET_TABLE).count()
latest = (
    spark.sql(
        f"""
    SELECT MAX(ingestion_timestamp) AS latest_sync
    FROM {TARGET_TABLE}
"""
    )
    .collect()[0]
    .latest_sync
)

print(f"Table: {TARGET_TABLE}")
print(f"Total rows: {row_count}")
print(f"Latest sync: {latest}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Job Summary

# COMMAND ----------

summary = {
    "status": "SUCCESS",
    "timestamp": datetime.utcnow().isoformat(),
    "mcp_server": MCP_SERVER_URL,
    "queries": SEARCH_QUERIES,
    "recipes_fetched": len(all_recipes),
    "recipes_written": count,
    "target_table": TARGET_TABLE,
    "total_rows": row_count,
}

print(json.dumps(summary, indent=2))

# Exit with success for job scheduler
dbutils.notebook.exit(json.dumps(summary))
