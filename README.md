# Cookidoo Agent Assistant

An AI-powered platform that enhances the Cookidoo cooking experience by enabling recipe customization, intelligent cooking assistance, and automated shopping list generation — built with Databricks, MCP, and Azure.

## Project Status: Core Infrastructure Complete

All foundational components have been created and are ready for deployment and feature implementation.

- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** — Complete project structure and detailed setup guide
- **[docs/PRD.md](docs/PRD.md)** — Product Requirements Document

## Prerequisites

Before starting, ensure you have installed:

- **Python 3.11+**
- **Node.js 16+** (includes npm)
- **Docker Desktop**
- **Azure Developer CLI (`azd`)** — for cloud deployment

See **[PREREQUISITES.md](PREREQUISITES.md)** for the complete installation guide on Windows.

## Quick Start

### Deploy to Azure (Recommended)

Deploy everything to Azure with a single command using [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/):

```powershell
# Install azd (one-time)
winget install Microsoft.Azd

# Clone and enter the project
git clone https://github.com/acorran/cookidoo-agent.git
cd cookidoo-agent

# Authenticate
azd auth login

# Set Cookidoo credentials
azd env new dev
azd env set COOKIDOO_EMAIL "your@email.com"
azd env set COOKIDOO_PASSWORD "yourpassword"

# Deploy everything (infra + build + deploy)
azd up
```

See **[docs/AZURE_DEPLOYMENT.md](docs/AZURE_DEPLOYMENT.md)** for the full guide with architecture, prerequisites, and troubleshooting.

### Local Docker Setup

```powershell
# Build and start all services
docker-compose up --build

# Access the application
# Frontend:   http://localhost:3000
# Backend:    http://localhost:8000/docs
# MCP Server: http://localhost:8001 (REST) + :8002 (MCP SSE)
```

### Manual Local Setup

```powershell
# Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env  # Edit with your config
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm start

# MCP Server (new terminal)
cd mcp-server
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

## Features

### Recipe Modification
- Adapt recipes to dietary restrictions (gluten-free, vegan, etc.)
- Adjust serving sizes automatically
- Substitute ingredients with intelligent recommendations
- Save personalised variations to your Cookidoo account

### Intelligent Cooking Assistant
- Ask questions about ingredients and cooking techniques
- Get recipe recommendations based on preferences
- Receive cooking tips and best practices
- Learn about ingredient substitutions

### Smart Shopping Lists
- Generate consolidated shopping lists from multiple recipes
- Organise ingredients by category for efficient shopping
- Automatically calculate quantities for adjusted serving sizes

### Data Analytics (Databricks)
- Track cooking patterns and preferences
- Analyse recipe modifications and trends
- Visualise user interactions through Databricks notebooks
- Continuous improvement through usage insights

## Architecture

```
┌─────────────────┐
│   React Web UI  │  (frontend/)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    FastAPI       │  (backend/)
│   Backend API   │
└────────┬────────┘
         │
    ┌────┴────────────┐
    │                 │
    ▼                 ▼
┌─────────┐   ┌──────────────┐
│   MCP   │   │  Databricks  │
│ Server  │   │ Unity Catalog│
│(mcp-    │   │ Delta Tables │
│ server/)│   │ AI Agents    │
└────┬────┘   └──────────────┘
     │
     ▼
┌─────────────────┐
│  Cookidoo API   │
│ (cookidoo-api)  │
└─────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React, TypeScript |
| **Backend** | FastAPI, Python 3.11+ |
| **MCP Server** | FastMCP, cookidoo-api |
| **LLM** | Claude Sonnet 4.5 (via Databricks Model Serving) |
| **Data Platform** | Databricks Unity Catalog, Delta Live Tables |
| **AI Agents** | Databricks Mosaic AI Agent Framework, UC Functions |
| **Infrastructure** | Azure Container Apps, Bicep (IaC) |
| **Secrets** | Azure Key Vault |
| **Containerisation** | Docker, Docker Compose |
| **Deployment** | Azure Developer CLI (`azd up`) |

## Project Structure

```
cookidoo-agent/
├── azure.yaml                    # azd deployment configuration
├── docker-compose.yml            # Local multi-container setup
├── setup.ps1                     # Automated local setup script
├── verify-prerequisites.ps1      # Check all tools are installed
│
├── backend/                      # FastAPI backend
│   ├── main.py                   # Application entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/                      # API route handlers
│   │   ├── chat.py
│   │   ├── health.py
│   │   ├── recipes.py
│   │   └── shopping.py
│   ├── config/                   # Settings & configuration
│   │   └── settings.py
│   ├── models/                   # Pydantic data models
│   ├── services/                 # Business logic
│   │   ├── chat_service.py
│   │   ├── recipe_service.py
│   │   └── shopping_service.py
│   └── utils/                    # Helpers (Key Vault, logging)
│       ├── azure_key_vault.py
│       ├── dependencies.py
│       └── logging_config.py
│
├── frontend/                     # React frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── public/
│   └── src/
│       ├── App.tsx
│       ├── components/           # Layout, shared components
│       ├── pages/                # Chat, Recipes, Shopping, Home
│       ├── services/api.ts       # Backend API client
│       └── types/                # TypeScript interfaces
│
├── mcp-server/                   # Model Context Protocol server
│   ├── server.py                 # MCP server (REST + SSE)
│   ├── mcp_tools.py              # Cookidoo tool definitions
│   ├── requirements.txt
│   └── .env.template
│
├── databricks/                   # Databricks notebooks & scripts
│   ├── notebooks/                # Jupyter notebooks (.ipynb)
│   │   ├── 00_test_cookidoo_connection.ipynb
│   │   ├── 01_setup_catalog_and_schemas.ipynb
│   │   ├── 02_dlt_pipeline.ipynb
│   │   ├── 03_mcp_client_integration.ipynb
│   │   ├── 04_uc_functions_mcp_tools.ipynb
│   │   └── 05_mcp_sync_recipes.ipynb
│   └── scripts/                  # Automation scripts
│       ├── deploy_infrastructure.py
│       ├── deploy_mcp_sync_job.py
│       └── generate_sample_data.py
│
├── infra/                        # Azure infrastructure (Bicep)
│   ├── main.bicep                # Main template
│   ├── main.parameters.json
│   └── modules/                  # Container Apps, ACR, Key Vault, etc.
│
├── docker/                       # Dockerfiles & nginx config
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── mcp.Dockerfile
│   └── nginx.conf
│
├── tests/                        # Test suites
│   ├── conftest.py
│   ├── requirements.txt
│   ├── test_api_endpoints.py
│   └── test_recipe_service.py
│
├── docs/                         # Documentation
│   ├── PRD.md                    # Product Requirements Document
│   ├── AZURE_DEPLOYMENT.md       # Azure deployment guide
│   ├── DATABRICKS_DEPLOYMENT.md  # Databricks setup guide
│   └── COOKIDOO_MCP_INTEGRATION.md
│
└── scripts/                      # Deployment scripts
    └── deploy_azure_infrastructure.py
```

