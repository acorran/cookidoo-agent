# Databricks notebook source
# MAGIC %md
# MAGIC # Delta Live Tables Pipeline - Recipe Data ETL
# MAGIC 
# MAGIC This notebook defines a Delta Live Tables (DLT) pipeline for the Cookidoo Agent Assistant.
# MAGIC 
# MAGIC **Pipeline Architecture:**
# MAGIC - **Bronze Layer**: Raw recipe data from Cookidoo API
# MAGIC - **Silver Layer**: Cleaned, validated, and deduplicated data
# MAGIC - **Gold Layer**: Business-ready aggregated datasets
# MAGIC 
# MAGIC **Run this as a DLT pipeline, not as a regular notebook**

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer - Raw Ingestion

# COMMAND ----------

@dlt.table(
    name="bronze_recipes",
    comment="Raw recipe data from Cookidoo API",
    table_properties={"quality": "bronze"}
)
def bronze_recipes():
    """
    Ingest raw recipe data from cloud storage or API landing zone.
    This table captures all raw data without transformation.
    """
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "/mnt/cookidoo/schemas/bronze_recipes")
        .option("cloudFiles.inferColumnTypes", "true")
        .load("/mnt/cookidoo/landing/recipes/")
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.input_file_name())
    )

# COMMAND ----------

