# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog Functions – MCP Tool Wrappers
# MAGIC
# MAGIC This notebook registers the Cookidoo MCP tools as **Unity Catalog (UC) functions**.
# MAGIC UC functions can be used as tools by Databricks AI agents, Genie spaces,
# MAGIC and SQL queries – providing a governed, discoverable interface to the MCP server.
# MAGIC
# MAGIC **Architecture:**
# MAGIC ```
# MAGIC Databricks Agent / Genie / SQL
# MAGIC         │
# MAGIC         ▼
# MAGIC   UC Function (cookidoo_agent.main.search_recipes)
# MAGIC         │
# MAGIC         ▼
# MAGIC   MCP Server (Docker container, REST API)
# MAGIC         │
# MAGIC         ▼
# MAGIC   Cookidoo Platform API
# MAGIC ```
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - Unity Catalog `cookidoo_agent` and schema `main` created
# MAGIC - MCP server URL stored in secret scope `cookidoo-mcp`
# MAGIC - Cookidoo credentials in secret scope `cookidoo-secrets`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

KEY_VAULT_SCOPE = "cookidoo-secrets"
MCP_SCOPE = "cookidoo-mcp"
UC_CATALOG = "cookidoo_agent"
UC_SCHEMA = "main"

# In Azure, this is the Container Apps internal FQDN (private, VNet-only).
# Stored by scripts/deploy_azure_infrastructure.py during deployment.
try:
    MCP_SERVER_URL = dbutils.secrets.get(scope=MCP_SCOPE, key="mcp-server-url")
except Exception:
    # Fallback for local Docker testing only
    MCP_SERVER_URL = "http://localhost:8001"

