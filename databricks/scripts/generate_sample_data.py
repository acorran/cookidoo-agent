"""
Script to generate sample recipe data for testing the Cookidoo Agent Assistant.

This creates synthetic recipe data that matches the schema used in the application.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
import uuid


class RecipeGenerator:
    """Generate synthetic recipe data for testing."""
    
    CUISINES = ["Italian", "Mexican", "Asian", "Mediterranean", "American", "French", "Indian"]
    MEAL_TYPES = ["breakfast", "lunch", "dinner", "dessert", "snack", "appetizer"]
    DIFFICULTIES = ["easy", "medium", "hard"]
    DIETARY_RESTRICTIONS = ["vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free"]
    
    SAMPLE_INGREDIENTS = [
        "flour", "sugar", "eggs", "butter", "milk", "salt", "pepper",
        "olive oil", "garlic", "onion", "tomatoes", "chicken", "beef",
        "rice", "pasta", "cheese", "basil", "oregano", "cumin"
    ]
    
    UNITS = ["cup", "tbsp", "tsp", "oz", "lb", "g", "kg", "ml", "l", "piece"]
    
    def generate_recipe(self, recipe_id: str = None) -> Dict:
        """Generate a single recipe."""
        if not recipe_id:
            recipe_id = f"recipe-{uuid.uuid4().hex[:12]}"
        
        cuisine = random.choice(self.CUISINES)
        meal_type = random.choice(self.MEAL_TYPES)
        difficulty = random.choice(self.DIFFICULTIES)
        servings = random.choice([2, 4, 6, 8])
        
        # Generate ingredients
        num_ingredients = random.randint(5, 12)
        ingredients = [
            {
                "name": random.choice(self.SAMPLE_INGREDIENTS),
                "quantity": round(random.uniform(0.25, 4), 2),
                "unit": random.choice(self.UNITS),
                "notes": ""
            }
            for _ in range(num_ingredients)
        ]
        
        # Generate cooking steps
        num_steps = random.randint(4, 8)
        cooking_steps = [
            {
                "step_number": i + 1,
                "instruction": f"Step {i + 1}: Prepare ingredients and follow cooking method.",
                "duration_minutes": random.randint(5, 30) if random.random() > 0.5 else None,
                "temperature": f"{random.choice([325, 350, 375, 400, 425])}°F" if random.random() > 0.7 else None
            }
            for i in range(num_steps)
        ]
        
        prep_time = random.randint(10, 60)
        cook_time = random.randint(15, 120)
        total_time = prep_time + cook_time
        
        # Generate dietary restrictions
        num_restrictions = random.randint(0, 2)
        dietary_restrictions = random.sample(self.DIETARY_RESTRICTIONS, num_restrictions)
        
        recipe = {
            "recipe_id": recipe_id,
            "title": f"{cuisine} {meal_type.capitalize()}",
            "description": f"A delicious {cuisine.lower()} {meal_type} recipe.",
            "servings": servings,
            "prep_time_minutes": prep_time,
            "cook_time_minutes": cook_time,
            "total_time_minutes": total_time,
            "difficulty": difficulty,
            "cuisine": cuisine,
            "meal_type": meal_type,
            "dietary_restrictions": dietary_restrictions,
            "ingredients": ingredients,
            "cooking_steps": cooking_steps,
            "nutritional_info": {
                "calories": random.randint(200, 800),
                "protein_g": round(random.uniform(10, 50), 1),
                "carbs_g": round(random.uniform(20, 100), 1),
                "fat_g": round(random.uniform(5, 40), 1),
                "fiber_g": round(random.uniform(2, 15), 1),
                "sugar_g": round(random.uniform(1, 25), 1),
                "sodium_mg": random.randint(200, 1500)
            },
            "source": "cookidoo",
            "image_url": f"https://example.com/recipes/{recipe_id}.jpg",
            "tags": [cuisine.lower(), meal_type, difficulty],
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return recipe
    
    def generate_user_interaction(self, user_id: str, recipe_id: str) -> Dict:
        """Generate a user interaction event."""
        interaction_types = ["view", "modify", "save", "chat", "shopping_list"]
        
        interaction = {
            "interaction_id": f"int-{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "interaction_type": random.choice(interaction_types),
            "recipe_id": recipe_id if random.random() > 0.3 else None,
            "conversation_id": f"conv-{uuid.uuid4().hex[:8]}",
            "request_text": "User requested modification" if random.random() > 0.5 else None,
            "response_text": "Assistant provided response",
            "modifications_applied": ["dietary_change", "serving_adjustment"] if random.random() > 0.7 else [],
            "satisfaction_score": round(random.uniform(3.0, 5.0), 1),
            "feedback": "Helpful" if random.random() > 0.5 else None,
            "timestamp": datetime.now().isoformat(),
            "session_id": f"session-{uuid.uuid4().hex[:8]}",
            "metadata": {"source": "web_app", "version": "1.0.0"}
        }
        
        return interaction
    
    def generate_shopping_list(self, user_id: str, recipe_ids: List[str]) -> Dict:
        """Generate a shopping list."""
        items = [
            {
                "name": random.choice(self.SAMPLE_INGREDIENTS),
                "quantity": round(random.uniform(0.5, 5), 2),
                "unit": random.choice(self.UNITS),
                "category": random.choice(["produce", "dairy", "meat", "pantry"]),
                "checked": random.random() > 0.7,
                "notes": "",
                "from_recipes": [random.choice(recipe_ids)]
            }
            for _ in range(random.randint(5, 15))
        ]
        
        shopping_list = {
            "list_id": f"list-{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "recipe_ids": recipe_ids,
            "items": items,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "total_items": len(items),
            "checked_items": sum(1 for item in items if item["checked"])
        }
        
        return shopping_list


def generate_sample_data(num_recipes: int = 100, output_dir: str = "./sample_data"):
    """Generate complete sample dataset."""
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    generator = RecipeGenerator()
    
    print(f"Generating {num_recipes} sample recipes...")
    
    # Generate recipes
    recipes = [generator.generate_recipe() for _ in range(num_recipes)]
    with open(f"{output_dir}/recipes.json", "w") as f:
        json.dump(recipes, f, indent=2)
    print(f"✓ Created {len(recipes)} recipes -> {output_dir}/recipes.json")
    
    # Generate user interactions
    user_ids = [f"user-{i:04d}" for i in range(1, 21)]  # 20 users
    interactions = []
    
    for _ in range(num_recipes * 5):  # 5 interactions per recipe average
        user_id = random.choice(user_ids)
        recipe_id = random.choice(recipes)["recipe_id"]
        interactions.append(generator.generate_user_interaction(user_id, recipe_id))
    
    with open(f"{output_dir}/interactions.json", "w") as f:
        json.dump(interactions, f, indent=2)
    print(f"✓ Created {len(interactions)} interactions -> {output_dir}/interactions.json")
    
    # Generate shopping lists
    shopping_lists = []
    for user_id in user_ids:
        num_lists = random.randint(1, 3)
        for _ in range(num_lists):
            recipe_ids = [r["recipe_id"] for r in random.sample(recipes, random.randint(2, 5))]
            shopping_lists.append(generator.generate_shopping_list(user_id, recipe_ids))
    
    with open(f"{output_dir}/shopping_lists.json", "w") as f:
        json.dump(shopping_lists, f, indent=2)
    print(f"✓ Created {len(shopping_lists)} shopping lists -> {output_dir}/shopping_lists.json")
    
    print(f"\nSample data generated in: {output_dir}/")
    print(f"  - {len(recipes)} recipes")
    print(f"  - {len(interactions)} user interactions")
    print(f"  - {len(shopping_lists)} shopping lists")


if __name__ == "__main__":
    import sys
    
    num_recipes = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./sample_data"
    
    generate_sample_data(num_recipes, output_dir)
