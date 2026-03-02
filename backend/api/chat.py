"""
Chat and Q&A API endpoints for cooking assistance.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from ..models.chat import ChatRequest, ChatResponse
from ..services.chat_service import ChatService
from ..utils.dependencies import get_chat_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat with the cooking assistant AI.
    
    Provides intelligent responses to cooking questions, ingredient substitutions,
    technique explanations, and recipe-specific queries.
    
    Args:
        request: Chat request with message and optional context
        
    Returns:
        ChatResponse: AI response with suggested follow-ups
    """
    try:
        logger.info(f"Processing chat request: {request.message[:100]}...")
        
        response = await chat_service.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            recipe_context=request.recipe_context,
            include_history=request.include_history
        )
        
        logger.info(f"Chat response generated for conversation: {response.conversation_id}")
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid chat request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Retrieve conversation history.
    
    Args:
        conversation_id: ID of the conversation
        limit: Maximum number of messages to return
        
    Returns:
        List of chat messages
    """
    try:
        history = await chat_service.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit
        )
        return {"conversation_id": conversation_id, "messages": history}
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/history/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete a conversation and its history.
    
    Args:
        conversation_id: ID of the conversation to delete
        
    Returns:
        Success message
    """
    try:
        await chat_service.delete_conversation(conversation_id)
        return {"success": True, "message": "Conversation deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
