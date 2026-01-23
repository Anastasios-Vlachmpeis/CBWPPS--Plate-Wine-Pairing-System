"""
Wine Sommelier AI - Gemini 3 Flash Integration
Uses molecular flavor science to recommend wine pairings
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class WineSommelier:
    """
    World-Class Molecular Sommelier using Gemini 3 Flash
    Recommends wines based on molecular flavor compound analysis
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3-flash-preview"):
        """
        Initialize the Wine Sommelier
        
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
        genai.configure(api_key=api_key)
        
        # Initialize model with safety settings
        self.model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Load knowledge base
        self.wines = None
        self.ingredient_flavor_map = None
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load processed wines and ingredient flavor map from JSON files"""
        processed_data_dir = Path("processed_data")
        
        # Load wines
        wines_path = processed_data_dir / "processed_wines.json"
        if not wines_path.exists():
            raise FileNotFoundError(f"Wines file not found: {wines_path}")
        
        with open(wines_path, 'r', encoding='utf-8') as f:
            self.wines = json.load(f)
        
        # Load ingredient flavor map
        ingredient_path = processed_data_dir / "ingredient_flavor_map.json"
        if not ingredient_path.exists():
            raise FileNotFoundError(f"Ingredient flavor map not found: {ingredient_path}")
        
        with open(ingredient_path, 'r', encoding='utf-8') as f:
            self.ingredient_flavor_map = json.load(f)
        
        print(f"Loaded {len(self.wines)} wines and {len(self.ingredient_flavor_map)} ingredients")
    
    def _create_system_instruction(self) -> str:
        """Create the system instruction for Gemini"""
        return """You are a World-Class Molecular Sommelier and Data Analyst with deep expertise in:
- Flavor chemistry and molecular gastronomy
- Wine science and terroir
- Food-wine pairing principles
- Chemical compound interactions in food and wine

Your role is to analyze dishes at a molecular level and recommend wines based on shared flavor compounds, 
culinary harmony, and scientific principles. You must provide detailed scientific reasoning while also 
making recommendations accessible to restaurant staff and customers."""
    
    def _create_prompt(
        self, 
        dish_description: Optional[str] = None,
        dish_image: Optional[bytes] = None
    ) -> str:
        """
        Create the complete prompt with knowledge base context
        
        Args:
            dish_description: Text description of the dish
            dish_image: Image bytes (if provided, description is optional)
        
        Returns:
            Complete prompt string
        """
        # Format wines data for context (compact JSON)
        wines_json = json.dumps(self.wines, ensure_ascii=False, indent=2)
        
        # Format ingredient map (compact JSON)
        ingredient_map_json = json.dumps(self.ingredient_flavor_map, ensure_ascii=False, indent=2)
        
        # Build the prompt
        prompt = f"""You are analyzing a dish to recommend wine pairings using molecular flavor science.

KNOWLEDGE BASE:

1. WINE DATABASE ({len(self.wines)} wines):
{wines_json}

2. INGREDIENT FLAVOR MAP ({len(self.ingredient_flavor_map)} ingredients):
{ingredient_map_json}

MOLECULAR SEARCH METHODOLOGY:

Step 1: Identify Key Ingredients
- Extract the primary ingredients from the dish description/image
- Consider both main proteins/vegetables and flavoring agents (herbs, spices, sauces)

Step 2: Cross-Reference Chemical Compounds
- For each identified ingredient, look up its compounds in the ingredient_flavor_map
- Compile a list of all unique compounds present in the dish

Step 3: Find Wine Matches
- Search wines that have overlapping flavor_compounds with the dish
- Also consider wines where the 'harmonize' field matches the dish category
- Prioritize wines with:
  * More shared compounds (stronger molecular connection)
  * Matching harmonize tags
  * Appropriate body/acidity for the dish type

Step 4: Select Top 3 Recommendations
- Choose wines with the strongest molecular connections
- Ensure diversity (different types, regions, or styles)
- Consider traditional pairing wisdom alongside molecular science

OUTPUT FORMAT (STRICT JSON - NO MARKDOWN, NO CODE BLOCKS):

{{
  "top_matches": [wine_id_1, wine_id_2, wine_id_3],
  "scientific_reasoning": "Detailed explanation mentioning specific shared molecules. Example: 'The sea bass contains Citral (3,7-dimethyl-2,6-octadienal) and Geraniol compounds, which are also present in the Sauvignon Blanc's flavor profile. These shared terpenes create a harmonious molecular bridge...'",
  "culinary_reasoning": "Human-friendly explanation for restaurant staff. Example: 'This crisp white wine complements the delicate fish with its bright acidity, while the shared citrus notes enhance the lemon butter sauce.'",
  "upsell_tip": "Why this wine increases meal value. Example: 'This premium selection elevates the dish by adding complexity and depth, creating a memorable dining experience that justifies the investment.'"
}}

IMPORTANT:
- Return ONLY valid JSON, no markdown formatting, no code blocks
- Use wine_id values from the database
- Be specific about compound names in scientific_reasoning
- Make culinary_reasoning accessible to non-experts
- Make upsell_tip compelling but honest

DISH TO ANALYZE:
"""
        
        if dish_image:
            prompt += "[Image provided - analyze the dish visually]"
        elif dish_description:
            prompt += f"{dish_description}"
        else:
            raise ValueError("Either dish_description or dish_image must be provided")
        
        return prompt
    
    def recommend(
        self,
        dish_description: Optional[str] = None,
        dish_image: Optional[Union[bytes, str]] = None
    ) -> Dict[str, Any]:
        """
        Recommend wine pairings for a dish
        
        Args:
            dish_description: Text description of the dish (e.g., "Grilled sea bass with lemon butter sauce")
            dish_image: Image bytes or path to image file
        
        Returns:
            Dictionary with:
            - top_matches: List of 3 wine IDs
            - scientific_reasoning: Detailed molecular explanation
            - culinary_reasoning: Human-friendly explanation
            - upsell_tip: Value proposition
        
        Raises:
            ValueError: If neither dish_description nor dish_image provided
            ValueError: If API key not configured
        """
        # Handle image input
        image_data = None
        if dish_image:
            if isinstance(dish_image, str):
                # Assume it's a file path
                image_path = Path(dish_image)
                if not image_path.exists():
                    raise FileNotFoundError(f"Image file not found: {image_path}")
                with open(image_path, 'rb') as f:
                    image_data = f.read()
            elif isinstance(dish_image, bytes):
                image_data = dish_image
            else:
                raise ValueError("dish_image must be bytes or file path string")
        
        # Create prompt
        prompt = self._create_prompt(
            dish_description=dish_description,
            dish_image=image_data
        )
        
        # Prepare content for Gemini
        if image_data:
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(image_data))
            content = [prompt, image]
        else:
            content = prompt
        
        # Generate response
        try:
            response = self.model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Validate structure
            required_keys = ["top_matches", "scientific_reasoning", "culinary_reasoning", "upsell_tip"]
            for key in required_keys:
                if key not in result:
                    raise ValueError(f"Missing required key in response: {key}")
            
            # Validate top_matches
            if not isinstance(result["top_matches"], list) or len(result["top_matches"]) != 3:
                raise ValueError("top_matches must be a list of exactly 3 wine IDs")
            
            # Add wine details for convenience
            result["wine_details"] = []
            for wine_id in result["top_matches"]:
                wine = next((w for w in self.wines if w.get("wine_id") == wine_id), None)
                if wine:
                    result["wine_details"].append(wine)
                else:
                    print(f"Warning: Wine ID {wine_id} not found in database")
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse text: {response_text}")
        except Exception as e:
            raise RuntimeError(f"Error generating recommendation: {e}")
    
    def get_wine_by_id(self, wine_id: int) -> Optional[Dict[str, Any]]:
        """Get full wine details by ID"""
        return next((w for w in self.wines if w.get("wine_id") == wine_id), None)
    
    def search_wines_by_compounds(self, compounds: List[str]) -> List[Dict[str, Any]]:
        """
        Helper method to search wines by shared compounds
        
        Args:
            compounds: List of compound names to search for
        
        Returns:
            List of wines that share at least one compound, sorted by number of matches
        """
        matches = []
        compounds_set = set(compounds)
        
        for wine in self.wines:
            wine_compounds = set(wine.get("flavor_compounds", []))
            shared = compounds_set.intersection(wine_compounds)
            if shared:
                matches.append({
                    "wine": wine,
                    "shared_compounds": list(shared),
                    "match_count": len(shared)
                })
        
        # Sort by match count (descending)
        matches.sort(key=lambda x: x["match_count"], reverse=True)
        return matches


