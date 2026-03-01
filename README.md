# Cookidoo Agent Assistant

An AI-powered platform that enhances the Cookidoo cooking experience by enabling recipe customization, intelligent cooking assistance, and automated shopping list generation.

## 🎉 Project Status: Core Infrastructure Complete!

All foundational components have been created and are ready for deployment and feature implementation.

📖 **See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for complete project structure and detailed setup guide.**

## ⚠️ Prerequisites

**Before starting**, ensure you have installed:
- Python 3.11+
- Node.js 16+ (includes npm)
- Docker Desktop

📋 **[PREREQUISITES.md](PREREQUISITES.md)** - Complete installation guide for Windows

## 🚀 Quick Start

### Deploy to Azure (Recommended)

Deploy everything to Azure with a single command using [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/):

```powershell
# Install azd (one-time)
winget install Microsoft.Azd

# Authenticate
azd auth login

# Set Cookidoo credentials
azd env new dev
azd env set COOKIDOO_EMAIL "your@email.com"
azd env set COOKIDOO_PASSWORD "yourpassword"

# Deploy everything (infra + build + deploy)
azd up
```

📖 **[docs/AZURE_DEPLOYMENT.md](docs/AZURE_DEPLOYMENT.md)** - Full deployment guide with prerequisites, architecture, and troubleshooting

### Local Docker Setup

```powershell
# Build and start all services
docker-compose up --build

# Access the application
# Frontend:   http://localhost:3000
# Backend:    http://localhost:8000/docs
# MCP Server: http://localhost:8001 (REST) + :8002 (MCP SSE)
```

### Automated Local Setup

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
cp .env.example .env
npm start

# MCP Server (new terminal)
cd mcp-server
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

## Overview

The Cookidoo Agent Assistant addresses the limitations of the Cookidoo platform by providing users with the ability to:
- Modify and personalize existing recipes
- Generate new recipe variations based on dietary needs and preferences
- Save customized recipes to "My Cookidoo Recipes"
- Get intelligent answers about cooking techniques and ingredients
- Generate automated shopping lists from selected recipes

## Features

### 🍳 Recipe Modification
- Adapt recipes to dietary restrictions (gluten-free, vegan, etc.)
- Adjust serving sizes automatically
- Substitute ingredients with intelligent recommendations
- Save personalized variations to your Cookidoo account

### 🤖 Intelligent Cooking Assistant
- Ask questions about ingredients and cooking techniques
- Get recipe recommendations based on preferences
- Receive cooking tips and best practices
- Learn about ingredient substitutions

### 🛒 Smart Shopping Lists
- Generate consolidated shopping lists from multiple recipes
- Organize ingredients by category for efficient shopping
- Automatically calculate quantities for adjusted serving sizes
- Export lists in various formats

### 📊 Data Analytics
- Track your cooking patterns and preferences
- Analyze recipe modifications and trends
- Visualize user interactions through Databricks notebooks
- Continuous improvement through usage insights

## Architecture

```
┌─────────────────┐
│   React Web UI │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI/Flask  │
│   Backend API   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AgentBricks    │
│  LLM Agent      │
└────┬────────────┘
     │
     ├──────────────┐
     │              │
     ▼              ▼
┌─────────┐   ┌──────────────┐
│   MCP   │   │  Databricks  │
│ Server  │   │ Delta Tables │
└────┬────┘   └──────────────┘
     │
     ▼
┌─────────────────┐
│  Cookidoo API   │
└─────────────────┘
```

## Tech Stack

### Frontend
- **Framework**: React
- **UI Components**: Modern React component library
- **State Management**: React Context / Redux

### Backend
- **Framework**: FastAPI or Flask
- **LLM Orchestration**: AgentBricks
- **API Integration**: MCP (Model Context Protocol) Server
- **Language**: Python 3.9+

### Data & Analytics
- **Platform**: Databricks
- **Storage**: Delta Live Tables (DLT)
- **Notebooks**: Interactive data exploration and visualization

### Infrastructure
- **Containerization**: Docker
- **Cloud Platform**: Microsoft Azure
- **Deployment**: Azure Container Apps
- **Secrets Management**: Azure Key Vault

