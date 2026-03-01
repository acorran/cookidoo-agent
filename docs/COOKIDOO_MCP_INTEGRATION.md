# Cookidoo MCP Integration Guide

## Overview

This guide shows how to integrate the **mcp-cookidoo** library into the Cookidoo Agent Assistant project.

**Repository**: https://github.com/alexandrepa/mcp-cookidoo  
**Base Library**: https://github.com/miaucl/cookidoo-api

## Quick Test

A Databricks notebook has been created for testing: `databricks/notebooks/00_test_cookidoo_connection.ipynb`

### Prerequisites

1. **Azure Key Vault Scope** in Databricks with secrets:
   - `cookidoo-email`: Your Cookidoo account email
   - `cookidoo-password`: Your Cookidoo account password

2. **Run the test notebook:**
   ```python
   # In Databricks, open and run:
   # databricks/notebooks/00_test_cookidoo_connection.ipynb
   
   # Set your Key Vault scope name in cell #3:
   KEY_VAULT_SCOPE = "cookidoo-secrets"  # Your scope name
   ```

## Integration Steps

### 1. Update MCP Server Dependencies

Add to `mcp-server/requirements.txt`:

```txt
cookidoo-api>=0.5.0
fastmcp>=0.1.0
```

Install:
```powershell
cd mcp-server
.\venv\Scripts\Activate.ps1
pip install cookidoo-api fastmcp
```

### 2. Update MCP Server Implementation

The current `mcp-server/server.py` has placeholder code. Here's how to integrate cookidoo-api:

**File: `mcp-server/server.py`**

