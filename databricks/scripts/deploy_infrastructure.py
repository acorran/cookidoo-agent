"""
Setup script for deploying Databricks infrastructure via Python SDK.

This script automates:
- Catalog and schema creation
- DLT pipeline deployment
- Vector search index setup
- Model endpoint deployment
"""

import os
import sys
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import *
from databricks.sdk.service.pipelines import *
from databricks.sdk.service.serving import *


class DatabricksDeployer:
    """Handles deployment of Databricks resources."""
    
    def __init__(self, workspace_url: str, token: str):
        """Initialize Databricks client."""
        self.client = WorkspaceClient(
            host=workspace_url,
            token=token
        )
        self.catalog_name = "cookidoo_agent"
        
    def create_catalog_and_schemas(self):
        """Create Unity Catalog and schemas."""
        print(f"Creating catalog: {self.catalog_name}")
        
        try:
            # Create catalog
            self.client.catalogs.create(
                name=self.catalog_name,
                comment="Catalog for Cookidoo Agent Assistant application"
            )
            print(f"✓ Catalog '{self.catalog_name}' created")
        except Exception as e:
            print(f"Catalog may already exist: {e}")
        
        # Create schemas
        schemas = {
            "main": "Main production schema for operational data",
            "staging": "Staging schema for data validation and testing",
            "analytics": "Analytics schema for aggregated insights",
            "ml": "Machine learning schema for models and features"
        }
        
        for schema_name, comment in schemas.items():
            try:
                self.client.schemas.create(
                    catalog_name=self.catalog_name,
                    name=schema_name,
                    comment=comment
                )
                print(f"✓ Schema '{schema_name}' created")
            except Exception as e:
                print(f"Schema '{schema_name}' may already exist: {e}")
    
    def deploy_dlt_pipeline(self, notebook_path: str, storage_path: str):
        """Deploy Delta Live Tables pipeline."""
        print("\nDeploying DLT pipeline...")
        
        pipeline_config = {
            "name": "cookidoo_recipe_etl",
            "storage": storage_path,
            "configuration": {
                "catalog": self.catalog_name,
                "target_schema": "main"
            },
            "clusters": [
                {
                    "label": "default",
                    "num_workers": 2,
                    "spark_conf": {
                        "spark.databricks.delta.preview.enabled": "true"
                    }
                }
            ],
            "libraries": [
                {"notebook": {"path": notebook_path}}
            ],
            "continuous": False,
            "development": True,
            "edition": "ADVANCED",
            "channel": "CURRENT"
        }
        
        try:
            pipeline = self.client.pipelines.create(**pipeline_config)
            print(f"✓ DLT Pipeline created: {pipeline.pipeline_id}")
            return pipeline.pipeline_id
        except Exception as e:
            print(f"Error creating pipeline: {e}")
            return None
    
    def create_vector_search_index(
        self,
        index_name: str,
        source_table: str,
        embedding_column: str,
        primary_key: str
    ):
        """Create vector search index (placeholder - requires Databricks Vector Search API)."""
        print(f"\nCreating vector search index: {index_name}")
        print(f"  Source table: {source_table}")
        print(f"  Embedding column: {embedding_column}")
        print(f"  Primary key: {primary_key}")
        
        # Note: Vector Search API may require different SDK version
        # This is a placeholder showing the structure
        print("⚠ Vector search creation requires additional configuration")
        print("  Run the setup notebook or use Databricks UI to complete")
    
    def deploy_model_endpoint(
        self,
        endpoint_name: str,
        model_name: str,
        model_version: str
    ):
        """Deploy a model serving endpoint."""
        print(f"\nDeploying model endpoint: {endpoint_name}")
        
        try:
            endpoint_config = {
                "name": endpoint_name,
                "config": {
                    "served_models": [
                        {
                            "model_name": model_name,
                            "model_version": model_version,
                            "workload_size": "Small",
                            "scale_to_zero_enabled": True
                        }
                    ],
                    "traffic_config": {
                        "routes": [
                            {
                                "served_model_name": f"{model_name}-{model_version}",
                                "traffic_percentage": 100
                            }
                        ]
                    }
                }
            }
            
            endpoint = self.client.serving_endpoints.create(**endpoint_config)
            print(f"✓ Model endpoint created: {endpoint.name}")
            return endpoint.name
        except Exception as e:
            print(f"Error creating endpoint: {e}")
            return None
    
    def setup_permissions(self):
        """Set up workspace permissions."""
        print("\nSetting up permissions...")
        print("⚠ Permissions should be configured via Databricks Admin Console")
        print("  Required groups: data_engineers, data_scientists, analysts")


def main():
    """Main deployment function."""
    # Get credentials from environment
    workspace_url = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    
    if not workspace_url or not token:
        print("Error: Set DATABRICKS_HOST and DATABRICKS_TOKEN environment variables")
        sys.exit(1)
    
    print("=" * 70)
    print(" Databricks Infrastructure Deployment")
    print("=" * 70)
    
    deployer = DatabricksDeployer(workspace_url, token)
    
    # Step 1: Create catalog and schemas
    print("\n[1/4] Creating catalog and schemas...")
    deployer.create_catalog_and_schemas()
    
    # Step 2: Deploy DLT pipeline
    print("\n[2/4] Deploying DLT pipeline...")
    notebook_path = "/Workspace/Users/<your-email>/cookidoo-agent/notebooks/02_dlt_pipeline"
    storage_path = "dbfs:/pipelines/cookidoo_agent"
    pipeline_id = deployer.deploy_dlt_pipeline(notebook_path, storage_path)
    
    # Step 3: Create vector search index
    print("\n[3/4] Setting up vector search...")
    deployer.create_vector_search_index(
        index_name="recipe_embeddings_index",
        source_table=f"{deployer.catalog_name}.ml.recipe_embeddings",
        embedding_column="embedding",
        primary_key="recipe_id"
    )
    
    # Step 4: Configure permissions
    print("\n[4/4] Configuring permissions...")
    deployer.setup_permissions()
    
    print("\n" + "=" * 70)
    print(" Deployment Summary")
    print("=" * 70)
    print(f"Catalog: {deployer.catalog_name}")
    print("Schemas: main, staging, analytics, ml")
    if pipeline_id:
        print(f"DLT Pipeline ID: {pipeline_id}")
    print("\nNext steps:")
    print("1. Upload notebooks to Databricks workspace")
    print("2. Run the setup notebook: 01_setup_catalog_and_schemas")
    print("3. Start the DLT pipeline")
    print("4. Complete vector search configuration")
    print("5. Deploy model endpoints")
    print("=" * 70)


if __name__ == "__main__":
    main()
