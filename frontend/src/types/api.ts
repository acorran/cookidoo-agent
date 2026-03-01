/**
 * TypeScript interfaces for API responses
 */

export interface ApiResponse<T = any> {
    data?: T;
    error?: ApiError;
    success: boolean;
    timestamp?: string;
}

export interface ApiError {
    code: string;
    message: string;
    details?: any;
    status_code?: number;
}

export interface HealthCheck {
    status: string;
    version: string;
    timestamp: string;
    checks: {
        database: string;
        mcp_server: string;
        llm_service: string;
    };
}
