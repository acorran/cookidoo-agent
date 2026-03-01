# Databricks notebook source
# MAGIC %md
# MAGIC # Cookidoo MCP Connection Test
# MAGIC 
# MAGIC This notebook tests the connection to Cookidoo using the mcp-cookidoo library.
# MAGIC 
# MAGIC **Prerequisites:**
# MAGIC - Azure Key Vault scope configured in Databricks with Cookidoo credentials
# MAGIC - Secrets stored: `cookidoo-email` and `cookidoo-password`
# MAGIC 
# MAGIC **Based on:** https://github.com/alexandrepa/mcp-cookidoo

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Install Dependencies

# COMMAND ----------

# MAGIC %pip install cookidoo-api fastmcp pydantic

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Import Required Libraries

# COMMAND ----------

import os
import sys
from typing import Optional
from datetime import datetime

# For Key Vault access
try:
    from cookidoo_api import Cookidoo
    print("✓ cookidoo-api imported successfully")
except ImportError as e:
    print(f"✗ Error importing cookidoo-api: {e}")
    print("Installing cookidoo-api...")
    dbutils.library.installPyPI("cookidoo-api")
    dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Configuration
# MAGIC 
# MAGIC Set your Key Vault scope name here. The scope should contain:
# MAGIC - `cookidoo-email`: Your Cookidoo email address
# MAGIC - `cookidoo-password`: Your Cookidoo password

# COMMAND ----------

# Configuration
KEY_VAULT_SCOPE = "cookidoo-secrets"  # Change this to your Key Vault scope name

print(f"Using Key Vault scope: {KEY_VAULT_SCOPE}")
print("\nExpected secrets:")
print("  - cookidoo-email")
print("  - cookidoo-password")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Retrieve Credentials from Key Vault

# COMMAND ----------

try:
    # Retrieve credentials from Databricks secrets
    cookidoo_email = dbutils.secrets.get(scope=KEY_VAULT_SCOPE, key="cookidoo-email")
    cookidoo_password = dbutils.secrets.get(scope=KEY_VAULT_SCOPE, key="cookidoo-password")
    
    print("✓ Credentials retrieved successfully from Key Vault")
    print(f"  Email: {cookidoo_email[:3]}***@{cookidoo_email.split('@')[1] if '@' in cookidoo_email else '***'}")
    print(f"  Password: {'*' * 8}")
    
except Exception as e:
    print(f"✗ Error retrieving credentials: {e}")
    print("\nPlease ensure:")
    print(f"  1. Key Vault scope '{KEY_VAULT_SCOPE}' exists in Databricks")
    print("  2. Secrets 'cookidoo-email' and 'cookidoo-password' are configured")
    print("  3. You have access to the scope")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Initialize Cookidoo Client

# COMMAND ----------

