/**
 * TypeScript interfaces for Recipe models
 */

export interface Ingredient {
    name: string;
    quantity: number;
    unit: string;
    notes?: string;
}

export interface CookingStep {
    step_number: number;
    instruction: string;
    duration_minutes?: number;
    temperature?: string;
}

export interface Recipe {
    id: string;
    title: string;
    description: string;
    servings: number;
    prep_time_minutes: number;
    cook_time_minutes: number;
    total_time_minutes: number;
    difficulty: 'easy' | 'medium' | 'hard';
    cuisine?: string;
    meal_type?: string;
    dietary_restrictions: string[];
    ingredients: Ingredient[];
    cooking_steps: CookingStep[];
    nutritional_info?: NutritionalInfo;
    source?: string;
    image_url?: string;
    tags?: string[];
    created_at?: string;
    updated_at?: string;
}

export interface NutritionalInfo {
    calories: number;
    protein_g?: number;
    carbs_g?: number;
    fat_g?: number;
    fiber_g?: number;
    sugar_g?: number;
    sodium_mg?: number;
}

export interface RecipeModificationRequest {
    recipe_id?: string;
    original_recipe?: Recipe;
    modifications: string;
    preserve_cooking_method?: boolean;
    target_servings?: number;
}

export interface RecipeModificationResponse {
    original_recipe: Recipe;
    modified_recipe: Recipe;
    explanation: string;
    changes_made: string[];
    conversation_id: string;
}

export interface RecipeSearchRequest {
    query: string;
    filters?: {
        dietary_restrictions?: string[];
        max_prep_time_minutes?: number;
        difficulty?: string;
        cuisine?: string;
        meal_type?: string;
    };
    limit?: number;
}

export interface RecipeSearchResponse {
    recipes: Recipe[];
    total_count: number;
    query: string;
}
