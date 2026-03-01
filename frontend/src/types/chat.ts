/**
 * TypeScript interfaces for Chat models
 */

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
}

export interface ChatRequest {
    message: string;
    conversation_id?: string;
    context?: {
        recipe_id?: string;
        current_recipe?: any;
        user_preferences?: any;
    };
}

export interface ChatResponse {
    response: string;
    conversation_id: string;
    message_id: string;
    sources?: string[];
    suggested_actions?: SuggestedAction[];
    confidence_score?: number;
}

export interface SuggestedAction {
    action_type: string;
    description: string;
    parameters?: Record<string, any>;
}

export interface ConversationHistory {
    conversation_id: string;
    messages: ChatMessage[];
    created_at: string;
    updated_at: string;
}