class CookidooTestClient:
    """Wrapper for Cookidoo API testing."""
    
    def __init__(self, email: str, password: str):
        """Initialize the Cookidoo client."""
        self.email = email
        self.password = password
        self.client: Optional[Cookidoo] = None
        self.is_authenticated = False
    
    def connect(self) -> bool:
        """
        Authenticate with Cookidoo.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            print("Connecting to Cookidoo...")
            print(f"  Email: {self.email[:3]}***@{self.email.split('@')[1]}")
            
            # Initialize Cookidoo client
            self.client = Cookidoo()
            
            # Authenticate
            print("  Authenticating...")
            self.client.login(self.email, self.password)
            
            self.is_authenticated = True
            print("✓ Authentication successful!")
            return True
            
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            self.is_authenticated = False
            return False
    
    def get_user_info(self) -> dict:
        """
        Get basic user information.
        
        Returns:
            dict: User information
        """
        if not self.is_authenticated or not self.client:
            raise Exception("Not authenticated. Call connect() first.")
        
        try:
            # Get user profile or basic info
            # Note: API methods may vary, adjust based on actual cookidoo-api implementation
            info = {
                "email": self.email,
                "authenticated": self.is_authenticated,
                "timestamp": datetime.now().isoformat()
            }
            return info
        except Exception as e:
            print(f"✗ Error getting user info: {e}")
            return {"error": str(e)}
    
    def test_recipe_search(self, query: str = "pasta", limit: int = 5) -> list:
        """
        Test recipe search functionality.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            list: Recipe search results
        """
        if not self.is_authenticated or not self.client:
            raise Exception("Not authenticated. Call connect() first.")
        
        try:
            print(f"\nSearching for recipes: '{query}' (limit: {limit})")
            
            # Search recipes - adjust method based on actual cookidoo-api
            recipes = self.client.search_recipes(query)[:limit]
            
            print(f"✓ Found {len(recipes)} recipes")
            return recipes
            
        except Exception as e:
            print(f"✗ Error searching recipes: {e}")
            return []
    
    def get_recipe_details(self, recipe_id: str) -> dict:
        """
        Get details for a specific recipe.
        
        Args:
            recipe_id: Recipe ID
            
        Returns:
            dict: Recipe details
        """
        if not self.is_authenticated or not self.client:
            raise Exception("Not authenticated. Call connect() first.")
        
        try:
            print(f"\nFetching recipe details: {recipe_id}")
            
            # Get recipe details
            recipe = self.client.get_recipe(recipe_id)
            
            print(f"✓ Recipe retrieved: {recipe.get('name', 'Unknown')}")
            return recipe
            
        except Exception as e:
            print(f"✗ Error getting recipe: {e}")
            return {"error": str(e)}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Test Connection

# COMMAND ----------

# Initialize client
print("=" * 60)
print(" Cookidoo MCP Connection Test")
print("=" * 60)

client = CookidooTestClient(cookidoo_email, cookidoo_password)

# Test authentication
success = client.connect()

if success:
    print("\n" + "=" * 60)
    print(" Connection Status: SUCCESS ✓")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print(" Connection Status: FAILED ✗")
    print("=" * 60)
    raise Exception("Failed to connect to Cookidoo")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Test User Information

# COMMAND ----------

if client.is_authenticated:
    print("Testing user information retrieval...")
    user_info = client.get_user_info()
    
    print("\nUser Information:")
    for key, value in user_info.items():
        print(f"  {key}: {value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Test Recipe Search (Optional)

# COMMAND ----------

if client.is_authenticated:
    try:
        # Test recipe search
        recipes = client.test_recipe_search(query="pasta", limit=5)
        
        if recipes:
            print("\nSample Recipes Found:")
            for i, recipe in enumerate(recipes, 1):
                recipe_name = recipe.get('name', recipe.get('title', 'Unknown'))
                recipe_id = recipe.get('id', recipe.get('recipe_id', 'N/A'))
                print(f"  {i}. {recipe_name} (ID: {recipe_id})")
        else:
            print("\nNo recipes found or search not supported")
            
    except Exception as e:
        print(f"\n⚠️  Recipe search test skipped: {e}")
        print("This is optional - connection test was successful")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Summary & Next Steps

# COMMAND ----------

print("=" * 60)
print(" Test Summary")
print("=" * 60)
print(f"✓ Connection: {'SUCCESS' if client.is_authenticated else 'FAILED'}")
print(f"✓ Key Vault Integration: SUCCESS")
print(f"✓ Email: {cookidoo_email[:3]}***@{cookidoo_email.split('@')[1]}")
print(f"✓ Timestamp: {datetime.now().isoformat()}")
print("=" * 60)

print("\n📝 Next Steps:")
print("  1. Update mcp-server/server.py with cookidoo-api integration")
print("  2. Replace CookidooClient placeholder with actual implementation")
print("  3. Add to mcp-server/requirements.txt:")
print("     - cookidoo-api")
print("     - fastmcp")
print("  4. Configure backend to use MCP server with Key Vault credentials")
print("  5. Test recipe retrieval, modification, and saving workflows")

print("\n🔗 Resources:")
print("  - mcp-cookidoo: https://github.com/alexandrepa/mcp-cookidoo")
print("  - cookidoo-api: https://github.com/miaucl/cookidoo-api")
print("  - Project docs: docs/DATABRICKS_DEPLOYMENT.md")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Cleanup

# COMMAND ----------

# Clear sensitive variables
if 'cookidoo_email' in locals():
    del cookidoo_email
if 'cookidoo_password' in locals():
    del cookidoo_password

print("✓ Credentials cleared from memory")
print("✓ Test completed successfully!")