@dlt.table(
    name="bronze_user_interactions",
    comment="Raw user interaction events",
    table_properties={"quality": "bronze"}
)
def bronze_user_interactions():
    """Ingest raw user interaction events from application logs."""
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", "/mnt/cookidoo/schemas/bronze_interactions")
        .load("/mnt/cookidoo/landing/interactions/")
        .withColumn("ingestion_timestamp", F.current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer - Cleaned and Validated

# COMMAND ----------

@dlt.table(
    name="silver_recipes",
    comment="Cleaned and validated recipe data",
    table_properties={"quality": "silver"}
)
@dlt.expect_all_or_drop({
    "valid_recipe_id": "recipe_id IS NOT NULL",
    "valid_title": "title IS NOT NULL AND LENGTH(title) > 0",
    "valid_servings": "servings > 0",
    "valid_times": "total_time_minutes >= 0"
})
def silver_recipes():
    """
    Clean and validate bronze recipes.
    - Remove duplicates
    - Validate required fields
    - Standardize data types
    - Add derived columns
    """
    return (
        dlt.read_stream("bronze_recipes")
        .select(
            F.col("recipe_id").cast("string").alias("recipe_id"),
            F.col("title").cast("string").alias("title"),
            F.col("description").cast("string").alias("description"),
            F.coalesce(F.col("servings").cast("int"), F.lit(4)).alias("servings"),
            F.col("prep_time_minutes").cast("int").alias("prep_time_minutes"),
            F.col("cook_time_minutes").cast("int").alias("cook_time_minutes"),
            F.col("total_time_minutes").cast("int").alias("total_time_minutes"),
            F.lower(F.col("difficulty")).alias("difficulty"),
            F.col("cuisine").cast("string").alias("cuisine"),
            F.col("meal_type").cast("string").alias("meal_type"),
            F.col("dietary_restrictions").alias("dietary_restrictions"),
            F.col("ingredients").alias("ingredients"),
            F.col("cooking_steps").alias("cooking_steps"),
            F.col("nutritional_info").alias("nutritional_info"),
            F.col("source").cast("string").alias("source"),
            F.col("image_url").cast("string").alias("image_url"),
            F.col("tags").alias("tags"),
            F.coalesce(
                F.col("created_at").cast("timestamp"),
                F.current_timestamp()
            ).alias("created_at"),
            F.current_timestamp().alias("updated_at"),
            F.current_timestamp().alias("ingested_at")
        )
        .withColumn(
            "ingredient_count",
            F.size(F.col("ingredients"))
        )
        .withColumn(
            "step_count",
            F.size(F.col("cooking_steps"))
        )
        .withColumn(
            "is_quick_recipe",
            F.when(F.col("total_time_minutes") <= 30, True).otherwise(False)
        )
        .dropDuplicates(["recipe_id"])
    )

# COMMAND ----------

@dlt.table(
    name="silver_user_interactions",
    comment="Cleaned user interaction events",
    table_properties={"quality": "silver"}
)
@dlt.expect_all_or_drop({
    "valid_interaction_id": "interaction_id IS NOT NULL",
    "valid_type": "interaction_type IN ('view', 'modify', 'save', 'chat', 'shopping_list')",
    "valid_timestamp": "timestamp IS NOT NULL"
})
def silver_user_interactions():
    """Clean and validate user interactions."""
    return (
        dlt.read_stream("bronze_user_interactions")
        .select(
            F.col("interaction_id").cast("string"),
            F.col("user_id").cast("string"),
            F.col("interaction_type").cast("string"),
            F.col("recipe_id").cast("string"),
            F.col("conversation_id").cast("string"),
            F.col("request_text").cast("string"),
            F.col("response_text").cast("string"),
            F.col("modifications_applied"),
            F.col("satisfaction_score").cast("double"),
            F.col("feedback").cast("string"),
            F.col("timestamp").cast("timestamp"),
            F.col("session_id").cast("string"),
            F.col("metadata")
        )
        .withColumn("date", F.to_date(F.col("timestamp")))
        .withColumn("hour", F.hour(F.col("timestamp")))
        .dropDuplicates(["interaction_id"])
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer - Business Aggregates

# COMMAND ----------

@dlt.table(
    name="gold_recipe_metrics",
    comment="Aggregated recipe performance metrics",
    table_properties={"quality": "gold"}
)
def gold_recipe_metrics():
    """
    Daily aggregated metrics per recipe.
    Used for analytics dashboards and recommendations.
    """
    interactions = dlt.read("silver_user_interactions")
    
    return (
        interactions
        .filter(F.col("recipe_id").isNotNull())
        .groupBy("recipe_id", "date")
        .agg(
            F.count("*").alias("total_interactions"),
            F.countDistinct("user_id").alias("unique_users"),
            F.sum(
                F.when(F.col("interaction_type") == "view", 1).otherwise(0)
            ).alias("view_count"),
            F.sum(
                F.when(F.col("interaction_type") == "modify", 1).otherwise(0)
            ).alias("modification_count"),
            F.sum(
                F.when(F.col("interaction_type") == "save", 1).otherwise(0)
            ).alias("save_count"),
            F.avg("satisfaction_score").alias("avg_satisfaction"),
            F.collect_list("modifications_applied").alias("all_modifications")
        )
        .withColumn("engagement_score", 
            F.col("view_count") + 
            (F.col("modification_count") * 2) + 
            (F.col("save_count") * 3)
        )
    )

# COMMAND ----------

@dlt.table(
    name="gold_user_activity",
    comment="Daily user activity summary",
    table_properties={"quality": "gold"}
)
def gold_user_activity():
    """Daily activity metrics per user."""
    interactions = dlt.read("silver_user_interactions")
    
    return (
        interactions
        .groupBy("user_id", "date")
        .agg(
            F.count("*").alias("total_interactions"),
            F.countDistinct("recipe_id").alias("unique_recipes"),
            F.countDistinct("session_id").alias("session_count"),
            F.sum(
                F.when(F.col("interaction_type") == "view", 1).otherwise(0)
            ).alias("recipes_viewed"),
            F.sum(
                F.when(F.col("interaction_type") == "modify", 1).otherwise(0)
            ).alias("recipes_modified"),
            F.sum(
                F.when(F.col("interaction_type") == "save", 1).otherwise(0)
            ).alias("recipes_saved"),
            F.sum(
                F.when(F.col("interaction_type") == "chat", 1).otherwise(0)
            ).alias("chat_interactions"),
            F.avg("satisfaction_score").alias("avg_satisfaction"),
            F.min("timestamp").alias("first_interaction"),
            F.max("timestamp").alias("last_interaction")
        )
        .withColumn(
            "session_duration_minutes",
            (F.unix_timestamp("last_interaction") - 
             F.unix_timestamp("first_interaction")) / 60
        )
    )

# COMMAND ----------

@dlt.table(
    name="gold_popular_modifications",
    comment="Most common recipe modifications by cuisine and meal type",
    table_properties={"quality": "gold"}
)
def gold_popular_modifications():
    """Identify popular modification patterns."""
    interactions = dlt.read("silver_user_interactions")
    recipes = dlt.read("silver_recipes")
    
    return (
        interactions
        .filter(F.col("interaction_type") == "modify")
        .filter(F.col("modifications_applied").isNotNull())
        .join(recipes, "recipe_id", "left")
        .select(
            F.explode("modifications_applied").alias("modification"),
            "cuisine",
            "meal_type",
            "difficulty",
            "date"
        )
        .groupBy("modification", "cuisine", "meal_type", "difficulty")
        .agg(
            F.count("*").alias("modification_count"),
            F.max("date").alias("last_used")
        )
        .filter(F.col("modification_count") > 5)
        .orderBy(F.desc("modification_count"))
    )

# COMMAND ----------

@dlt.table(
    name="gold_ingredient_popularity",
    comment="Popular and trending ingredients",
    table_properties={"quality": "gold"}
)
def gold_ingredient_popularity():
    """Track ingredient popularity across recipes."""
    recipes = dlt.read("silver_recipes")
    
    return (
        recipes
        .select(
            F.explode("ingredients").alias("ingredient"),
            "cuisine",
            "created_at"
        )
        .select(
            F.col("ingredient.name").alias("ingredient_name"),
            "cuisine",
            F.to_date("created_at").alias("date")
        )
        .groupBy("ingredient_name", "cuisine", "date")
        .agg(
            F.count("*").alias("recipe_count")
        )
        .withColumn(
            "rank",
            F.row_number().over(
                F.Window
                .partitionBy("date", "cuisine")
                .orderBy(F.desc("recipe_count"))
            )
        )
        .filter(F.col("rank") <= 50)
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Quality Monitoring

# COMMAND ----------

@dlt.table(
    name="data_quality_metrics",
    comment="Data quality monitoring for the pipeline"
)
def data_quality_metrics():
    """Track data quality metrics across the pipeline."""
    return spark.sql("""
        SELECT
            'bronze_recipes' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT recipe_id) as unique_recipes,
            SUM(CASE WHEN recipe_id IS NULL THEN 1 ELSE 0 END) as null_recipe_ids,
            current_timestamp() as check_timestamp
        FROM LIVE.bronze_recipes
        
        UNION ALL
        
        SELECT
            'silver_recipes' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT recipe_id) as unique_recipes,
            0 as null_recipe_ids,
            current_timestamp() as check_timestamp
        FROM LIVE.silver_recipes
    """)