```python
"""
Model Context Protocol (MCP) Server for Cookidoo API Integration
Uses: https://github.com/alexandrepa/mcp-cookidoo
"""

import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn

# Import cookidoo-api
try:
    from cookidoo_api import Cookidoo
    COOKIDOO_AVAILABLE = True
except ImportError:
    COOKIDOO_AVAILABLE = False
    logging.warning("cookidoo-api not available. Install: pip install cookidoo-api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Cookidoo MCP Server",
    description="Model Context Protocol server for Cookidoo API integration",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class RecipeSearchRequest(BaseModel):
    query: str
    limit: int = 20


class CookidooClientWrapper:
    """Wrapper for Cookidoo API client with session management."""
    
    def __init__(self):
        """Initialize the client."""
        if not COOKIDOO_AVAILABLE:
            raise ImportError("cookidoo-api required: pip install cookidoo-api")
        
        self.client: Optional[Cookidoo] = None
        self.authenticated = False
        self.email: Optional[str] = None
    
    def authenticate(self, email: str, password: str) -> bool:
        """
        Authenticate with Cookidoo.
        
        Args:
            email: Cookidoo account email
            password: Cookidoo account password
            
        Returns:
            bool: True if successful
        """
        try:
            self.client = Cookidoo()
            self.client.login(email, password)
            self.authenticated = True
            self.email = email
            logger.info(f"✓ Authenticated: {email}")
            return True
        except Exception as e:
            logger.error(f"✗ Authentication failed: {e}")
            self.authenticated = False
            raise
    
    def get_recipe(self, recipe_id: str) -> Dict:
        """
        Get recipe details by ID.
        
        Args:
            recipe_id: Recipe ID
            
        Returns:
            dict: Recipe details
        """
        if not self.authenticated or not self.client:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        try:
            recipe = self.client.get_recipe(recipe_id)
            return recipe
        except Exception as e:
            logger.error(f"Error fetching recipe {recipe_id}: {e}")
            raise HTTPException(status_code=404, detail=str(e))
    
    def search_recipes(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for recipes.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            list: Recipe list
        """
        if not self.authenticated or not self.client:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        try:
            recipes = self.client.search_recipes(query)
            return recipes[:limit] if recipes else []
        except Exception as e:
            logger.error(f"Error searching recipes: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def save_recipe(self, recipe_data: Dict) -> Dict:
        """
        Save custom recipe to Cookidoo.
        
        Args:
            recipe_data: Recipe data
            
        Returns:
            dict: Saved recipe
        """
        if not self.authenticated or not self.client:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        try:
            result = self.client.create_recipe(recipe_data)
            return result
        except Exception as e:
            logger.error(f"Error saving recipe: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Global client instance (in production, use session-based)
cookidoo_client = CookidooClientWrapper()


# Endpoints
@app.post("/auth/login", response_model=AuthResponse)
async def login(auth: AuthRequest):
    """Authenticate with Cookidoo."""
    try:
        cookidoo_client.authenticate(auth.username, auth.password)
        
        # Generate token (simplified - use JWT in production)
        token = f"cookidoo_{auth.username}_{hash(auth.password)}"
        
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            expires_in=3600
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    """Get recipe by ID."""
    return cookidoo_client.get_recipe(recipe_id)


@app.post("/recipes/search")
async def search_recipes(request: RecipeSearchRequest):
    """Search for recipes."""
    return cookidoo_client.search_recipes(request.query, request.limit)


@app.post("/recipes")
async def save_recipe(recipe_data: Dict):
    """Save custom recipe."""
    return cookidoo_client.save_recipe(recipe_data)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "authenticated": cookidoo_client.authenticated,
        "cookidoo_api_available": COOKIDOO_AVAILABLE
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 3. Update Backend to Use MCP Server

**File: `backend/services/recipe_service.py`**

Update the `get_recipe` method:

```python
async def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
    """
    Fetch recipe from Cookidoo via MCP server.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.MCP_SERVER_URL}/recipes/{recipe_id}",
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            return Recipe(**data)
            
    except Exception as e:
        logger.error(f"Error fetching recipe: {e}")
        return None
```

### 4. Configure Environment Variables

**File: `backend/.env`**

```env
# MCP Server
MCP_SERVER_URL=http://localhost:8001

# Cookidoo Credentials (store in Azure Key Vault in production)
COOKIDOO_EMAIL=your-email@example.com
COOKIDOO_PASSWORD=your-password
```

**File: `mcp-server/.env`**

```env
# Server Configuration
HOST=0.0.0.0
PORT=8001

# Cookidoo Credentials
COOKIDOO_EMAIL=your-email@example.com
COOKIDOO_PASSWORD=your-password
```

### 5. Test the Integration

#### Test 1: Start MCP Server

```powershell
cd mcp-server
.\venv\Scripts\Activate.ps1
python server.py
```

#### Test 2: Test Authentication

```powershell
# PowerShell
$body = @{
    username = "your-email@example.com"
    password = "your-password"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/auth/login" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

#### Test 3: Search Recipes

```powershell
$searchBody = @{
    query = "pasta"
    limit = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/recipes/search" `
    -Method Post `
    -Body $searchBody `
    -ContentType "application/json"
```

#### Test 4: Run Databricks Notebook

In Databricks, run `databricks/notebooks/00_test_cookidoo_connection.ipynb` to test connection with Key Vault credentials.

### 6. Docker Integration

Update `docker-compose.yml` to pass Cookidoo credentials:

```yaml
services:
  mcp-server:
    build:
      context: .
      dockerfile: docker/mcp.Dockerfile
    ports:
      - "8001:8001"
    environment:
      - COOKIDOO_EMAIL=${COOKIDOO_EMAIL}
      - COOKIDOO_PASSWORD=${COOKIDOO_PASSWORD}
    env_file:
      - mcp-server/.env
```

## Production Considerations

### 1. Security

**DO NOT** hardcode credentials. Use:

- **Azure Key Vault** for secrets
- **Environment variables** for local dev
- **Databricks secrets** for notebooks

**Update backend to use Key Vault:**

```python
from backend.utils.azure_key_vault import get_secret

# In recipe_service.py
cookidoo_email = get_secret("cookidoo-email")
cookidoo_password = get_secret("cookidoo-password")
```

### 2. Session Management

Current implementation uses a global client. For production:

- Use session-based authentication
- Implement token refresh
- Add user-specific client instances

### 3. Error Handling

Add retry logic for API calls:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def get_recipe_with_retry(recipe_id: str):
    return await get_recipe(recipe_id)
```

### 4. Rate Limiting

Cookidoo may have rate limits. Implement:

- Request throttling
- Caching for frequently accessed recipes
- Queue for bulk operations

## Troubleshooting

### Issue: cookidoo-api not found

```powershell
pip install cookidoo-api
```

### Issue: Authentication fails

1. Verify credentials in .env
2. Check Cookidoo account is active
3. Test manually at https://cookidoo.com
4. Check for API changes (community library may need updates)

### Issue: Recipe not found

- Verify recipe ID format
- Check if recipe is accessible with your account
- Some recipes may be region-specific

### Issue: Databricks Key Vault access denied

1. Verify scope exists: `databricks secrets list-scopes`
2. Check secret names: `databricks secrets list --scope cookidoo-secrets`
3. Verify permissions on the scope

## API Reference

### cookidoo-api Methods

Based on https://github.com/miaucl/cookidoo-api:

```python
from cookidoo_api import Cookidoo

client = Cookidoo()

# Authentication
client.login(email, password)

# Get recipe
recipe = client.get_recipe(recipe_id)

# Search recipes
recipes = client.search_recipes(query)

# Create custom recipe
result = client.create_recipe(recipe_data)

# Get collections
collections = client.get_collections()

# Get shopping list
shopping_list = client.get_shopping_list()
```

## Next Steps

1. ✅ Run Databricks test notebook: `00_test_cookidoo_connection.ipynb`
2. ⬜ Update `mcp-server/server.py` with code above
3. ⬜ Update `mcp-server/requirements.txt`
4. ⬜ Test MCP server locally
5. ⬜ Integrate with backend services
6. ⬜ Update Docker configuration
7. ⬜ Deploy with Key Vault credentials

## Resources

- **mcp-cookidoo**: https://github.com/alexandrepa/mcp-cookidoo
- **cookidoo-api**: https://github.com/miaucl/cookidoo-api
- **Test Notebook**: `databricks/notebooks/00_test_cookidoo_connection.ipynb`
- **Implementation Checklist**: `IMPLEMENTATION_CHECKLIST.md`

---

**Last Updated**: March 1, 2026  
**Status**: Test notebook created, integration guide complete
