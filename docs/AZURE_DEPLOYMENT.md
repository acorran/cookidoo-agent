# Azure Deployment Guide (azd)

Deploy the entire Cookidoo Agent Assistant to Azure with a single command using the Azure Developer CLI.

## What Gets Deployed

| Resource                       | Purpose                                 | SKU/Tier      |
| ------------------------------ | --------------------------------------- | ------------- |
| **Resource Group**             | Container for all resources             | —             |
| **Virtual Network**            | Private networking (10.0.0.0/16)        | —             |
| **Container Registry**         | Docker image storage                    | Basic         |
| **Key Vault**                  | Secrets (Cookidoo credentials)          | Standard      |
| **Container Apps Environment** | Internal-only hosting                   | Consumption   |
| **Container App: mcp-server**  | REST (8001) + MCP SSE (8002)            | Internal only |
| **Container App: backend**     | FastAPI API (8000)                      | External      |
| **Container App: frontend**    | React UI (3000)                         | External      |
| **Private DNS Zone**           | VNet name resolution for Container Apps | —             |
| **Log Analytics**              | Diagnostics and logging                 | PerGB2018     |
| **Databricks** *(optional)*    | AI notebooks, Unity Catalog, agents     | Premium       |

**Estimated cost**: ~£5-10/day without Databricks, ~£30-50/day with Databricks Premium.

---

## Prerequisites

### 1. Azure Developer CLI (azd)

```powershell
# Install via winget (recommended)
winget install Microsoft.Azd

# Or via PowerShell
powershell -ex AllSigned -c "Invoke-RestMethod 'https://aka.ms/install-azd.ps1' | Invoke-Expression"

# Verify
azd version
```

### 2. Azure CLI

```powershell
# Install via winget
winget install Microsoft.AzureCLI

# Verify
az --version
```

### 3. Docker Desktop

Required for building container images locally before pushing to ACR.

```powershell
# Check if installed
docker --version

# If not installed, download from https://www.docker.com/products/docker-desktop
# Or: winget install Docker.DockerDesktop
```

### 4. Azure Subscription