## Databricks Setup

The project includes 6 Jupyter notebooks for Databricks, run them in order:

1. **`00_test_cookidoo_connection`** — Verify Cookidoo API credentials via Key Vault
2. **`01_setup_catalog_and_schemas`** — Create Unity Catalog, schemas, and tables
3. **`02_dlt_pipeline`** — Delta Live Tables: Bronze → Silver → Gold
4. **`03_mcp_client_integration`** — Connect to MCP server (REST + SSE patterns)
5. **`04_uc_functions_mcp_tools`** — Register UC Functions as AI agent tools
6. **`05_mcp_sync_recipes`** — Scheduled recipe sync job

See **[docs/DATABRICKS_DEPLOYMENT.md](docs/DATABRICKS_DEPLOYMENT.md)** for the complete guide.

## API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Chat with the cooking assistant |
| `GET` | `/api/recipes/search` | Search recipes |
| `GET` | `/api/recipes/{id}` | Get recipe details |
| `POST` | `/api/recipes/modify` | Modify an existing recipe |
| `POST` | `/api/recipes/save` | Save recipe to Cookidoo |
| `POST` | `/api/shopping-list` | Generate shopping list |

## Running Tests

```powershell
cd tests
pip install -r requirements.txt
pytest -v --cov=backend
```

## Development

```powershell
# Format code
black backend/ tests/

# Lint code
flake8 backend/ tests/

# Type checking
mypy backend/
```

## Environment Variables

The backend uses pydantic-settings. Create `backend/.env` from `backend/.env.example`:

```env
# Azure Key Vault
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# MCP Server
MCP_SERVER_URL=http://localhost:8001
MCP_SSE_URL=http://localhost:8002

# LLM Configuration
LLM_MODEL=claude-sonnet-4-5-20250514
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Databricks (optional, for direct integration)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token
```

Sensitive credentials (Cookidoo email/password, API keys) should be stored in **Azure Key Vault**, not in `.env` files. See [docs/AZURE_DEPLOYMENT.md](docs/AZURE_DEPLOYMENT.md) for Key Vault setup.

## Deployment

### Azure (Production)

```powershell
azd up       # Provision + build + deploy
azd deploy   # Redeploy code only (after infra is up)
azd down     # Tear down all resources
```

See **[docs/AZURE_DEPLOYMENT.md](docs/AZURE_DEPLOYMENT.md)** for the complete guide.

### Docker (Local)

```powershell
docker-compose up --build        # Start all services
docker-compose down              # Stop all services
docker-compose logs -f backend   # View backend logs
```

## Monitoring & Logging

- **Application logs**: Structured JSON logging via Python `logging` module
- **Azure**: `az containerapp logs show --name cookidoo-backend --resource-group <rg> --follow`
- **Docker**: `docker-compose logs -f backend`
- **Databricks**: Analytics dashboards via notebooks in `databricks/notebooks/`

## Documentation

| Document | Description |
|----------|-------------|
| [PREREQUISITES.md](PREREQUISITES.md) | Tool installation guide |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project overview and setup |
| [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) | Feature implementation tracker |
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document |
| [docs/AZURE_DEPLOYMENT.md](docs/AZURE_DEPLOYMENT.md) | Azure deployment guide |
| [docs/DATABRICKS_DEPLOYMENT.md](docs/DATABRICKS_DEPLOYMENT.md) | Databricks setup guide |
| [docs/COOKIDOO_MCP_INTEGRATION.md](docs/COOKIDOO_MCP_INTEGRATION.md) | MCP + Cookidoo API integration |

## Security

- Never commit credentials or API keys — all secrets go in Azure Key Vault
- `.gitignore` is configured to exclude `.env`, credentials, and secret files
- HTTPS/TLS enforced in Azure Container Apps
- Databricks secrets scopes backed by Azure Key Vault

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow PEP 8 coding standards
4. Write tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Links

- **Repository**: [github.com/acorran/cookidoo-agent](https://github.com/acorran/cookidoo-agent)
- **Issues**: [github.com/acorran/cookidoo-agent/issues](https://github.com/acorran/cookidoo-agent/issues)
- **cookidoo-api**: [github.com/miaucl/cookidoo-api](https://github.com/miaucl/cookidoo-api)
- **mcp-cookidoo**: [github.com/alexandrepa/mcp-cookidoo](https://github.com/alexandrepa/mcp-cookidoo)

---

**Built with Azure, Databricks, and MCP for the cooking community**
