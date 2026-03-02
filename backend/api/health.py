"""
Health check and monitoring endpoints.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Health status and timestamp
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "cookidoo-agent-backend"
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    
    Checks if all dependencies are available and the service is ready to handle requests.
    """
    try:
        # TODO: Check Databricks connection
        # TODO: Check MCP server connection
        # TODO: Check Azure Key Vault access
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dependencies": {
                    "databricks": "connected",
                    "mcp_server": "connected",
                    "key_vault": "accessible"
                }
            }
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e)
            }
        )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.
    
    Simple check to verify the service is still running.
    """
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
