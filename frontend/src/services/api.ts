/**
 * API client for backend communication
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: `${API_BASE_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000,
});

// Request interceptor
apiClient.interceptors.request.use(
    (config) => {
        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized
            localStorage.removeItem('authToken');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Recipe API
export const recipeApi = {
    getRecipe: (id: string) => apiClient.get(`/recipes/${id}`),
    searchRecipes: (query: string, filters?: any) =>
        apiClient.post('/recipes/search', { query, ...filters }),
    modifyRecipe: (data: any) => apiClient.post('/recipes/modify', data),
    saveRecipe: (recipe: any, saveToCookidoo: boolean = true) =>
        apiClient.post(`/recipes/save?save_to_cookidoo=${saveToCookidoo}`, recipe),
    scaleRecipe: (id: string, servings: number) =>
        apiClient.post(`/recipes/${id}/scale?target_servings=${servings}`),
    getCollections: () => apiClient.get('/recipes/collections'),
    getCreatedRecipes: () => apiClient.get('/recipes/created'),
    getCreatedRecipeDetail: (id: string) => apiClient.get(`/recipes/created/${id}`),
};

// Chat API
export const chatApi = {
    sendMessage: (data: any) => apiClient.post('/chat', data),
    getHistory: (conversationId: string, limit: number = 50) =>
        apiClient.get(`/chat/history/${conversationId}?limit=${limit}`),
    deleteConversation: (conversationId: string) =>
        apiClient.delete(`/chat/history/${conversationId}`),
};

// Shopping List API
export const shoppingApi = {
    generateList: (data: any) => apiClient.post('/shopping-list/generate', data),
    getList: (listId: string) => apiClient.get(`/shopping-list/${listId}`),
    toggleItem: (listId: string, itemIndex: number, checked: boolean) =>
        apiClient.put(`/shopping-list/${listId}/item/${itemIndex}/check?checked=${checked}`),
};

// Health API
export const healthApi = {
    check: () => apiClient.get('/health'),
};

export default apiClient;
