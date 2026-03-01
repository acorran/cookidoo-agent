# Databricks Deployment & Configuration Guide
## Cookidoo Agent Assistant

**Version:** 1.0  
**Last Updated:** November 28, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture Overview](#architecture-overview)
4. [Catalog & Schema Setup](#catalog--schema-setup)
5. [Delta Live Tables (DLT) Configuration](#delta-live-tables-dlt-configuration)
6. [Vector Search Setup](#vector-search-setup)
7. [Model Serving Endpoints](#model-serving-endpoints)
8. [AgentBricks Configuration](#agentbricks-configuration)
9. [MCP Server Integration](#mcp-server-integration)
10. [Genie Space Setup](#genie-space-setup)
11. [Notebooks Deployment](#notebooks-deployment)
12. [Monitoring & Logging](#monitoring--logging)
13. [Security & Access Control](#security--access-control)
14. [Deployment Checklist](#deployment-checklist)

---

## Overview

This guide provides comprehensive step-by-step instructions for deploying the Cookidoo Agent Assistant infrastructure on Databricks. The deployment includes data storage, LLM model serving, vector search capabilities, and analytics notebooks.

### Deployment Goals

- Establish Unity Catalog structure for organized data management
- Create Delta Live Tables pipelines for real-time data processing
- Configure vector search for recipe similarity and recommendations
- Deploy Claude Sonnet 4.5 model endpoint for LLM interactions
- Set up AgentBricks for LLM orchestration workflows
- Integrate MCP server for Cookidoo API interactions
- Create Genie Space for natural language analytics
- Deploy analytical notebooks for insights and monitoring

---

## Prerequisites

### Required Access & Permissions

- Databricks workspace with Admin or Power User access
- Unity Catalog enabled workspace
- Model Serving capability enabled
- Vector Search feature enabled (contact Databricks rep if not available)
- Azure subscription with appropriate permissions
- Databricks CLI installed and configured

### Required Software

```powershell
# Install Databricks CLI
pip install databricks-cli

# Configure CLI
databricks configure --token
# Enter workspace URL: https://your-workspace.cloud.databricks.com
# Enter token: <your-personal-access-token>

# Verify connection
databricks workspace ls /
```

### Environment Variables

Create a `.databricks.env` file:

```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=<your-token>
DATABRICKS_CATALOG=cookidoo_agent
DATABRICKS_SCHEMA=main
WORKSPACE_ID=<your-workspace-id>
```

---

## Architecture Overview

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Databricks Workspace                      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Unity Catalog: cookidoo_agent                   │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │  │
│  │  │   Schema:    │  │   Schema:    │  │  Schema:   │ │  │
│  │  │     main     │  │   staging    │  │  analytics │ │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Delta Live Tables (DLT) Pipelines             │  │
│  │                                                        │  │
│  │  recipes_bronze → recipes_silver → recipes_gold      │  │
│  │  interactions_bronze → interactions_silver → gold    │  │
│  │  shopping_lists_pipeline                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Vector Search Index                       │  │
│  │                                                        │  │
│  │  recipe_embeddings (for similarity search)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Model Serving Endpoints                      │  │
│  │                                                        │  │
│  │  cookidoo-agent-primary (Claude Sonnet 4.5)            │  │
│  │  cookidoo-agent-analytics (Claude Opus 4.1)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AgentBricks Orchestration                 │  │
│  │                                                        │  │
│  │  Recipe Modification Agent                             │  │
│  │  Q&A Agent                                             │  │
│  │  Shopping List Agent                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Genie Space                           │  │
│  │                                                        │  │
│  │  Natural language analytics interface                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   MCP Server     │
                    │ (Cookidoo API)   │
                    └──────────────────┘
```

### Component Interactions

1. **External Data Ingestion**: MCP server fetches recipe data from Cookidoo
2. **Bronze Layer**: Raw data lands in staging tables
3. **Silver Layer**: DLT applies cleaning, validation, deduplication
4. **Gold Layer**: Aggregated, analytics-ready tables
5. **Vector Search**: Recipe embeddings enable semantic search
6. **Model Serving**: LLM endpoints process user requests
7. **AgentBricks**: Orchestrates complex multi-step workflows
8. **Genie Space**: Provides analytics to stakeholders

---

## Catalog & Schema Setup

### Step 1: Create Unity Catalog

Execute in Databricks SQL or notebook:

```sql
-- Create the main catalog for the Cookidoo Agent project
CREATE CATALOG IF NOT EXISTS cookidoo_agent
COMMENT 'Main catalog for Cookidoo Agent Assistant data and models';

-- Grant necessary permissions
GRANT USE CATALOG ON CATALOG cookidoo_agent TO `account users`;
GRANT CREATE SCHEMA ON CATALOG cookidoo_agent TO `data_engineers`;
```

### Step 2: Create Schemas

```sql
USE CATALOG cookidoo_agent;

-- Main schema for production data
CREATE SCHEMA IF NOT EXISTS main
COMMENT 'Production schema for recipe data, user interactions, and operational tables';

-- Staging schema for data ingestion
CREATE SCHEMA IF NOT EXISTS staging
COMMENT 'Staging schema for raw data ingestion from Cookidoo API';

-- Analytics schema for aggregated views and dashboards
CREATE SCHEMA IF NOT EXISTS analytics
COMMENT 'Analytics schema for aggregated metrics and reporting views';

-- ML schema for model artifacts and feature tables
CREATE SCHEMA IF NOT EXISTS ml
COMMENT 'ML schema for model artifacts, feature stores, and training data';

-- Grant permissions
GRANT USE SCHEMA ON SCHEMA main TO `account users`;
GRANT SELECT ON SCHEMA main TO `account users`;
GRANT ALL PRIVILEGES ON SCHEMA staging TO `data_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA ml TO `ml_engineers`;
```

### Step 3: Create Core Tables

```sql
USE CATALOG cookidoo_agent;
USE SCHEMA main;

-- Recipes table
CREATE TABLE IF NOT EXISTS recipes (
    recipe_id STRING NOT NULL,
    title STRING NOT NULL,
    description STRING,
    servings INT,
    prep_time_minutes INT,
    cook_time_minutes INT,
    total_time_minutes INT,
    difficulty STRING,
    ingredients ARRAY<STRUCT<
        name: STRING,
        quantity: DOUBLE,
        unit: STRING,
        notes: STRING
    >>,
    steps ARRAY<STRUCT<
        step_number: INT,
        instruction: STRING,
        duration_minutes: INT,
        temperature: INT
    >>,
    tags ARRAY<STRING>,
    dietary_info ARRAY<STRING>,
    nutritional_info STRUCT<
        calories: INT,
        protein_g: DOUBLE,
        carbohydrates_g: DOUBLE,
        fat_g: DOUBLE,
        fiber_g: DOUBLE,
        sodium_mg: INT
    >,
    source STRING,
    source_url STRING,
    image_url STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY (recipe_id)
)
USING DELTA
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Core recipes table with full recipe information';

-- User interactions table
CREATE TABLE IF NOT EXISTS user_interactions (
    interaction_id STRING NOT NULL,
    user_id STRING,
    session_id STRING,
    interaction_type STRING NOT NULL,  -- 'recipe_view', 'recipe_modify', 'chat', 'shopping_list'
    recipe_id STRING,
    interaction_data MAP<STRING, STRING>,
    timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (interaction_id)
)
USING DELTA
PARTITIONED BY (DATE(timestamp))
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true'
)
COMMENT 'User interaction events for analytics and model improvement';

-- Recipe modifications table
CREATE TABLE IF NOT EXISTS recipe_modifications (
    modification_id STRING NOT NULL,
    original_recipe_id STRING NOT NULL,
    modified_recipe_id STRING NOT NULL,
    user_id STRING,
    modification_prompt STRING,
    modifications_applied ARRAY<STRING>,
    modification_notes STRING,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (modification_id),
    FOREIGN KEY (original_recipe_id) REFERENCES recipes(recipe_id)
)
USING DELTA
PARTITIONED BY (DATE(created_at))
COMMENT 'Tracking of recipe modifications for analysis and improvement';

-- Shopping lists table
CREATE TABLE IF NOT EXISTS shopping_lists (
    list_id STRING NOT NULL,
    user_id STRING,
    list_name STRING,
    recipe_ids ARRAY<STRING>,
    items ARRAY<STRUCT<
        ingredient_name: STRING,
        quantity: DOUBLE,
        unit: STRING,
        category: STRING,
        checked: BOOLEAN,
        source_recipes: ARRAY<STRING>
    >>,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    PRIMARY KEY (list_id)
)
USING DELTA
COMMENT 'User-generated shopping lists';

-- Chat conversations table
CREATE TABLE IF NOT EXISTS chat_conversations (
    conversation_id STRING NOT NULL,
    user_id STRING,
    messages ARRAY<STRUCT<
        role: STRING,
        content: STRING,
        timestamp: TIMESTAMP
    >>,
    recipe_context STRING,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    PRIMARY KEY (conversation_id)
)
USING DELTA
PARTITIONED BY (DATE(created_at))
COMMENT 'Chat conversation history for context and analysis';
```

### Step 4: Create Indexes

```sql
-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_recipes_tags ON recipes(tags);
CREATE INDEX IF NOT EXISTS idx_recipes_dietary ON recipes(dietary_info);
CREATE INDEX IF NOT EXISTS idx_interactions_user ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_recipe ON user_interactions(recipe_id);
```

---

## Delta Live Tables (DLT) Configuration

### Overview

Delta Live Tables provide declarative ETL pipelines that automatically manage data quality, lineage, and refreshes. We'll create three main DLT pipelines:

1. **recipes_pipeline**: Ingest and process recipe data
2. **interactions_pipeline**: Process user interaction events
3. **shopping_lists_pipeline**: Aggregate shopping list data

### Step 1: Create DLT Pipeline Configuration

Save as `databricks/dlt/recipes_pipeline.json`:

```json
{
  "name": "cookidoo_recipes_pipeline",
  "storage": "/mnt/cookidoo_agent/pipelines/recipes",
  "target": "cookidoo_agent.main",
  "continuous": false,
  "channel": "CURRENT",
  "edition": "ADVANCED",
  "photon": true,
  "libraries": [
    {
      "notebook": {
        "path": "/Workspace/cookidoo-agent/databricks/notebooks/dlt_recipes_bronze_silver_gold"
      }
    }
  ],
  "clusters": [
    {
      "label": "default",
      "autoscale": {
        "min_workers": 1,
        "max_workers": 5,
        "mode": "ENHANCED"
      }
    }
  ],
  "configuration": {
    "source_path": "/mnt/cookidoo_agent/raw/recipes",
    "checkpoint_location": "/mnt/cookidoo_agent/checkpoints/recipes"
  },
  "notifications": [
    {
      "alerts": ["on-update-failure", "on-update-fatal-failure"],
      "email_recipients": ["data-team@company.com"]
    }
  ]
}
```

### Step 2: Create DLT Notebook (Bronze → Silver → Gold)

Save as notebook at `databricks/notebooks/dlt_recipes_bronze_silver_gold.ipynb`:

```python
# Databricks notebook source
import dlt
from pydantic import ValidationError
from datetime import datetime

# COMMAND ----------
# MAGIC %md
# MAGIC # Recipes DLT Pipeline: Bronze → Silver → Gold
# MAGIC
# MAGIC This notebook defines the Delta Live Tables pipeline for recipe data processing.

# COMMAND ----------
# Bronze Layer: Raw data ingestion

@dlt.table(
    name="recipes_bronze",
    comment="Raw recipe data from Cookidoo API via MCP server",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "ingestion_timestamp"
    }
)
def recipes_bronze():
    """
    Ingest raw recipe data from cloud storage (populated by MCP server).
    No transformations, just load and timestamp.
    """
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "/mnt/cookidoo_agent/schemas/recipes")
        .load("/mnt/cookidoo_agent/raw/recipes")
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("source_file", input_file_name())
    )

# COMMAND ----------
# Silver Layer: Cleaned and validated data

@dlt.table(
    name="recipes_silver",
    comment="Cleaned and validated recipe data",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true"
    }
)
@dlt.expect_all_or_drop({
    "valid_recipe_id": "recipe_id IS NOT NULL AND recipe_id != ''",
    "valid_title": "title IS NOT NULL AND LENGTH(title) > 0",
    "valid_servings": "servings IS NULL OR servings >= 1",
    "valid_times": "prep_time_minutes IS NULL OR prep_time_minutes >= 0"
})
def recipes_silver():
    """
    Apply data quality rules and transformations.
    - Remove duplicates
    - Validate required fields
    - Standardize formats
    - Enrich with calculated fields
    """
    from pyspark.sql import functions as F
    
    df = dlt.read_stream("recipes_bronze")
    
    return (
        df
        # Remove duplicates based on recipe_id, keeping latest
        .withWatermark("ingestion_timestamp", "1 hour")
        .dropDuplicates(["recipe_id"])
        
        # Calculate total time if missing
        .withColumn(
            "total_time_minutes",
            F.when(
                F.col("total_time_minutes").isNull(),
                F.coalesce(F.col("prep_time_minutes"), F.lit(0)) + 
                F.coalesce(F.col("cook_time_minutes"), F.lit(0))
            ).otherwise(F.col("total_time_minutes"))
        )
        
        # Standardize difficulty levels
        .withColumn(
            "difficulty",
            F.lower(F.trim(F.col("difficulty")))
        )
        
        # Add processing metadata
        .withColumn("processed_at", F.current_timestamp())
        .withColumn("data_quality_score", F.lit(1.0))  # Can be enhanced with scoring logic
    )

# COMMAND ----------
# Gold Layer: Analytics-ready aggregated data

@dlt.table(
    name="recipes_gold",
    comment="Analytics-ready recipe data with enrichments",
    table_properties={
        "quality": "gold"
    }
)
def recipes_gold():
    """
    Create aggregated, analytics-ready recipe data.
    - Add derived features
    - Create lookup-friendly structures
    - Optimize for query performance
    """
    from pyspark.sql import functions as F
    
    df = dlt.read("recipes_silver")
    
    return (
        df
        # Add derived features
        .withColumn("is_quick_recipe", F.col("total_time_minutes") <= 30)
        .withColumn("is_vegetarian", F.array_contains(F.col("dietary_info"), "vegetarian"))
        .withColumn("is_vegan", F.array_contains(F.col("dietary_info"), "vegan"))
        .withColumn("is_gluten_free", F.array_contains(F.col("dietary_info"), "gluten_free"))
        
        # Calculate ingredient count
        .withColumn("ingredient_count", F.size(F.col("ingredients")))
        .withColumn("step_count", F.size(F.col("steps")))
        
        # Create searchable text field
        .withColumn(
            "searchable_text",
            F.concat_ws(" ",
                F.col("title"),
                F.col("description"),
                F.array_join(F.col("tags"), " ")
            )
        )
    )

# COMMAND ----------
# Materialized view: Recipe statistics

@dlt.table(
    name="recipe_statistics",
    comment="Aggregated statistics about recipes"
)
def recipe_statistics():
    """
    Create summary statistics for dashboards and monitoring.
    """
    from pyspark.sql import functions as F
    
    return (
        dlt.read("recipes_gold")
        .groupBy()
        .agg(
            F.count("*").alias("total_recipes"),
            F.avg("total_time_minutes").alias("avg_total_time"),
            F.avg("servings").alias("avg_servings"),
            F.countDistinct("source").alias("unique_sources"),
            F.sum(F.when(F.col("is_vegetarian"), 1).otherwise(0)).alias("vegetarian_count"),
            F.sum(F.when(F.col("is_vegan"), 1).otherwise(0)).alias("vegan_count"),
            F.sum(F.when(F.col("is_quick_recipe"), 1).otherwise(0)).alias("quick_recipe_count")
        )
    )
```

### Step 3: Deploy DLT Pipeline

```powershell
# Using Databricks CLI
databricks pipelines create --json @databricks/dlt/recipes_pipeline.json

# Or using Python script
python databricks/scripts/deploy_dlt_pipeline.py
```

### Step 4: Start DLT Pipeline

```python
# databricks/scripts/start_dlt_pipeline.py
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import pipelines

w = WorkspaceClient()

# Find pipeline by name
pipeline_list = w.pipelines.list_pipelines()
pipeline = next((p for p in pipeline_list if p.name == "cookidoo_recipes_pipeline"), None)

if pipeline:
    # Start the pipeline
    update = w.pipelines.start_update(
        pipeline_id=pipeline.pipeline_id,
        full_refresh=False  # Set to True for complete refresh
    )
    
    print(f"Pipeline update started: {update.update_id}")
else:
    print("Pipeline not found")
```

---

## Vector Search Setup

Vector search enables semantic similarity searches for recipes, allowing users to find similar recipes based on ingredients, cooking methods, or flavor profiles.

### Step 1: Create Vector Search Endpoint

```python
# databricks/scripts/setup_vector_search.py
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (
    EndpointType,
    VectorIndexType,
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn
)

w = WorkspaceClient()

# Create vector search endpoint
endpoint = w.vector_search_endpoints.create_endpoint(
    name="cookidoo-vector-search",
    endpoint_type=EndpointType.STANDARD
)

print(f"Vector search endpoint created: {endpoint.name}")
```

### Step 2: Create Vector Index for Recipes

```python
# Wait for endpoint to be ready
import time
while True:
    endpoint_info = w.vector_search_endpoints.get_endpoint(name="cookidoo-vector-search")
    if endpoint_info.endpoint_status.state == "ONLINE":
        break
    print("Waiting for endpoint to come online...")
    time.sleep(30)

# Create vector index
index = w.vector_search_indexes.create_index(
    name="cookidoo_agent.main.recipe_embeddings_index",
    endpoint_name="cookidoo-vector-search",
    primary_key="recipe_id",
    index_type=VectorIndexType.DELTA_SYNC,
    delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
        source_table="cookidoo_agent.main.recipes_gold",
        embedding_source_columns=[
            EmbeddingSourceColumn(
                name="searchable_text",
                embedding_model_endpoint_name="databricks-bge-large-en"  # Use Databricks embedding model
            )
        ],
        pipeline_type="TRIGGERED"
    )
)

print(f"Vector index created: {index.name}")
```

### Step 3: Query Vector Index

```python
# Example: Find similar recipes
def find_similar_recipes(query_text: str, num_results: int = 10):
    """Find recipes similar to the query text."""
    
    results = w.vector_search_indexes.query_index(
        index_name="cookidoo_agent.main.recipe_embeddings_index",
        query_text=query_text,
        columns=["recipe_id", "title", "description", "tags"],
        num_results=num_results
    )
    
    return results.manifest.columns

# Usage
similar_recipes = find_similar_recipes("quick pasta dishes with vegetables")
```

---

## Model Serving Endpoints

### Step 1: Create Claude Sonnet 4.5 Endpoint (Primary)

```python
# databricks/scripts/create_model_endpoint.py
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    ServedEntityInput,
    EndpointCoreConfigInput,
    AutoCaptureConfigInput
)

w = WorkspaceClient()

# Create primary LLM endpoint (Claude Sonnet 4.5)
endpoint = w.serving_endpoints.create(
    name="cookidoo-agent-primary",
    config=EndpointCoreConfigInput(
        served_entities=[
            ServedEntityInput(
                entity_name="anthropic.claude-sonnet-4-5",
                entity_version="1",
                workload_size="Small",
                scale_to_zero_enabled=True,
                environment_vars={
                    "TEMPERATURE": "0.7",
                    "MAX_TOKENS": "2000"
                }
            )
        ],
        auto_capture_config=AutoCaptureConfigInput(
            catalog_name="cookidoo_agent",
            schema_name="ml",
            table_name_prefix="llm_inference_logs"
        )
    )
)

print(f"Model endpoint created: {endpoint.name}")
```

### Step 2: Test Model Endpoint

```python
# Test the endpoint
import requests
import os

def query_llm_endpoint(prompt: str) -> str:
    """Query the Claude Sonnet 4.5 endpoint."""
    
    workspace_url = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    url = f"{workspace_url}/serving-endpoints/cookidoo-agent-primary/invocations"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are an expert cooking assistant with deep knowledge of recipes and culinary techniques."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"]

# Test
result = query_llm_endpoint("How do I make pasta carbonara?")
print(result)
```

### Step 3: Create Analytics Endpoint (Claude Opus 4.1)

```python
# Create secondary endpoint for complex analytics tasks
analytics_endpoint = w.serving_endpoints.create(
    name="cookidoo-agent-analytics",
    config=EndpointCoreConfigInput(
        served_entities=[
            ServedEntityInput(
                entity_name="anthropic.claude-opus-4-1",
                entity_version="1",
                workload_size="Medium",
                scale_to_zero_enabled=True
            )
        ]
    )
)

print(f"Analytics endpoint created: {analytics_endpoint.name}")
```

---

## AgentBricks Configuration

AgentBricks orchestrates complex multi-step workflows involving the LLM, MCP server, and Databricks.

### Step 1: Install AgentBricks

```python
# Install in Databricks cluster
%pip install databricks-agents agentbricks mlflow

# Or add to cluster configuration
{
  "libraries": [
    {"pypi": {"package": "databricks-agents"}},
    {"pypi": {"package": "agentbricks"}},
    {"pypi": {"package": "mlflow>=2.10.0"}}
  ]
}
```

### Step 2: Define Recipe Modification Agent

Save as `databricks/notebooks/agent_recipe_modification.py`:

```python
# Databricks notebook source
from agentbricks import Agent, Tool, Chain
from databricks.sdk import WorkspaceClient
import mlflow

# COMMAND ----------

# Initialize workspace client
w = WorkspaceClient()

# COMMAND ----------

# Define tools for the agent
@Tool(name="get_recipe", description="Retrieve a recipe from Cookidoo by ID")
def get_recipe(recipe_id: str) -> dict:
    """Fetch recipe from Databricks table."""
    from pyspark.sql import functions as F
    
    recipe_df = spark.table("cookidoo_agent.main.recipes_gold").filter(
        F.col("recipe_id") == recipe_id
    )
    
    if recipe_df.count() == 0:
        raise ValueError(f"Recipe {recipe_id} not found")
    
    return recipe_df.first().asDict()

@Tool(name="query_llm", description="Query the LLM for recipe modifications")
def query_llm(prompt: str, system_prompt: str = None) -> str:
    """Query Claude Sonnet 4.5 endpoint."""
    import requests
    import os
    
    url = f"{os.getenv('DATABRICKS_HOST')}/serving-endpoints/cookidoo-agent-primary/invocations"
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = requests.post(
        url,
        json={"messages": messages, "max_tokens": 2000, "temperature": 0.7},
        headers={"Authorization": f"Bearer {os.getenv('DATABRICKS_TOKEN')}"}
    )
    
    return response.json()["choices"][0]["message"]["content"]

@Tool(name="save_recipe", description="Save modified recipe to Databricks")
def save_recipe(recipe_data: dict) -> str:
    """Save recipe to Delta table."""
    from pyspark.sql import Row
    from datetime import datetime
    
    recipe_data["updated_at"] = datetime.utcnow()
    
    recipe_df = spark.createDataFrame([Row(**recipe_data)])
    
    recipe_df.write.format("delta").mode("append").saveAsTable(
        "cookidoo_agent.main.recipes_gold"
    )
    
    return recipe_data["recipe_id"]

# COMMAND ----------

# Define the Recipe Modification Agent
class RecipeModificationAgent(Agent):
    """Agent for modifying recipes based on user requirements."""
    
    def __init__(self):
        super().__init__(
            name="RecipeModificationAgent",
            description="Modifies recipes based on natural language instructions",
            tools=[get_recipe, query_llm, save_recipe]
        )
    
    def modify_recipe(self, recipe_id: str, modification_prompt: str) -> dict:
        """
        Main workflow for recipe modification.
        
        Steps:
        1. Retrieve original recipe
        2. Generate modification using LLM
        3. Validate modifications
        4. Save modified recipe
        5. Return both versions
        """
        
        # Step 1: Get original recipe
        original_recipe = self.run_tool("get_recipe", recipe_id=recipe_id)
        
        # Step 2: Generate modification
        system_prompt = """You are an expert chef and recipe developer. 
        When modifying recipes, ensure:
        - Ingredient substitutions are culinarily sound
        - Cooking times/temps are adjusted appropriately
        - Instructions remain clear and actionable
        - The modified recipe will actually work
        
        Return the modified recipe in the same JSON structure as the original."""
        
        modification_prompt_full = f"""
        Original Recipe:
        {original_recipe}
        
        User Request: {modification_prompt}
        
        Please modify the recipe according to the user's request and return the complete modified recipe.
        """
        
        modified_recipe_str = self.run_tool(
            "query_llm",
            prompt=modification_prompt_full,
            system_prompt=system_prompt
        )
        
        # Parse and validate (simplified - add proper parsing)
        import json
        modified_recipe = json.loads(modified_recipe_str)
        
        # Step 3: Generate new recipe ID
        import uuid
        modified_recipe["recipe_id"] = f"modified_{uuid.uuid4().hex[:8]}"
        modified_recipe["source"] = "llm_generated"
        
        # Step 4: Save modified recipe
        new_recipe_id = self.run_tool("save_recipe", recipe_data=modified_recipe)
        
        # Step 5: Log modification to tracking table
        self._log_modification(original_recipe["recipe_id"], new_recipe_id, modification_prompt)
        
        return {
            "original_recipe": original_recipe,
            "modified_recipe": modified_recipe,
            "modification_prompt": modification_prompt
        }
    
    def _log_modification(self, original_id: str, modified_id: str, prompt: str):
        """Log modification to tracking table."""
        from pyspark.sql import Row
        from datetime import datetime
        import uuid
        
        log_data = {
            "modification_id": f"mod_{uuid.uuid4().hex[:12]}",
            "original_recipe_id": original_id,
            "modified_recipe_id": modified_id,
            "modification_prompt": prompt,
            "created_at": datetime.utcnow()
        }
        
        log_df = spark.createDataFrame([Row(**log_data)])
        log_df.write.format("delta").mode("append").saveAsTable(
            "cookidoo_agent.main.recipe_modifications"
        )

# COMMAND ----------

# Register agent with MLflow
agent = RecipeModificationAgent()

with mlflow.start_run(run_name="recipe_modification_agent"):
    mlflow.log_param("agent_name", agent.name)
    mlflow.log_param("model_endpoint", "cookidoo-agent-primary")
    
    # Test the agent
    test_result = agent.modify_recipe(
        recipe_id="cookidoo_12345",
        modification_prompt="Make this recipe vegan"
    )
    
    mlflow.log_dict(test_result, "test_modification.json")
    
    print("Agent registered successfully!")
```

---

## MCP Server Integration

The Model Context Protocol (MCP) server provides standardized access to the Cookidoo API.

### Databricks Integration Approach

Since the MCP server runs as an external service, we integrate it with Databricks through:

1. **REST API calls** from Databricks notebooks and jobs
2. **Data ingestion** - MCP server writes recipe data to cloud storage, which DLT pipelines consume
3. **Streaming integration** - Real-time recipe updates

### Step 1: Configure MCP Server Connection

```python
# databricks/notebooks/mcp_integration_config.py
import os
from databricks.sdk import WorkspaceClient

# Store MCP server configuration in Databricks secrets
w = WorkspaceClient()

# Create secret scope for MCP credentials
try:
    w.secrets.create_scope(scope="cookidoo-mcp")
except Exception:
    pass  # Scope already exists

# Store MCP server URL (actual secrets stored via CLI)
# databricks secrets put-secret cookidoo-mcp mcp-server-url
# databricks secrets put-secret cookidoo-mcp cookidoo-username
# databricks secrets put-secret cookidoo-mcp cookidoo-password

# Function to get MCP server URL
def get_mcp_config():
    return {
        "mcp_server_url": dbutils.secrets.get(scope="cookidoo-mcp", key="mcp-server-url"),
        "username": dbutils.secrets.get(scope="cookidoo-mcp", key="cookidoo-username"),
        "password": dbutils.secrets.get(scope="cookidoo-mcp", key="cookidoo-password")
    }
```

### Step 2: Create MCP Integration Functions

```python
# databricks/notebooks/mcp_integration_functions.py
import requests
from typing import Dict, List, Optional

def fetch_recipe_from_cookidoo(recipe_id: str) -> Dict:
    """Fetch a recipe from Cookidoo via MCP server."""
    
    config = get_mcp_config()
    
    response = requests.get(
        f"{config['mcp_server_url']}/api/recipes/{recipe_id}",
        headers={"Authorization": f"Bearer {get_mcp_auth_token()}"}
    )
    
    response.raise_for_status()
    return response.json()

def save_recipe_to_cookidoo(recipe_data: Dict) -> str:
    """Save a modified recipe to Cookidoo via MCP server."""
    
    config = get_mcp_config()
    
    response = requests.post(
        f"{config['mcp_server_url']}/api/recipes/save",
        json=recipe_data,
        headers={"Authorization": f"Bearer {get_mcp_auth_token()}"}
    )
    
    response.raise_for_status()
    return response.json()["recipe_id"]

def sync_recipes_to_delta():
    """
    Batch sync recipes from Cookidoo to Delta Lake.
    This function is run periodically to keep data fresh.
    """
    config = get_mcp_config()
    
    # Fetch recipe list
    response = requests.get(
        f"{config['mcp_server_url']}/api/recipes/list",
        headers={"Authorization": f"Bearer {get_mcp_auth_token()}"}
    )
    
    recipes = response.json()["recipes"]
    
    # Write to Delta bronze table
    from pyspark.sql import Row
    from datetime import datetime
    
    recipe_rows = [Row(**{**recipe, "ingestion_timestamp": datetime.utcnow()}) 
                   for recipe in recipes]
    
    recipes_df = spark.createDataFrame(recipe_rows)
    
    recipes_df.write.format("delta").mode("append").saveAsTable(
        "cookidoo_agent.staging.recipes_bronze"
    )
    
    return len(recipes)

# Helper function for authentication
def get_mcp_auth_token() -> str:
    """Get authentication token for MCP server."""
    config = get_mcp_config()
    
    response = requests.post(
        f"{config['mcp_server_url']}/auth/token",
        json={
            "username": config["username"],
            "password": config["password"]
        }
    )
    
    return response.json()["access_token"]
```

### Step 3: Schedule MCP Sync Job

```python
# databricks/scripts/schedule_mcp_sync_job.py
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import (
    Task,
    TaskDependency,
    NotebookTask,
    JobCluster,
    CronSchedule
)

w = WorkspaceClient()

# Create scheduled job for recipe sync
job = w.jobs.create(
    name="cookidoo_recipe_sync",
    tasks=[
        Task(
            task_key="sync_recipes",
            description="Sync recipes from Cookidoo via MCP server",
            notebook_task=NotebookTask(
                notebook_path="/Workspace/cookidoo-agent/databricks/notebooks/mcp_sync_recipes",
                base_parameters={}
            ),
            job_cluster_key="main_cluster"
        )
    ],
    job_clusters=[
        JobCluster(
            job_cluster_key="main_cluster",
            new_cluster={
                "spark_version": "14.3.x-scala2.12",
                "node_type_id": "Standard_DS3_v2",
                "num_workers": 2
            }
        )
    ],
    schedule=CronSchedule(
        quartz_cron_expression="0 0 2 * * ?",  # Daily at 2 AM
        timezone_id="UTC",
        pause_status="UNPAUSED"
    )
)

print(f"Sync job created: {job.job_id}")
```

---

## Genie Space Setup

Genie provides a natural language interface for analytics and data exploration.

### Step 1: Create Genie Space

```python
# Via Databricks UI or SDK
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Genie spaces are typically created through the UI
# Navigate to: Data Intelligence Platform → Genie → Create Space

# Configuration:
# - Name: "Cookidoo Recipe Analytics"
# - Description: "Natural language analytics for recipe data and user interactions"
# - Catalog: cookidoo_agent
# - Schemas: main, analytics
```

### Step 2: Configure Genie Instructions

Create instructions file for Genie to understand your domain:

```markdown
# Genie Instructions for Cookidoo Agent Analytics

## Domain Context
This workspace contains data about recipes, user interactions, modifications, and shopping lists
for the Cookidoo Agent Assistant platform.

## Key Tables
- **recipes_gold**: Main recipe data with full details
- **user_interactions**: User activity events
- **recipe_modifications**: Recipe modification history
- **shopping_lists**: User-generated shopping lists
- **recipe_statistics**: Aggregated metrics

## Common Queries
- "How many recipes do we have by difficulty level?"
- "What are the most popular dietary restrictions?"
- "Show me recipe modification trends over time"
- "Which recipes have the highest engagement?"
- "What's the average cooking time for vegan recipes?"

## Field Explanations
- **recipe_id**: Unique identifier for each recipe
- **is_quick_recipe**: Recipes with total_time_minutes <= 30
- **dietary_info**: Array of dietary tags (vegetarian, vegan, etc.)
- **interaction_type**: Type of user action (recipe_view, recipe_modify, chat, shopping_list)
```

### Step 3: Create Sample Genie Queries

```sql
-- Save these as "Saved Queries" in Genie for quick access

-- Query 1: Recipe popularity by difficulty
SELECT 
    difficulty,
    COUNT(*) as recipe_count,
    AVG(total_time_minutes) as avg_time
FROM cookidoo_agent.main.recipes_gold
GROUP BY difficulty
ORDER BY recipe_count DESC;

-- Query 2: User engagement trends
SELECT 
    DATE_TRUNC('day', timestamp) as date,
    interaction_type,
    COUNT(*) as interaction_count
FROM cookidoo_agent.main.user_interactions
WHERE timestamp >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY date, interaction_type
ORDER BY date DESC;

-- Query 3: Most modified recipes
SELECT 
    r.title,
    r.recipe_id,
    COUNT(m.modification_id) as modification_count
FROM cookidoo_agent.main.recipes_gold r
JOIN cookidoo_agent.main.recipe_modifications m 
    ON r.recipe_id = m.original_recipe_id
GROUP BY r.title, r.recipe_id
ORDER BY modification_count DESC
LIMIT 20;
```

---

## Notebooks Deployment

Deploy analytical and operational notebooks to the Databricks workspace.

### Step 1: Create Notebooks Directory Structure

```
/Workspace/cookidoo-agent/
├── databricks/
│   ├── notebooks/
│   │   ├── setup/
│   │   │   ├── 01_initial_setup.py
│   │   │   ├── 02_create_tables.sql
│   │   │   └── 03_load_sample_data.py
│   │   ├── dlt/
│   │   │   ├── dlt_recipes_bronze_silver_gold.py
│   │   │   └── dlt_interactions_pipeline.py
│   │   ├── analytics/
│   │   │   ├── recipe_analytics_dashboard.py
│   │   │   ├── user_engagement_analysis.py
│   │   │   └── modification_trends.py
│   │   └── agents/
│   │       ├── agent_recipe_modification.py
│   │       ├── agent_qa.py
│   │       └── agent_shopping_list.py
```

### Step 2: Deploy Notebooks via CLI

```powershell
# Import all notebooks to workspace
databricks workspace import-dir `
    ./databricks/notebooks `
    /Workspace/cookidoo-agent/databricks/notebooks `
    --overwrite

# Verify import
databricks workspace ls /Workspace/cookidoo-agent/databricks/notebooks
```

### Step 3: Create Analytics Dashboard Notebook

Save as `databricks/notebooks/analytics/recipe_analytics_dashboard.py`:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Recipe Analytics Dashboard
# MAGIC 
# MAGIC Comprehensive analytics for recipe data and user engagement.

# COMMAND ----------
import plotly.express as px
import plotly.graph_objects as go
from pyspark.sql import functions as F

# COMMAND ----------
# MAGIC %md
# MAGIC ## Recipe Overview Statistics

# COMMAND ----------
# Get recipe statistics
stats_df = spark.table("cookidoo_agent.main.recipe_statistics")
stats = stats_df.collect()[0]

# Display key metrics
displayHTML(f"""
<div style="display: flex; justify-content: space-around; margin: 20px;">
    <div style="text-align: center;">
        <h2>{stats.total_recipes:,}</h2>
        <p>Total Recipes</p>
    </div>
    <div style="text-align: center;">
        <h2>{stats.avg_total_time:.0f} min</h2>
        <p>Avg Cook Time</p>
    </div>
    <div style="text-align: center;">
        <h2>{stats.vegetarian_count:,}</h2>
        <p>Vegetarian</p>
    </div>
    <div style="text-align: center;">
        <h2>{stats.vegan_count:,}</h2>
        <p>Vegan</p>
    </div>
</div>
""")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Recipe Distribution by Difficulty

# COMMAND ----------
difficulty_df = (
    spark.table("cookidoo_agent.main.recipes_gold")
    .groupBy("difficulty")
    .agg(F.count("*").alias("count"))
    .toPandas()
)

fig = px.pie(
    difficulty_df,
    values='count',
    names='difficulty',
    title='Recipe Distribution by Difficulty Level'
)
fig.show()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Most Popular Recipe Tags

# COMMAND ----------
tags_df = (
    spark.table("cookidoo_agent.main.recipes_gold")
    .select(F.explode("tags").alias("tag"))
    .groupBy("tag")
    .agg(F.count("*").alias("count"))
    .orderBy(F.desc("count"))
    .limit(20)
    .toPandas()
)

fig = px.bar(
    tags_df,
    x='count',
    y='tag',
    orientation='h',
    title='Top 20 Recipe Tags'
)
fig.update_layout(yaxis={'categoryorder':'total ascending'})
fig.show()

# COMMAND ----------
# MAGIC %md
# MAGIC ## User Engagement Trends (Last 30 Days)

# COMMAND ----------
from datetime import datetime, timedelta

thirty_days_ago = datetime.now() - timedelta(days=30)

engagement_df = (
    spark.table("cookidoo_agent.main.user_interactions")
    .filter(F.col("timestamp") >= thirty_days_ago)
    .groupBy(
        F.date_trunc("day", "timestamp").alias("date"),
        "interaction_type"
    )
    .agg(F.count("*").alias("count"))
    .orderBy("date")
    .toPandas()
)

fig = px.line(
    engagement_df,
    x='date',
    y='count',
    color='interaction_type',
    title='User Engagement Trends (Last 30 Days)'
)
fig.show()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Recipe Modification Analysis

# COMMAND ----------
mod_trends_df = (
    spark.table("cookidoo_agent.main.recipe_modifications")
    .groupBy(F.date_trunc("day", "created_at").alias("date"))
    .agg(F.count("*").alias("modification_count"))
    .orderBy("date")
    .limit(90)
    .toPandas()
)

fig = px.area(
    mod_trends_df,
    x='date',
    y='modification_count',
    title='Recipe Modifications Over Time (Last 90 Days)'
)
fig.show()
```

---

## Monitoring & Logging

### Step 1: Enable Databricks Monitoring

```python
# Create monitoring dashboard in Databricks SQL

-- Query 1: Model endpoint performance
SELECT 
    timestamp,
    endpoint_name,
    status_code,
    execution_duration_ms,
    request_id
FROM system.serving.serving_endpoint_request_logs
WHERE endpoint_name IN ('cookidoo-agent-primary', 'cookidoo-agent-analytics')
    AND timestamp >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
ORDER BY timestamp DESC;

-- Query 2: DLT pipeline health
SELECT 
    pipeline_id,
    update_id,
    state,
    creation_time,
    latest_update_time
FROM system.pipelines.pipeline_update_events
WHERE pipeline_id = '<your-pipeline-id>'
ORDER BY creation_time DESC
LIMIT 100;

-- Query 3: Vector search query performance
SELECT 
    timestamp,
    index_name,
    query_text,
    num_results,
    execution_time_ms
FROM system.vector_search.query_logs
WHERE index_name = 'cookidoo_agent.main.recipe_embeddings_index'
ORDER BY timestamp DESC;
```

### Step 2: Set Up Alerts

```python
# databricks/scripts/setup_alerts.py
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import Alert, AlertOptions

w = WorkspaceClient()

# Create alert for high error rate
alert = w.alerts.create(
    name="cookidoo_agent_high_error_rate",
    options=AlertOptions(
        column="error_rate",
        op=">=",
        value=0.05,  # Alert if error rate >= 5%
        muted=False
    ),
    query_id="<your-query-id>",  # Query that calculates error rate
    rearm=3600  # Rearm after 1 hour
)
```

---

## Security & Access Control

### Step 1: Set Up Unity Catalog Permissions

```sql
-- Grant appropriate permissions to user groups

-- Data Engineers: Full access to staging and main schemas
GRANT ALL PRIVILEGES ON SCHEMA cookidoo_agent.staging TO `data_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA cookidoo_agent.main TO `data_engineers`;

-- ML Engineers: Access to ML schema and model serving
GRANT ALL PRIVILEGES ON SCHEMA cookidoo_agent.ml TO `ml_engineers`;
GRANT SELECT ON SCHEMA cookidoo_agent.main TO `ml_engineers`;

-- Analysts: Read access to main and analytics schemas
GRANT SELECT ON SCHEMA cookidoo_agent.main TO `analysts`;
GRANT SELECT ON SCHEMA cookidoo_agent.analytics TO `analysts`;

-- Application service principal: Limited access for production app
GRANT SELECT ON TABLE cookidoo_agent.main.recipes_gold TO `cookidoo_app_service_principal`;
GRANT INSERT ON TABLE cookidoo_agent.main.user_interactions TO `cookidoo_app_service_principal`;
GRANT INSERT ON TABLE cookidoo_agent.main.recipe_modifications TO `cookidoo_app_service_principal`;
```

### Step 2: Configure Secret Scopes

```powershell
# Create secret scope backed by Azure Key Vault
databricks secrets create-scope --scope cookidoo-production --scope-backend-type AZURE_KEYVAULT `
    --resource-id /subscriptions/{subscription-id}/resourceGroups/{rg}/providers/Microsoft.KeyVault/vaults/{vault-name} `
    --dns-name https://{vault-name}.vault.azure.net/

# Grant access to service principals
databricks secrets put-acl --scope cookidoo-production --principal cookidoo_app_service_principal --permission READ
```

---

## Deployment Checklist

Use this checklist to ensure complete deployment:

### Pre-Deployment
- [ ] Databricks workspace provisioned with Unity Catalog
- [ ] Azure Key Vault created and configured
- [ ] Service principals created for application access
- [ ] Databricks CLI configured locally
- [ ] All required permissions granted

### Catalog & Schema
- [ ] Unity Catalog `cookidoo_agent` created
- [ ] Schemas created: main, staging, analytics, ml
- [ ] Core tables created with proper constraints
- [ ] Indexes created for performance
- [ ] Permissions configured correctly

### Delta Live Tables
- [ ] DLT pipeline configuration files created
- [ ] DLT notebooks deployed to workspace
- [ ] Pipelines created and validated
- [ ] Initial pipeline runs successful
- [ ] Data quality expectations passing

### Vector Search
- [ ] Vector search endpoint created and online
- [ ] Recipe embeddings index created
- [ ] Initial embedding sync completed
- [ ] Query performance validated

### Model Serving
- [ ] Claude Sonnet 4.5 endpoint deployed (primary)
- [ ] Claude Opus 4.1 endpoint deployed (analytics)
- [ ] Endpoints tested and responding
- [ ] Auto-capture configured for inference logs
- [ ] Rate limiting configured

### AgentBricks
- [ ] AgentBricks library installed on clusters
- [ ] Recipe modification agent deployed
- [ ] Q&A agent deployed
- [ ] Shopping list agent deployed
- [ ] Agents registered in MLflow
- [ ] Agent workflows tested

### MCP Integration
- [ ] Secret scope created for MCP credentials
- [ ] MCP server URL and credentials stored
- [ ] Integration functions deployed
- [ ] Sync job scheduled
- [ ] Initial sync completed successfully

### Genie Space
- [ ] Genie space created
- [ ] Domain instructions configured
- [ ] Sample queries saved
- [ ] Access permissions granted

### Notebooks
- [ ] All notebooks imported to workspace
- [ ] Analytics dashboards functional
- [ ] Setup notebooks documented
- [ ] Notebook permissions configured

### Monitoring & Alerts
- [ ] Monitoring queries created
- [ ] Dashboards configured
- [ ] Alerts set up for critical metrics
- [ ] Log aggregation working

### Security
- [ ] All secrets stored in Key Vault/secret scopes
- [ ] Row-level security configured (if needed)
- [ ] Audit logging enabled
- [ ] Access policies reviewed and approved

### Documentation
- [ ] This deployment guide completed
- [ ] Architecture diagrams created
- [ ] Runbooks for common operations
- [ ] Disaster recovery plan documented

---

## Conclusion

This guide has walked through the complete Databricks setup for the Cookidoo Agent Assistant. Key achievements:

- **Structured data platform** with Unity Catalog, schemas, and Delta tables
- **Automated data pipelines** using Delta Live Tables for data quality
- **Semantic search capabilities** with vector search indexes
- **Production LLM serving** with Claude Sonnet 4.5 and Opus 4.1
- **Intelligent orchestration** using AgentBricks workflows
- **External integration** with Cookidoo API via MCP server
- **Analytics interface** through Genie Space
- **Operational notebooks** for analysis and monitoring

The platform is now ready for the backend application to connect and serve users with intelligent recipe assistance.

For questions or issues, refer to:
- Databricks documentation: https://docs.databricks.com
- Project repository: https://github.com/yourusername/cookidoo-agent
- Support: data-platform@company.com