### Security
- **Credential Storage**: Azure Key Vault
- **Authentication**: Token-based auth
- **HTTPS/TLS**: Secure data transmission

## Prerequisites

- Python 3.9 or higher
- Node.js 16+ and npm/yarn
- Docker and Docker Compose
- Azure account with Key Vault access
- Databricks workspace
- Cookidoo account credentials

## Getting Started

### 1. Clone the Repository

```powershell
git clone https://github.com/yourusername/cookidoo-agent.git
cd cookidoo-agent
```

### 2. Set Up Python Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Azure Key Vault
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# Cookidoo Credentials (stored in Key Vault)
COOKIDOO_USERNAME=your-username
COOKIDOO_PASSWORD=your-password

# LLM Configuration
LLM_MODEL=gpt-4
LLM_API_KEY=your-api-key

# Databricks
DATABRICKS_HOST=https://your-databricks-instance.cloud.databricks.com
DATABRICKS_TOKEN=your-databricks-token

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
```

### 4. Set Up Azure Key Vault

Store sensitive credentials in Azure Key Vault:

```powershell
# Login to Azure
az login

# Create Key Vault (if not exists)
az keyvault create --name cookidoo-agent-kv --resource-group your-rg --location eastus

# Store secrets
az keyvault secret set --vault-name cookidoo-agent-kv --name "cookidoo-username" --value "your-username"
az keyvault secret set --vault-name cookidoo-agent-kv --name "cookidoo-password" --value "your-password"
az keyvault secret set --vault-name cookidoo-agent-kv --name "llm-api-key" --value "your-api-key"
```

### 5. Initialize Databricks

```powershell
# Run setup scripts
python scripts/setup_databricks.py

# Deploy DLT pipelines
python scripts/deploy_dlt.py
```

### 6. Run the Application

#### Option A: Local Development

```powershell
# Start backend
cd backend
uvicorn main:app --reload --port 8000

# In a new terminal, start frontend
cd frontend
npm install
npm start
```

#### Option B: Docker Compose

```powershell
# Build and run all services
docker-compose up --build
```

Access the application at `http://localhost:3000`

## Project Structure

```
cookidoo-agent/
├── backend/                 # FastAPI/Flask backend
│   ├── api/                # API endpoints
│   ├── agents/             # AgentBricks LLM agents
│   ├── services/           # Business logic services
│   ├── models/             # Data models
│   ├── utils/              # Utility functions
│   └── main.py             # Application entry point
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service clients
│   │   └── utils/         # Frontend utilities
│   └── public/
├── mcp-server/            # Model Context Protocol server
│   ├── cookidoo/          # Cookidoo API integration
│   └── server.py          # MCP server implementation
├── databricks/            # Databricks notebooks and configs
│   ├── notebooks/         # Analysis notebooks
│   ├── dlt/               # Delta Live Tables pipelines
│   └── scripts/           # Setup and utility scripts
├── docker/                # Docker configurations
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── mcp.Dockerfile
├── tests/                 # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                  # Documentation
│   ├── api/              # API documentation
│   ├── deployment/       # Deployment guides
│   └── architecture/     # Architecture diagrams
├── scripts/              # Utility scripts
├── .env.example          # Example environment variables
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Python dependencies
├── PRD.md               # Product Requirements Document
└── README.md            # This file
```

## Development

### Running Tests

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test suite
pytest tests/unit
pytest tests/integration
```

### Code Quality

```powershell
# Format code
black backend/ tests/

# Lint code
flake8 backend/ tests/

# Type checking
mypy backend/
```

### Pre-commit Hooks

```powershell
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

- `POST /api/v1/recipes/modify` - Modify an existing recipe
- `POST /api/v1/recipes/generate` - Generate a new recipe variation
- `POST /api/v1/recipes/save` - Save recipe to Cookidoo
- `GET /api/v1/recipes/{id}` - Retrieve recipe details
- `POST /api/v1/chat` - Chat with the cooking assistant
- `POST /api/v1/shopping-list` - Generate shopping list

