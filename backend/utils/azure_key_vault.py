"""
Azure Key Vault integration for secure credential management.
"""

import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from config.settings import get_settings

logger = logging.getLogger(__name__)

_secret_client: Optional[SecretClient] = None


async def init_key_vault(vault_url: str):
    """
    Initialize Azure Key Vault client.
    
    Args:
        vault_url: URL of the Azure Key Vault
    """
    global _secret_client
    
    try:
        credential = DefaultAzureCredential()
        _secret_client = SecretClient(vault_url=vault_url, credential=credential)
        logger.info(f"Azure Key Vault client initialized for {vault_url}")
    except Exception as e:
        logger.error(f"Failed to initialize Key Vault: {str(e)}", exc_info=True)
        raise


def get_secret(secret_name: str) -> str:
    """
    Retrieve a secret from Azure Key Vault.
    
    Args:
        secret_name: Name of the secret to retrieve
        
    Returns:
        str: Secret value
        
    Raises:
        ValueError: If Key Vault client not initialized
        Exception: If secret retrieval fails
    """
    if _secret_client is None:
        raise ValueError("Key Vault client not initialized. Call init_key_vault() first.")
    
    try:
        secret = _secret_client.get_secret(secret_name)
        logger.debug(f"Retrieved secret: {secret_name}")
        return secret.value
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {str(e)}")
        raise


async def get_cookidoo_credentials() -> dict:
    """
    Retrieve Cookidoo API credentials from Key Vault.
    
    Returns:
        dict: Dictionary with 'username' and 'password' keys
    """
    try:
        username = get_secret("cookidoo-username")
        password = get_secret("cookidoo-password")
        
        return {
            "username": username,
            "password": password
        }
    except Exception as e:
        logger.error(f"Failed to retrieve Cookidoo credentials: {str(e)}")
        raise
