"""
Schedule the MCP Recipe Sync job on Databricks.

This script creates a Databricks Job that runs the 05_mcp_sync_recipes
notebook on a daily schedule. It can also be run manually.

Usage:
    python deploy_mcp_sync_job.py

Prerequisites:
    - Databricks CLI configured (databricks configure --token)
    - Or DATABRICKS_HOST and DATABRICKS_TOKEN environment variables set
"""

import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_sync_job():
    """Create the MCP recipe sync job on Databricks."""
    try:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.jobs import (
            CronSchedule,
            JobCluster,
            NotebookTask,
            Task,
        )
    except ImportError:
        logger.error("databricks-sdk not installed. Run: pip install databricks-sdk")
        sys.exit(1)

    w = WorkspaceClient()

    notebook_path = "/Workspace/cookidoo-agent/databricks/notebooks/05_mcp_sync_recipes"

    job = w.jobs.create(
        name="cookidoo_mcp_recipe_sync",
        tags={"project": "cookidoo-agent", "component": "mcp-sync"},
        tasks=[
            Task(
                task_key="sync_recipes",
                description=(
                    "Sync recipes from Cookidoo via MCP server REST API "
                    "into Delta Lake bronze table."
                ),
                notebook_task=NotebookTask(
                    notebook_path=notebook_path,
                    base_parameters={
                        "key_vault_scope": "cookidoo-secrets",
                        "mcp_scope": "cookidoo-mcp",
                        "target_table": "cookidoo_agent.staging.recipes_bronze",
                        "search_queries": "all",
                    },
                ),
                job_cluster_key="sync_cluster",
            ),
        ],
        job_clusters=[
            JobCluster(
                job_cluster_key="sync_cluster",
                new_cluster={
                    "spark_version": "14.3.x-scala2.12",
                    "node_type_id": "Standard_DS3_v2",
                    "num_workers": 0,  # Single node – sufficient for API calls
                    "spark_conf": {
                        "spark.databricks.cluster.profile": "singleNode",
                        "spark.master": "local[*]",
                    },
                },
            ),
        ],
        schedule=CronSchedule(
            quartz_cron_expression="0 0 2 * * ?",  # Daily at 2 AM UTC
            timezone_id="UTC",
            pause_status="UNPAUSED",
        ),
        max_concurrent_runs=1,
    )

    logger.info(f"✓ Sync job created: ID={job.job_id}")
    logger.info(f"  Name: cookidoo_mcp_recipe_sync")
    logger.info(f"  Notebook: {notebook_path}")
    logger.info(f"  Schedule: Daily at 2:00 AM UTC")
    logger.info(f"  Cluster: Single-node Standard_DS3_v2")

    return job.job_id


if __name__ == "__main__":
    job_id = create_sync_job()
    print(f"\nJob ID: {job_id}")
    print("Run manually: databricks jobs run-now --job-id", job_id)
