/**
 * TypeScript interfaces for Shopping List models
 */

export interface ShoppingListItem {
    name: string;
    quantity: number;
    unit: string;
    category: string;
    checked: boolean;
    notes?: string;
    from_recipes?: string[];
}

export interface ShoppingListRequest {
    recipe_ids: string[];
    consolidate_items?: boolean;
    servings_per_recipe?: Record<string, number>;
}

export interface ShoppingListResponse {
    list_id: string;
    items: ShoppingListItem[];
    recipe_count: number;
    created_at: string;
    total_items: number;
}

export interface ShoppingList {
    list_id: string;
    items: ShoppingListItem[];
    recipe_ids: string[];
    created_at: string;
    updated_at: string;
    total_items: number;
    checked_items: number;
}
