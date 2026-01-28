"""
Batch Menu Profiler - Phase 1 Initial Setup
Processes all restaurant recipes to create menu flavor profiles
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import google.genai as genai


class MenuProfiler:
    """
    Batch processes restaurant recipes to create molecular flavor profiles
    References WineSommelier logic for ingredient-compound mapping
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3-flash-preview"):
        """
        Initialize the Menu Profiler
        
        Args:
            api_key: Google AI API key (if None, reads from GOOGLE_AI_API_KEY env var)
            model_name: Gemini model to use (default: gemini-3-flash-preview)
        """
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            if api_key is None:
                # Try .env file
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    api_key = os.getenv("GOOGLE_AI_API_KEY")
                except ImportError:
                    pass
        
        if not api_key:
            raise ValueError(
                "API key not found. Please set GOOGLE_AI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Configure Gemini
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        
        # Load ingredient flavor map (reuse WineSommelier logic)
        self.ingredient_flavor_map = None
        self._load_ingredient_map()
    
    def _load_ingredient_map(self):
        """Load ingredient flavor map from processed data"""
        ingredient_path = Path("processed_data") / "ingredient_flavor_map.json"
        if not ingredient_path.exists():
            raise FileNotFoundError(f"Ingredient flavor map not found: {ingredient_path}")
        
        with open(ingredient_path, 'r', encoding='utf-8') as f:
            self.ingredient_flavor_map = json.load(f)
        
        print(f"Loaded {len(self.ingredient_flavor_map)} ingredients from flavor map")
    
    def _clean_ingredient_name(self, name: str) -> str:
        """Clean ingredient name for matching (reuse WineSommelier logic)"""
        name = name.lower().strip()
        # Remove special characters
        name = re.sub(r'[^a-z0-9\s]', '', name)
        name = re.sub(r'[_\s]+', ' ', name)
        return name.strip()
    
    def _get_compounds_for_ingredient(self, ingredient: str) -> List[str]:
        """
        Get compounds for an ingredient from the flavor map
        
        Args:
            ingredient: Ingredient name
        
        Returns:
            List of compound names, empty list if not found
        """
        cleaned = self._clean_ingredient_name(ingredient)
        
        # Try exact match first
        if ingredient in self.ingredient_flavor_map:
            return self.ingredient_flavor_map[ingredient].get("compounds", [])
        
        # Try cleaned name match
        for map_ingredient, data in self.ingredient_flavor_map.items():
            if data.get("cleaned_name") == cleaned:
                return data.get("compounds", [])
        
        # Try partial match
        for map_ingredient, data in self.ingredient_flavor_map.items():
            map_cleaned = data.get("cleaned_name", "")
            if cleaned in map_cleaned or map_cleaned in cleaned:
                return data.get("compounds", [])
        
        return []
    
    def _estimate_compounds_for_missing_ingredient(self, ingredient: str) -> List[str]:
        """
        Use Gemini to estimate compounds for ingredients not in the flavor map
        
        Args:
            ingredient: Ingredient name not found in map
        
        Returns:
            List of 5 most likely compound names
        """
        prompt = f"""You are a flavor chemist. For the ingredient "{ingredient}", 
provide the 5 most likely chemical flavor compounds found in this ingredient.

Return ONLY a JSON array of compound names (use standard chemical names like "Citral", "Geraniol", etc.).

Format: ["compound1", "compound2", "compound3", "compound4", "compound5"]

Ingredient: {ingredient}"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 300,
                    "response_mime_type": "application/json"
                }
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                response_text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text.strip()
            elif isinstance(response, dict) and 'text' in response:
                response_text = response['text'].strip()
            else:
                response_text = str(response).strip()
            
            # Clean and parse JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            compounds = json.loads(response_text)
            if isinstance(compounds, list):
                return compounds[:5]  # Ensure max 5
            elif isinstance(compounds, dict):
                # Sometimes returns {"compounds": [...]}
                if "compounds" in compounds:
                    return compounds["compounds"][:5]
                # Try to find array in values
                for value in compounds.values():
                    if isinstance(value, list):
                        return value[:5]
            
            return []
            
        except Exception as e:
            print(f"  Warning: Could not estimate compounds for '{ingredient}': {e}")
            return []
    
    def _extract_dish_info(self, recipe_content: str, is_image: bool = False) -> Dict[str, Any]:
        """
        Use Gemini to extract dish information from recipe
        
        Args:
            recipe_content: Text content or image bytes
            is_image: Whether content is an image
        
        Returns:
            Dictionary with dish_name, key_ingredients, dominant_flavors
        """
        prompt = """You are a culinary expert analyzing a recipe or dish.

Extract the following information:
1. dish_name: The name of the dish
2. key_ingredients: List of main ingredients (proteins, vegetables, herbs, spices, sauces)
3. dominant_flavors: List of dominant flavor profiles (e.g., "Spicy", "Acidic", "Umami", "Sweet", "Bitter", "Salty", "Rich", "Light", "Heavy", "Creamy", "Smoky", etc.)

Return ONLY valid JSON in this format:
{
  "dish_name": "Dish Name",
  "key_ingredients": ["ingredient1", "ingredient2", ...],
  "dominant_flavors": ["flavor1", "flavor2", ...]
}

Recipe/Dish: """
        
        try:
            if is_image:
                import PIL.Image
                import io
                if isinstance(recipe_content, bytes):
                    image = PIL.Image.open(io.BytesIO(recipe_content))
                else:
                    image = recipe_content  # Assume it's already a PIL Image
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt, image],
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 1000,
                        "response_mime_type": "application/json"
                    }
                )
            else:
                full_prompt = prompt + recipe_content
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 1000,
                        "response_mime_type": "application/json"
                    }
                )
            
            # Extract text from response
            if hasattr(response, 'text'):
                response_text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text.strip()
            elif isinstance(response, dict) and 'text' in response:
                response_text = response['text'].strip()
            else:
                response_text = str(response).strip()
            
            # Clean and parse JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Validate required fields
            if "dish_name" not in result:
                result["dish_name"] = "Unknown Dish"
            if "key_ingredients" not in result:
                result["key_ingredients"] = []
            if "dominant_flavors" not in result:
                result["dominant_flavors"] = []
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"  Warning: Failed to parse JSON response: {e}")
            return {
                "dish_name": "Unknown Dish",
                "key_ingredients": [],
                "dominant_flavors": []
            }
        except Exception as e:
            print(f"  Warning: Error extracting dish info: {e}")
            return {
                "dish_name": "Unknown Dish",
                "key_ingredients": [],
                "dominant_flavors": []
            }
    
    def _build_molecular_profile(self, ingredients: List[str]) -> List[str]:
        """
        Build molecular profile from ingredients
        
        Args:
            ingredients: List of ingredient names
        
        Returns:
            List of unique compound names
        """
        all_compounds = set()
        missing_ingredients = []
        
        for ingredient in ingredients:
            compounds = self._get_compounds_for_ingredient(ingredient)
            if compounds:
                all_compounds.update(compounds)
            else:
                missing_ingredients.append(ingredient)
        
        # Fallback: estimate compounds for missing ingredients
        if missing_ingredients:
            print(f"  Estimating compounds for {len(missing_ingredients)} missing ingredients...")
            for ingredient in missing_ingredients:
                estimated = self._estimate_compounds_for_missing_ingredient(ingredient)
                if estimated:
                    all_compounds.update(estimated)
                    print(f"    {ingredient}: {', '.join(estimated[:3])}...")
        
        return sorted(list(all_compounds))
    
    def _suggest_wine_type(self, dominant_flavors: List[str], compounds: List[str]) -> str:
        """
        Suggest wine type based on dominant flavors and compounds
        
        Args:
            dominant_flavors: List of flavor tags
            compounds: List of chemical compounds
        
        Returns:
            Suggested wine type (Red, White, Rosé, Sparkling, Dessert)
        """
        flavors_lower = [f.lower() for f in dominant_flavors]
        compounds_lower = [c.lower() for c in compounds]
        
        # Simple heuristic-based suggestions
        if any(f in flavors_lower for f in ['spicy', 'rich', 'heavy', 'umami', 'meaty']):
            return "Red"
        elif any(f in flavors_lower for f in ['light', 'acidic', 'citrus', 'fresh', 'crisp']):
            return "White"
        elif any(f in flavors_lower for f in ['sweet', 'dessert', 'creamy']):
            return "Dessert"
        elif any(f in flavors_lower for f in ['celebratory', 'bubbly']):
            return "Sparkling"
        else:
            # Default based on compounds (terpenes often in whites)
            if any('citral' in c or 'geraniol' in c or 'linalool' in c for c in compounds_lower):
                return "White"
            return "Red"  # Default fallback
    
    def process_recipe_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process a single recipe file
        
        Args:
            file_path: Path to recipe file (.txt, .jpg, or .png)
        
        Returns:
            Dictionary with dish profile or None if error
        """
        try:
            # Check if file is empty
            if file_path.stat().st_size == 0:
                print(f"  Warning: Empty file {file_path.name}, skipping...")
                return None
            
            # Determine file type
            suffix = file_path.suffix.lower()
            is_image = suffix in ['.jpg', '.jpeg', '.png']
            
            # Read file content
            if is_image:
                with open(file_path, 'rb') as f:
                    content = f.read()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"  Warning: Empty text file {file_path.name}, skipping...")
                        return None
            
            # Extract dish info
            print(f"  Processing {file_path.name}...")
            dish_info = self._extract_dish_info(content, is_image=is_image)
            
            # Build molecular profile
            ingredients = dish_info.get("key_ingredients", [])
            compounds = self._build_molecular_profile(ingredients)
            
            # Suggest wine type
            dominant_flavors = dish_info.get("dominant_flavors", [])
            suggested_wine_type = self._suggest_wine_type(dominant_flavors, compounds)
            
            # Create dish profile
            dish_id = file_path.stem  # Use filename without extension as ID
            
            profile = {
                "name": dish_info.get("dish_name", "Unknown Dish"),
                "compounds": compounds,
                "tags": dominant_flavors,
                "suggested_wine_type": suggested_wine_type,
                "ingredients": ingredients  # Keep for reference
            }
            
            print(f"    ✓ {profile['name']}: {len(compounds)} compounds, {len(dominant_flavors)} flavor tags")
            
            return profile
            
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            return None
    
    def process_recipes_folder(self, recipes_folder: Path = Path("recipes")) -> Dict[str, Dict[str, Any]]:
        """
        Process all recipes in a folder
        
        Args:
            recipes_folder: Path to recipes folder
        
        Returns:
            Dictionary mapping dish_id to dish profile
        """
        if not recipes_folder.exists():
            print(f"Recipes folder not found: {recipes_folder}")
            print("Creating empty folder...")
            recipes_folder.mkdir(exist_ok=True)
            return {}
        
        # Find all recipe files
        recipe_files = []
        for ext in ['.txt', '.jpg', '.jpeg', '.png']:
            recipe_files.extend(recipes_folder.glob(f"*{ext}"))
            recipe_files.extend(recipes_folder.glob(f"*{ext.upper()}"))
        
        if not recipe_files:
            print(f"No recipe files found in {recipes_folder}")
            return {}
        
        print(f"Found {len(recipe_files)} recipe files")
        print("-" * 70)
        
        menu_profile = {}
        processed = 0
        errors = 0
        
        for file_path in sorted(recipe_files):
            profile = self.process_recipe_file(file_path)
            if profile:
                dish_id = file_path.stem
                menu_profile[dish_id] = profile
                processed += 1
            else:
                errors += 1
        
        print("-" * 70)
        print(f"Processed: {processed} dishes | Errors: {errors}")
        
        return menu_profile
    
    def save_menu_profile(self, menu_profile: Dict[str, Dict[str, Any]], 
                         output_path: Path = Path("processed_data/menu_flavor_profile.json")):
        """
        Save menu profile to JSON file
        
        Args:
            menu_profile: Dictionary mapping dish_id to dish profile
            output_path: Path to output JSON file
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(menu_profile, f, indent=2, ensure_ascii=False)
        
        print(f"\nMenu profile saved to: {output_path}")
        print(f"Total dishes profiled: {len(menu_profile)}")


def main():
    """Main function to run batch profiling"""
    import sys
    
    # Initialize profiler
    try:
        profiler = MenuProfiler()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set your Google AI API key:")
        print("  export GOOGLE_AI_API_KEY='your-api-key'")
        print("  Or create a .env file with: GOOGLE_AI_API_KEY=your-api-key")
        sys.exit(1)
    
    # Process recipes
    recipes_folder = Path("recipes")
    menu_profile = profiler.process_recipes_folder(recipes_folder)
    
    # Save results
    if menu_profile:
        output_path = Path("processed_data/menu_flavor_profile.json")
        profiler.save_menu_profile(menu_profile, output_path)
        
        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        total_compounds = sum(len(dish["compounds"]) for dish in menu_profile.values())
        wine_types = {}
        for dish in menu_profile.values():
            wine_type = dish.get("suggested_wine_type", "Unknown")
            wine_types[wine_type] = wine_types.get(wine_type, 0) + 1
        
        print(f"Total dishes: {len(menu_profile)}")
        print(f"Total unique compounds: {total_compounds}")
        print(f"\nSuggested wine types:")
        for wine_type, count in sorted(wine_types.items()):
            print(f"  {wine_type}: {count}")
    else:
        print("\nNo dishes processed. Please add recipe files to the 'recipes' folder.")


if __name__ == "__main__":
    main()