print(f"Catalog:    {UC_CATALOG}")
print(f"Schema:     {UC_SCHEMA}")
print(f"MCP Server: {MCP_SERVER_URL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create UC Functions via SQL
# MAGIC
# MAGIC These SQL-based UC functions wrap HTTP calls to the MCP server.
# MAGIC Databricks AI agents automatically discover UC functions as tools.

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG cookidoo_agent;
# MAGIC USE SCHEMA main;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- UC Function: Search Recipes
# MAGIC -- Agents and Genie can call this function to search Cookidoo recipes.
# MAGIC CREATE OR REPLACE FUNCTION cookidoo_agent.main.search_recipes(
# MAGIC   query STRING COMMENT 'Natural language search query for recipes (e.g. "vegan pasta")',
# MAGIC   max_results INT DEFAULT 10 COMMENT 'Maximum number of results to return'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC COMMENT 'Search for recipes on the Cookidoo platform. Returns JSON array of recipe summaries with id, title, and description.'
# MAGIC LANGUAGE PYTHON
# MAGIC AS $$
# MAGIC   import requests
# MAGIC   import json
# MAGIC
# MAGIC   mcp_url = "MCP_SERVER_URL_PLACEHOLDER"
# MAGIC
# MAGIC   # Authenticate
# MAGIC   auth_resp = requests.post(
# MAGIC       f"{mcp_url}/auth/token",
# MAGIC       json={"username": "COOKIDOO_EMAIL_PLACEHOLDER", "password": "COOKIDOO_PASSWORD_PLACEHOLDER"},
# MAGIC       timeout=30,
# MAGIC   )
# MAGIC   token = auth_resp.json()["access_token"]
# MAGIC
# MAGIC   # Search
# MAGIC   resp = requests.get(
# MAGIC       f"{mcp_url}/api/recipes/search",
# MAGIC       params={"q": query, "limit": max_results},
# MAGIC       headers={"Authorization": f"Bearer {token}"},
# MAGIC       timeout=30,
# MAGIC   )
# MAGIC   return json.dumps(resp.json().get("results", []))
# MAGIC $$;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- UC Function: Get Recipe Details
# MAGIC CREATE OR REPLACE FUNCTION cookidoo_agent.main.get_recipe(
# MAGIC   recipe_id STRING COMMENT 'Unique Cookidoo recipe identifier'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC COMMENT 'Retrieve full details for a specific Cookidoo recipe including ingredients, steps, and nutritional information. Returns JSON.'
# MAGIC LANGUAGE PYTHON
# MAGIC AS $$
# MAGIC   import requests
# MAGIC   import json
# MAGIC
# MAGIC   mcp_url = "MCP_SERVER_URL_PLACEHOLDER"
# MAGIC
# MAGIC   auth_resp = requests.post(
# MAGIC       f"{mcp_url}/auth/token",
# MAGIC       json={"username": "COOKIDOO_EMAIL_PLACEHOLDER", "password": "COOKIDOO_PASSWORD_PLACEHOLDER"},
# MAGIC       timeout=30,
# MAGIC   )
# MAGIC   token = auth_resp.json()["access_token"]
# MAGIC
# MAGIC   resp = requests.get(
# MAGIC       f"{mcp_url}/api/recipes/{recipe_id}",
# MAGIC       headers={"Authorization": f"Bearer {token}"},
# MAGIC       timeout=30,
# MAGIC   )
# MAGIC   return json.dumps(resp.json())
# MAGIC $$;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- UC Function: Save Recipe
# MAGIC CREATE OR REPLACE FUNCTION cookidoo_agent.main.save_recipe(
# MAGIC   recipe_json STRING COMMENT 'JSON string of recipe data to save (must include title, ingredients, steps)'
# MAGIC )
# MAGIC RETURNS STRING
# MAGIC COMMENT 'Save a new or modified recipe to Cookidoo My Recipes collection. Input is a JSON string. Returns confirmation JSON.'
# MAGIC LANGUAGE PYTHON
# MAGIC AS $$
# MAGIC   import requests
# MAGIC   import json
# MAGIC
# MAGIC   mcp_url = "MCP_SERVER_URL_PLACEHOLDER"
# MAGIC   recipe_data = json.loads(recipe_json)
# MAGIC
# MAGIC   auth_resp = requests.post(
# MAGIC       f"{mcp_url}/auth/token",
# MAGIC       json={"username": "COOKIDOO_EMAIL_PLACEHOLDER", "password": "COOKIDOO_PASSWORD_PLACEHOLDER"},
# MAGIC       timeout=30,
# MAGIC   )
# MAGIC   token = auth_resp.json()["access_token"]
# MAGIC
# MAGIC   resp = requests.post(
# MAGIC       f"{mcp_url}/api/recipes/save",
# MAGIC       json={"recipe": recipe_data, "collection": "My Recipes"},
# MAGIC       headers={"Authorization": f"Bearer {token}"},
# MAGIC       timeout=30,
# MAGIC   )
# MAGIC   return json.dumps(resp.json())
# MAGIC $$;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Register UC Functions as Agent Tools
# MAGIC
# MAGIC With UC functions created, Databricks AI agents automatically discover
# MAGIC them. Here's how to explicitly configure an agent to use them.

# COMMAND ----------


def create_uc_agent():
    """
    Create a Databricks AI agent that uses UC functions as tools.

    UC functions are automatically discovered by function name.
    """
    try:
        from databricks.agents import Agent, AgentConfig
        from databricks.agents.tools import UCFunctionTool

        tools = [
            UCFunctionTool(function_name="cookidoo_agent.main.search_recipes"),
            UCFunctionTool(function_name="cookidoo_agent.main.get_recipe"),
            UCFunctionTool(function_name="cookidoo_agent.main.save_recipe"),
        ]

        config = AgentConfig(
            model_serving_endpoint="cookidoo-agent-primary",
            tools=tools,
            instructions=(
                "You are a helpful cooking assistant with access to the Cookidoo "
                "recipe platform. Use the search_recipes tool to find recipes, "
                "get_recipe to see full details, and save_recipe to save "
                "user modifications. Be specific about ingredients and quantities."
            ),
        )

        agent = Agent(config=config)
        print("✓ Agent created with UC function tools:")
        for t in tools:
            print(f"  - {t.function_name}")
        return agent

    except ImportError:
        print("⚠ databricks.agents not available")
        print("  Use Databricks Runtime ML 14.3+ or install databricks-agents")
        return None


agent = create_uc_agent()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Test UC Functions

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Test: Search for pasta recipes via UC function
# MAGIC SELECT cookidoo_agent.main.search_recipes('pasta', 3) AS results;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Test: Use in a query context
# MAGIC SELECT
# MAGIC   'pasta' AS query,
# MAGIC   cookidoo_agent.main.search_recipes('pasta', 5) AS results
# MAGIC UNION ALL
# MAGIC SELECT
# MAGIC   'risotto' AS query,
# MAGIC   cookidoo_agent.main.search_recipes('risotto', 5) AS results;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Genie Space Integration
# MAGIC
# MAGIC These UC functions are automatically available in Genie spaces
# MAGIC that reference the `cookidoo_agent.main` schema. Users can ask:
# MAGIC
# MAGIC - *"Search for vegan dinner recipes"*
# MAGIC - *"Show me the details of recipe XYZ"*
# MAGIC - *"Find gluten-free pasta recipes"*
# MAGIC
# MAGIC Genie will call the UC functions and return formatted results.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Important Notes
# MAGIC
# MAGIC ### Security – Credential Handling
# MAGIC
# MAGIC The UC function SQL definitions above use `PLACEHOLDER` values for
# MAGIC credentials. In production, replace with one of:
# MAGIC
# MAGIC 1. **Databricks Secrets** – Use `dbutils.secrets.get()` inside Python UDFs
# MAGIC    (requires a Python UC function, not SQL)
# MAGIC 2. **Service Principal** – Configure the MCP server to accept
# MAGIC    service principal auth instead of username/password
# MAGIC 3. **Pre-authenticated endpoint** – MCP server authenticated at startup
# MAGIC    via environment variables (recommended for Docker deployment)
# MAGIC
# MAGIC ### Cost Impact
# MAGIC
# MAGIC - UC functions execute on the **calling cluster** (notebook or SQL warehouse)
# MAGIC - The MCP server runs in Docker – **no additional Databricks cost**
# MAGIC - Only cost is the HTTP roundtrip time added to queries