def main():
    """Example usage"""
    import sys
    
    # Initialize sommelier
    try:
        sommelier = WineSommelier()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set your Google AI API key:")
        print("  export GOOGLE_AI_API_KEY='your-api-key'")
        print("  Or create a .env file with: GOOGLE_AI_API_KEY=your-api-key")
        sys.exit(1)
    
    # Example: Text-based recommendation
    print("Example: Recommending wine for 'Grilled sea bass with lemon butter sauce and herbs'")
    print("-" * 70)
    
    try:
        result = sommelier.recommend(
            dish_description="Grilled sea bass with lemon butter sauce and fresh herbs"
        )
        
        print("\nTOP 3 WINE RECOMMENDATIONS:")
        print(f"Wine IDs: {result['top_matches']}")
        
        print("\nSCIENTIFIC REASONING:")
        print(result['scientific_reasoning'])
        
        print("\nCULINARY REASONING:")
        print(result['culinary_reasoning'])
        
        print("\nUPSELL TIP:")
        print(result['upsell_tip'])
        
        print("\nWINE DETAILS:")
        for i, wine in enumerate(result.get('wine_details', []), 1):
            print(f"\n{i}. {wine.get('wine_name', 'Unknown')}")
            print(f"   Type: {wine.get('type_name', 'Unknown')}")
            print(f"   Body: {wine.get('body_name', 'Unknown')}")
            print(f"   Acidity: {wine.get('acidity_name', 'Unknown')}")
            print(f"   Grapes: {', '.join(wine.get('grapes', []))}")
            print(f"   Region: {wine.get('region', 'Unknown')}, {wine.get('country', 'Unknown')}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
