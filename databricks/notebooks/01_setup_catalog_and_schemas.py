# Databricks notebook source
# MAGIC %md
# MAGIC # Cookidoo Agent Assistant - Initial Setup
# MAGIC 
# MAGIC This notebook sets up the foundational infrastructure for the Cookidoo Agent Assistant:
# MAGIC - Creates Unity Catalog, schemas, and tables
# MAGIC - Configures access permissions
# MAGIC - Initializes configuration tables
# MAGIC - Validates connections
# MAGIC 
# MAGIC **Prerequisites:**
# MAGIC - Databricks workspace with Unity Catalog enabled
# MAGIC - Catalog admin privileges
# MAGIC - Azure Key Vault configured with Cookidoo credentials

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Install Required Libraries

# COMMAND ----------

# MAGIC %pip install databricks-sdk mlflow azure-keyvault-secrets azure-identity

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Configuration

# COMMAND ----------

# Configuration variables
CATALOG_NAME = "cookidoo_agent"
SCHEMAS = {
    "main": "Main production schema for operational data",
    "staging": "Staging schema for data validation and testing",
    "analytics": "Analytics schema for aggregated insights",
    "ml": "Machine learning schema for models and features"
}

# Service principal or user groups
DATA_ENGINEERS_GROUP = "data_engineers"
DATA_SCIENTISTS_GROUP = "data_scientists"
ANALYSTS_GROUP = "analysts"