You need an active Azure subscription. If you don't have one:
- [Azure Free Account](https://azure.microsoft.com/free/) — includes £150 credit for 30 days
- [Azure for Students](https://azure.microsoft.com/free/students/) — £75 credit, no credit card required

### 5. Cookidoo Account

You need a valid [Cookidoo](https://cookidoo.co.uk) account (email + password) for recipe access.

---

## Deployment Steps

### Step 1: Authenticate

```powershell
# Login to Azure (opens browser)
azd auth login

# Also login to Azure CLI (needed for Docker push)
az login
```

### Step 2: Initialise Environment

```powershell
# From the project root directory
cd c:\Users\andycorran\source\repos\cookidoo-agent

# Create a named environment (e.g. "dev", "staging", "prod")
azd env new dev
```

You'll be prompted to select:
- **Azure Subscription** — pick yours from the list
- **Azure Location** — choose a region (e.g. `uksouth`, `westeurope`, `eastus`)

### Step 3: Set Cookidoo Credentials

```powershell
azd env set COOKIDOO_EMAIL "your-cookidoo-email@example.com"
azd env set COOKIDOO_PASSWORD "your-cookidoo-password"
```

### Step 4: (Optional) Skip Databricks

Databricks Premium costs ~£25-40/day. To skip it during development:

```powershell
azd env set DEPLOY_DATABRICKS false
```

### Step 5: Deploy Everything

```powershell
azd up
```

This single command will:
1. **Provision infrastructure** — creates all Azure resources via Bicep
2. **Build Docker images** — builds backend, frontend, and mcp-server containers
3. **Push images** — uploads to Azure Container Registry
4. **Deploy containers** — starts all three Container Apps

First deployment takes **10-15 minutes**. Subsequent deployments are faster.

### Step 6: Verify

After `azd up` completes, it prints the service URLs:

```
Deploying services (azd deploy)

  (✓) Done: Service backend
  - Endpoint: https://ca-backend.<id>.uksouth.azurecontainerapps.io

  (✓) Done: Service frontend
  - Endpoint: https://ca-frontend.<id>.uksouth.azurecontainerapps.io

  (✓) Done: Service mcp-server
  - Endpoint: https://ca-mcp-server.internal.<id>.uksouth.azurecontainerapps.io
```

- **Frontend**: Open the frontend URL in your browser
- **Backend API docs**: Append `/docs` to the backend URL
- **MCP Server**: Internal only (no public URL) — accessible from Databricks via VNet

---

## Common Commands

```powershell
# Deploy only code changes (skip infra provisioning)
azd deploy

# Re-provision infrastructure only
azd provision

# Deploy a single service
azd deploy --service backend

# View current environment settings
azd env get-values

# Switch between environments
azd env select staging

# View deployed resources in Azure Portal
azd show

# Tear down everything (deletes all resources)
azd down
```

---

## Updating Credentials

```powershell
# Update Cookidoo credentials
azd env set COOKIDOO_EMAIL "new-email@example.com"
azd env set COOKIDOO_PASSWORD "new-password"

# Re-deploy to apply
azd up
```

---

## Troubleshooting

### "azd" command not found
Restart your terminal after installing azd, or add it to your PATH manually.

### Docker build fails
Ensure Docker Desktop is running: look for the whale icon in the system tray.

### Subscription permission errors
You need **Contributor** role on the Azure subscription. Check with:
```powershell
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --query "[].roleDefinitionName" -o tsv
```

### Databricks VNet injection fails
Databricks VNet injection requires the `Microsoft.Databricks` resource provider to be registered:
```powershell
az provider register --namespace Microsoft.Databricks
az provider show --namespace Microsoft.Databricks --query "registrationState"
```

### Container Apps fail to start
Check logs:
```powershell
az containerapp logs show --name ca-backend --resource-group rg-dev --type console
az containerapp logs show --name ca-mcp-server --resource-group rg-dev --type console
```

### Tear down and start fresh
```powershell
azd down --force --purge
azd up
```

---

## Architecture Diagram

```
                    ┌─────────────────────────────────────────────────┐
                    │              Azure Resource Group               │
                    │                                                 │
  Internet ────────┤  ┌──────────┐    ┌──────────┐                   │
                    │  │ Frontend │    │ Backend  │                   │
                    │  │ (React)  │    │ (FastAPI)│                   │
                    │  │ :3000    │    │ :8000    │                   │
                    │  └──────────┘    └────┬─────┘                   │
                    │       External        │ VNet                    │
                    │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─    │
                    │       Internal        │                         │
                    │                  ┌────▼──────┐                  │
                    │                  │MCP Server │                  │
                    │                  │:8001 :8002│                  │
                    │                  └───────────┘                  │
                    │  Container Apps Environment (VNet-integrated)   │
                    │                       │                         │
                    │           Private DNS │ Zone                    │
                    │                       │                         │
                    │  ┌────────────────────▼──────────────────────┐  │
                    │  │         Azure Databricks (Premium)        │  │
                    │  │    VNet-injected workers → MCP Server     │  │
                    │  └──────────────────────────────────────────┘  │
                    │                                                 │
                    │  ┌──────────┐  ┌───────────┐  ┌─────────────┐  │
                    │  │Key Vault │  │    ACR     │  │Log Analytics│  │
                    │  └──────────┘  └───────────┘  └─────────────┘  │
                    └─────────────────────────────────────────────────┘
```

---

## What's Next

After deployment:

1. **Test the frontend** — open the frontend URL and explore
2. **Test the API** — open `{backend-url}/docs` for the Swagger UI
3. **Set up Databricks** (if deployed) — run the notebooks in `databricks/notebooks/` in order:
   - `00_test_cookidoo_connection.ipynb` — verify MCP connectivity
   - `01_setup_catalog_and_schemas.ipynb` — create Unity Catalog objects
   - `02_dlt_pipeline.ipynb` — set up Delta Live Tables
   - `03_mcp_client_integration.ipynb` — test MCP client from Databricks
   - `04_uc_functions_mcp_tools.ipynb` — register tools in Unity Catalog
   - `05_mcp_sync_recipes.ipynb` — schedule recipe sync job
4. **Set up CI/CD** — run `azd pipeline config` to create a GitHub Actions workflow