## Deployment

### Docker Build

```powershell
# Build all images
docker-compose build

# Build specific service
docker build -f docker/backend.Dockerfile -t cookidoo-agent-backend .
```

### Azure Container Apps Deployment

```powershell
# Login to Azure
az login

# Create resource group
az group create --name cookidoo-agent-rg --location eastus

# Create container app environment
az containerapp env create --name cookidoo-agent-env --resource-group cookidoo-agent-rg --location eastus

# Deploy backend
az containerapp create \
  --name cookidoo-backend \
  --resource-group cookidoo-agent-rg \
  --environment cookidoo-agent-env \
  --image your-registry.azurecr.io/cookidoo-backend:latest \
  --target-port 8000 \
  --ingress external

# Deploy frontend
az containerapp create \
  --name cookidoo-frontend \
  --resource-group cookidoo-agent-rg \
  --environment cookidoo-agent-env \
  --image your-registry.azurecr.io/cookidoo-frontend:latest \
  --target-port 3000 \
  --ingress external
```

## Configuration

### LLM Model Configuration

Edit `backend/config/llm_config.yaml`:

```yaml
llm:
  model: gpt-4
  temperature: 0.7
  max_tokens: 2000
  system_prompt: |
    You are an expert cooking assistant with deep knowledge of recipes,
    ingredients, and cooking techniques.
```

### Databricks Configuration

Edit `databricks/config/dlt_config.json`:

```json
{
  "name": "cookidoo-agent-pipeline",
  "storage": "/mnt/cookidoo-agent",
  "target": "cookidoo_prod",
  "continuous": false
}
```

## Monitoring & Logging

### Application Logs

Logs are stored in structured format:

```powershell
# View logs (Docker)
docker-compose logs -f backend

# View logs (Azure)
az containerapp logs show --name cookidoo-backend --resource-group cookidoo-agent-rg --follow
```

### Databricks Dashboards

Access analytics dashboards in Databricks workspace:
- Recipe modification trends
- User interaction patterns
- Agent performance metrics
- Error rates and diagnostics

## Troubleshooting

### Common Issues

#### Cookidoo API Authentication Fails
```powershell
# Verify credentials in Key Vault
az keyvault secret show --vault-name cookidoo-agent-kv --name "cookidoo-username"

# Test MCP server connection
python scripts/test_cookidoo_connection.py
```

#### LLM Agent Not Responding
```powershell
# Check LLM API key
az keyvault secret show --vault-name cookidoo-agent-kv --name "llm-api-key"

# Review agent logs
docker-compose logs backend | grep "agent"
```

#### Databricks Connection Issues
```powershell
# Verify Databricks token
python scripts/test_databricks_connection.py

# Check network connectivity
Test-NetConnection your-databricks-instance.cloud.databricks.com -Port 443
```

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow PEP 8 coding standards
4. Write tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Review Process

- All PRs require at least one approval
- All tests must pass
- Code coverage should not decrease
- Follow the project's coding guidelines

## Security

### Reporting Security Issues

Please report security vulnerabilities to security@example.com

### Security Best Practices

- Never commit credentials or API keys
- Use Azure Key Vault for all secrets
- Regularly update dependencies
- Follow OWASP security guidelines
- Enable Azure Security Center recommendations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/cookidoo-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cookidoo-agent/discussions)

## Acknowledgments

- Cookidoo API open-source community
- AgentBricks framework contributors
- Databricks team for platform support
- Azure team for cloud infrastructure

## Roadmap

### Q1 2026
- [ ] Mobile app development (iOS/Android)
- [ ] Voice interface integration
- [ ] Multi-language support
- [ ] Enhanced recipe recommendation engine

### Q2 2026
- [ ] Meal planning calendar
- [ ] Nutritional analysis integration
- [ ] Social sharing features
- [ ] Recipe rating and reviews

### Q3 2026
- [ ] Integration with other recipe platforms
- [ ] Advanced AI training with user feedback
- [ ] Grocery delivery service integration
- [ ] Kitchen inventory management

---

**Built with ❤️ for the cooking community**