print(f"Catalog: {CATALOG_NAME}")
print(f"Schemas: {list(SCHEMAS.keys())}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create Catalog and Schemas

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create catalog if not exists
# MAGIC CREATE CATALOG IF NOT EXISTS cookidoo_agent
# MAGIC COMMENT 'Catalog for Cookidoo Agent Assistant application';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Use the catalog
# MAGIC USE CATALOG cookidoo_agent;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create main schema
# MAGIC CREATE SCHEMA IF NOT EXISTS main
# MAGIC COMMENT 'Main production schema for operational data';
# MAGIC 
# MAGIC -- Create staging schema
# MAGIC CREATE SCHEMA IF NOT EXISTS staging
# MAGIC COMMENT 'Staging schema for data validation and testing';
# MAGIC 
# MAGIC -- Create analytics schema
# MAGIC CREATE SCHEMA IF NOT EXISTS analytics
# MAGIC COMMENT 'Analytics schema for aggregated insights';
# MAGIC 
# MAGIC -- Create ml schema
# MAGIC CREATE SCHEMA IF NOT EXISTS ml
# MAGIC COMMENT 'Machine learning schema for models and features';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Create Tables in Main Schema

# COMMAND ----------

# MAGIC %sql
# MAGIC USE SCHEMA main;
# MAGIC 
# MAGIC -- Recipes table
# MAGIC CREATE TABLE IF NOT EXISTS recipes (
# MAGIC   recipe_id STRING NOT NULL,
# MAGIC   title STRING NOT NULL,
# MAGIC   description STRING,
# MAGIC   servings INT,
# MAGIC   prep_time_minutes INT,
# MAGIC   cook_time_minutes INT,
# MAGIC   total_time_minutes INT,
# MAGIC   difficulty STRING,
# MAGIC   cuisine STRING,
# MAGIC   meal_type STRING,
# MAGIC   dietary_restrictions ARRAY<STRING>,
# MAGIC   ingredients ARRAY<STRUCT<
# MAGIC     name: STRING,
# MAGIC     quantity: DOUBLE,
# MAGIC     unit: STRING,
# MAGIC     notes: STRING
# MAGIC   >>,
# MAGIC   cooking_steps ARRAY<STRUCT<
# MAGIC     step_number: INT,
# MAGIC     instruction: STRING,
# MAGIC     duration_minutes: INT,
# MAGIC     temperature: STRING
# MAGIC   >>,
# MAGIC   nutritional_info STRUCT<
# MAGIC     calories: DOUBLE,
# MAGIC     protein_g: DOUBLE,
# MAGIC     carbs_g: DOUBLE,
# MAGIC     fat_g: DOUBLE,
# MAGIC     fiber_g: DOUBLE,
# MAGIC     sugar_g: DOUBLE,
# MAGIC     sodium_mg: DOUBLE
# MAGIC   >,
# MAGIC   source STRING,
# MAGIC   image_url STRING,
# MAGIC   tags ARRAY<STRING>,
# MAGIC   created_at TIMESTAMP,
# MAGIC   updated_at TIMESTAMP,
# MAGIC   PRIMARY KEY (recipe_id)
# MAGIC )
# MAGIC COMMENT 'Recipes catalog from Cookidoo and user modifications';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- User interactions table
# MAGIC CREATE TABLE IF NOT EXISTS user_interactions (
# MAGIC   interaction_id STRING NOT NULL,
# MAGIC   user_id STRING,
# MAGIC   interaction_type STRING NOT NULL,
# MAGIC   recipe_id STRING,
# MAGIC   conversation_id STRING,
# MAGIC   request_text STRING,
# MAGIC   response_text STRING,
# MAGIC   modifications_applied ARRAY<STRING>,
# MAGIC   satisfaction_score DOUBLE,
# MAGIC   feedback STRING,
# MAGIC   timestamp TIMESTAMP NOT NULL,
# MAGIC   session_id STRING,
# MAGIC   metadata MAP<STRING, STRING>,
# MAGIC   PRIMARY KEY (interaction_id)
# MAGIC )
# MAGIC PARTITIONED BY (DATE(timestamp))
# MAGIC COMMENT 'User interactions with the LLM assistant';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Shopping lists table
# MAGIC CREATE TABLE IF NOT EXISTS shopping_lists (
# MAGIC   list_id STRING NOT NULL,
# MAGIC   user_id STRING,
# MAGIC   recipe_ids ARRAY<STRING>,
# MAGIC   items ARRAY<STRUCT<
# MAGIC     name: STRING,
# MAGIC     quantity: DOUBLE,
# MAGIC     unit: STRING,
# MAGIC     category: STRING,
# MAGIC     checked: BOOLEAN,
# MAGIC     notes: STRING,
# MAGIC     from_recipes: ARRAY<STRING>
# MAGIC   >>,
# MAGIC   created_at TIMESTAMP,
# MAGIC   updated_at TIMESTAMP,
# MAGIC   total_items INT,
# MAGIC   checked_items INT,
# MAGIC   PRIMARY KEY (list_id)
# MAGIC )
# MAGIC COMMENT 'Generated shopping lists from recipes';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Conversation history table
# MAGIC CREATE TABLE IF NOT EXISTS conversation_history (
# MAGIC   conversation_id STRING NOT NULL,
# MAGIC   user_id STRING,
# MAGIC   messages ARRAY<STRUCT<
# MAGIC     role: STRING,
# MAGIC     content: STRING,
# MAGIC     timestamp: TIMESTAMP
# MAGIC   >>,
# MAGIC   context MAP<STRING, STRING>,
# MAGIC   created_at TIMESTAMP,
# MAGIC   updated_at TIMESTAMP,
# MAGIC   message_count INT,
# MAGIC   PRIMARY KEY (conversation_id)
# MAGIC )
# MAGIC COMMENT 'Conversation history for chat sessions';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Create Analytics Tables

# COMMAND ----------

# MAGIC %sql
# MAGIC USE SCHEMA analytics;
# MAGIC 
# MAGIC -- Recipe popularity metrics
# MAGIC CREATE TABLE IF NOT EXISTS recipe_popularity (
# MAGIC   recipe_id STRING NOT NULL,
# MAGIC   date DATE NOT NULL,
# MAGIC   view_count INT DEFAULT 0,
# MAGIC   modification_count INT DEFAULT 0,
# MAGIC   save_count INT DEFAULT 0,
# MAGIC   average_rating DOUBLE,
# MAGIC   unique_users INT DEFAULT 0,
# MAGIC   PRIMARY KEY (recipe_id, date)
# MAGIC )
# MAGIC PARTITIONED BY (date)
# MAGIC COMMENT 'Daily recipe popularity metrics';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- User engagement metrics
# MAGIC CREATE TABLE IF NOT EXISTS user_engagement (
# MAGIC   user_id STRING NOT NULL,
# MAGIC   date DATE NOT NULL,
# MAGIC   total_interactions INT DEFAULT 0,
# MAGIC   recipes_viewed INT DEFAULT 0,
# MAGIC   recipes_modified INT DEFAULT 0,
# MAGIC   recipes_saved INT DEFAULT 0,
# MAGIC   chat_messages INT DEFAULT 0,
# MAGIC   shopping_lists_created INT DEFAULT 0,
# MAGIC   session_duration_minutes DOUBLE,
# MAGIC   PRIMARY KEY (user_id, date)
# MAGIC )
# MAGIC PARTITIONED BY (date)
# MAGIC COMMENT 'Daily user engagement metrics';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Create ML Feature Tables

# COMMAND ----------

# MAGIC %sql
# MAGIC USE SCHEMA ml;
# MAGIC 
# MAGIC -- Recipe embeddings for vector search
# MAGIC CREATE TABLE IF NOT EXISTS recipe_embeddings (
# MAGIC   recipe_id STRING NOT NULL,
# MAGIC   title STRING,
# MAGIC   embedding ARRAY<DOUBLE>,
# MAGIC   embedding_model STRING,
# MAGIC   created_at TIMESTAMP,
# MAGIC   PRIMARY KEY (recipe_id)
# MAGIC )
# MAGIC COMMENT 'Recipe embeddings for similarity search';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- User preference features
# MAGIC CREATE TABLE IF NOT EXISTS user_features (
# MAGIC   user_id STRING NOT NULL,
# MAGIC   preferred_cuisines ARRAY<STRING>,
# MAGIC   dietary_restrictions ARRAY<STRING>,
# MAGIC   skill_level STRING,
# MAGIC   avg_prep_time_preference INT,
# MAGIC   favorite_ingredients ARRAY<STRING>,
# MAGIC   disliked_ingredients ARRAY<STRING>,
# MAGIC   interaction_frequency_days DOUBLE,
# MAGIC   last_interaction TIMESTAMP,
# MAGIC   updated_at TIMESTAMP,
# MAGIC   PRIMARY KEY (user_id)
# MAGIC )
# MAGIC COMMENT 'User preference features for personalization';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Grant Permissions

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant SELECT on all schemas to analysts
# MAGIC GRANT USE CATALOG ON CATALOG cookidoo_agent TO `analysts`;
# MAGIC GRANT USE SCHEMA ON SCHEMA cookidoo_agent.main TO `analysts`;
# MAGIC GRANT USE SCHEMA ON SCHEMA cookidoo_agent.analytics TO `analysts`;
# MAGIC GRANT SELECT ON SCHEMA cookidoo_agent.main TO `analysts`;
# MAGIC GRANT SELECT ON SCHEMA cookidoo_agent.analytics TO `analysts`;
# MAGIC 
# MAGIC -- Grant full access to data engineers
# MAGIC GRANT USE CATALOG ON CATALOG cookidoo_agent TO `data_engineers`;
# MAGIC GRANT ALL PRIVILEGES ON CATALOG cookidoo_agent TO `data_engineers`;
# MAGIC 
# MAGIC -- Grant ML schema access to data scientists
# MAGIC GRANT USE CATALOG ON CATALOG cookidoo_agent TO `data_scientists`;
# MAGIC GRANT USE SCHEMA ON SCHEMA cookidoo_agent.ml TO `data_scientists`;
# MAGIC GRANT ALL PRIVILEGES ON SCHEMA cookidoo_agent.ml TO `data_scientists`;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Validate Setup

# COMMAND ----------

# Validate catalogs and schemas
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# List catalogs
print("=== Available Catalogs ===")
catalogs = spark.sql("SHOW CATALOGS").collect()
for catalog in catalogs:
    print(f"  - {catalog.catalog}")

# List schemas in cookidoo_agent
print("\n=== Schemas in cookidoo_agent ===")
schemas = spark.sql("SHOW SCHEMAS IN cookidoo_agent").collect()
for schema in schemas:
    print(f"  - {schema.databaseName}")

# List tables in main schema
print("\n=== Tables in cookidoo_agent.main ===")
tables = spark.sql("SHOW TABLES IN cookidoo_agent.main").collect()
for table in tables:
    print(f"  - {table.tableName}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Create Configuration Table

# COMMAND ----------

# MAGIC %sql
# MAGIC USE SCHEMA main;
# MAGIC 
# MAGIC CREATE TABLE IF NOT EXISTS system_config (
# MAGIC   config_key STRING NOT NULL,
# MAGIC   config_value STRING,
# MAGIC   config_type STRING,
# MAGIC   description STRING,
# MAGIC   updated_at TIMESTAMP,
# MAGIC   updated_by STRING,
# MAGIC   PRIMARY KEY (config_key)
# MAGIC )
# MAGIC COMMENT 'System configuration key-value pairs';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Insert default configurations
# MAGIC MERGE INTO system_config AS target
# MAGIC USING (
# MAGIC   SELECT * FROM VALUES
# MAGIC     ('llm_model', 'claude-sonnet-4.5-20250514', 'string', 'Primary LLM model for recipe modifications'),
# MAGIC     ('llm_temperature', '0.7', 'float', 'Temperature for LLM responses'),
# MAGIC     ('max_tokens', '4096', 'int', 'Maximum tokens for LLM responses'),
# MAGIC     ('vector_search_index', 'recipe_embeddings_index', 'string', 'Name of the vector search index'),
# MAGIC     ('embedding_model', 'text-embedding-ada-002', 'string', 'Model for generating embeddings'),
# MAGIC     ('cache_ttl_seconds', '3600', 'int', 'Cache TTL in seconds'),
# MAGIC     ('rate_limit_per_minute', '60', 'int', 'API rate limit per minute'),
# MAGIC     ('version', '1.0.0', 'string', 'Application version')
# MAGIC   AS configs(config_key, config_value, config_type, description)
# MAGIC ) AS source
# MAGIC ON target.config_key = source.config_key
# MAGIC WHEN NOT MATCHED THEN
# MAGIC   INSERT (config_key, config_value, config_type, description, updated_at, updated_by)
# MAGIC   VALUES (source.config_key, source.config_value, source.config_type, source.description, current_timestamp(), current_user());

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM system_config ORDER BY config_key;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Summary

# COMMAND ----------

print("=" * 60)
print(" Setup Complete!")
print("=" * 60)
print(f"\nCatalog: {CATALOG_NAME}")
print(f"Schemas: {', '.join(SCHEMAS.keys())}")
print("\nTables created:")
print("  main:")
print("    - recipes")
print("    - user_interactions")
print("    - shopping_lists")
print("    - conversation_history")
print("    - system_config")
print("  analytics:")
print("    - recipe_popularity")
print("    - user_engagement")
print("  ml:")
print("    - recipe_embeddings")
print("    - user_features")
print("\nNext steps:")
print("  1. Run the DLT pipeline setup notebook")
print("  2. Configure vector search index")
print("  3. Deploy model endpoints")
print("  4. Set up AgentBricks agent")
print("=" * 60)
