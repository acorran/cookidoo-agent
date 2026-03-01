"""
Cookidoo Agent Assistant - Main FastAPI Application

This is the main entry point for the FastAPI backend service.
It handles all API endpoints for recipe modification, Q&A, shopping lists,
and orchestrates communication between the LLM agent, MCP server, and Databricks.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api.recipes import router as recipes_router
from api.chat import router as chat_router
from api.shopping import router as shopping_router
from api.health import router as health_router
from config.settings import get_settings
from utils.logging_config import setup_logging
from utils.azure_key_vault import init_key_vault

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    
    Startup: Initialize connections to Azure Key Vault, Databricks, and MCP server.
    Shutdown: Clean up resources and close connections.
    """
    logger.info("Starting Cookidoo Agent Assistant backend...")
    settings = get_settings()
    
    try:
        # Initialize Azure Key Vault for secure credential management
        await init_key_vault(settings.azure_key_vault_url)
        logger.info("Azure Key Vault initialized successfully")
        
        # TODO: Initialize Databricks connection
        # TODO: Initialize MCP server connection
        # TODO: Initialize AgentBricks LLM orchestration
        
        logger.info("Backend startup complete")
        
        yield  # Application runs here
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Cookidoo Agent Assistant backend...")
        # TODO: Close Databricks connection
        # TODO: Close MCP server connection
        logger.info("Backend shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Cookidoo Agent Assistant API",
    description="AI-powered recipe modification, cooking assistance, and meal planning platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend access
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions gracefully."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

# Include API routers
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(recipes_router, prefix="/api/v1", tags=["Recipes"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(shopping_router, prefix="/api/v1", tags=["Shopping"])

@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "service": "Cookidoo Agent Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    # Run the application (for local development)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
