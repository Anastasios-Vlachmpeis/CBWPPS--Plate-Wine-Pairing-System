"""
Wine Sommelier AI - Gemini 3 Flash Integration
Uses molecular flavor science to recommend wine pairings
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import google.genai as genai


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
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        
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
    
    def _repair_json(self, json_str: str) -> str:
        """
        Repair common JSON issues from Gemini responses:
        - Trailing commas in arrays/objects
        - Unterminated strings
        - Malformed structure (numbers outside arrays)
        
        Args:
            json_str: Potentially malformed JSON string
        
        Returns:
            Repaired JSON string
        """
        # Remove markdown code blocks if present
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        # Fix trailing commas in arrays and objects
        # Pattern: match comma before closing bracket/brace (but not inside strings)
        # Use a more careful approach - find brackets/braces and check for trailing commas
        def fix_trailing_commas(text):
            result = []
            i = 0
            in_string = False
            escape_next = False
            bracket_stack = []
            
            while i < len(text):
                char = text[i]
                
                if escape_next:
                    result.append(char)
                    escape_next = False
                    i += 1
                    continue
                
                if char == '\\':
                    escape_next = True
                    result.append(char)
                    i += 1
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    result.append(char)
                    i += 1
                    continue
                
                if not in_string:
                    if char in '[{':
                        bracket_stack.append((char, len(result)))
                        result.append(char)
                    elif char in ']}':
                        # Check for trailing comma before this bracket
                        if bracket_stack:
                            bracket_stack.pop()
                            # Look backwards for comma
                            j = len(result) - 1
                            while j >= 0 and result[j] in ' \n\t':
                                j -= 1
                            if j >= 0 and result[j] == ',':
                                # Remove trailing comma
                                result.pop(j)
                        result.append(char)
                    else:
                        result.append(char)
                else:
                    result.append(char)
                
                i += 1
            
            return ''.join(result)
        
        json_str = fix_trailing_commas(json_str)
        
        # Fix malformed array structure: number appearing after closing bracket
        # Pattern 1: ]\s*\d+\s*[,}] - number after closing bracket with comma/brace
        json_str = re.sub(r'\]\s*(\d+)\s*([,}])', r', \1]\2', json_str)
        
        # Pattern 2: ],\s*\d+\s*\n - number after closing bracket with comma, then newline
        # This handles cases like: ],\n114717\n"scientific_reasoning"
        json_str = re.sub(r'\]\s*,\s*(\d+)\s*\n', r', \1]\n', json_str)
        
        # Pattern 3: ]\s*\d+\s*\n - number after closing bracket, then newline (no comma)
        json_str = re.sub(r'\]\s*(\d+)\s*\n\s*"', r', \1],\n  "', json_str)
        
        # Fix numbers appearing before opening bracket (should be inside)
        json_str = re.sub(r'(\d+)\s*\[', r'[\1', json_str)
        
        # Fix unterminated strings in value fields
        # Look for pattern: "key": "value that's not closed
        def fix_unterminated_strings(text):
            lines = text.split('\n')
            fixed_lines = []
            
            for line in lines:
                # Check for key-value pairs with unterminated strings
                if ':' in line and '"' in line:
                    # Try to find if there's an unterminated string value
                    # Pattern: "key": "value...
                    match = re.search(r'"([^"]+)":\s*"([^"]*)$', line)
                    if match and not line.rstrip().endswith('"') and not line.rstrip().endswith('",'):
                        # Unterminated string - close it
                        if line.rstrip().endswith(','):
                            line = line.rstrip(',') + '",'
                        else:
                            line = line.rstrip() + '"'
                
                fixed_lines.append(line)
            
            return '\n'.join(fixed_lines)
        
        json_str = fix_unterminated_strings(json_str)
        
        # Fix double commas
        json_str = re.sub(r',\s*,+', ',', json_str)
        
        # Remove commas before closing brackets/braces (safety check)
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        return json_str
    
    def _parse_json_response(self, response_text: str, context: str = "") -> Dict[str, Any]:
        """
        Parse JSON response with repair attempts
        
        Args:
            response_text: Raw response text from Gemini
            context: Context string for error messages
        
        Returns:
            Parsed JSON dictionary
        """
        response_text = response_text.strip()
        
        # First attempt: repair and parse
        try:
            repaired = self._repair_json(response_text)
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass
        
        # Second attempt: try to extract JSON object if wrapped in text
        try:
            # Find first { and last }
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_substr = response_text[start:end+1]
                repaired = self._repair_json(json_substr)
                return json.loads(repaired)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Third attempt: try to fix top_matches array specifically
        try:
            # Extract top_matches array manually
            top_matches_match = re.search(r'"top_matches"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
            if top_matches_match:
                # Extract wine IDs from the array
                array_content = top_matches_match.group(1)
                # Find all numbers in the array
                wine_ids = [int(x.strip()) for x in re.findall(r'\d+', array_content) if x.strip()]
                if len(wine_ids) >= 3:
                    # Reconstruct JSON with fixed top_matches
                    # Extract other fields
                    scientific_match = re.search(r'"scientific_reasoning"\s*:\s*"([^"]*(?:"[^"]*")*[^"]*)', response_text, re.DOTALL)
                    culinary_match = re.search(r'"culinary_reasoning"\s*:\s*"([^"]*(?:"[^"]*")*[^"]*)', response_text, re.DOTALL)
                    upsell_match = re.search(r'"upsell_tip"\s*:\s*"([^"]*(?:"[^"]*")*[^"]*)', response_text, re.DOTALL)
                    
                    result = {
                        "top_matches": wine_ids[:3],
                        "scientific_reasoning": scientific_match.group(1) if scientific_match else "Molecular pairing analysis.",
                        "culinary_reasoning": culinary_match.group(1) if culinary_match else "Recommended wine pairing.",
                        "upsell_tip": upsell_match.group(1) if upsell_match else "Premium wine selection."
                    }
                    return result
        except (ValueError, AttributeError):
            pass
        
        # Final attempt: raise with helpful error
        raise ValueError(
            f"Failed to parse JSON response{context}.\n"
            f"Original error: JSON decode error\n"
            f"Response text (first 500 chars): {response_text[:500]}"
        )
    
    def _identify_ingredients(
        self,
        dish_description: Optional[str] = None,
        dish_image: Optional[bytes] = None
    ) -> List[str]:
        """
        Stage 1: Identify key ingredients from dish (small prompt, no knowledge base)
        
        Args:
            dish_description: Text description of the dish
            dish_image: Image bytes
        
        Returns:
            List of ingredient names
        """
        prompt = """You are a culinary expert. Identify the key ingredients in this dish.
        
Return ONLY a JSON array of ingredient names. Include:
- Main proteins/meats/fish
- Vegetables
- Herbs and spices
- Key flavoring agents (sauces, marinades, etc.)

Format: ["ingredient1", "ingredient2", "ingredient3", ...]

Dish: """
        
        if dish_image:
            prompt += "[Analyze the image]"
        elif dish_description:
            prompt += dish_description
        else:
            raise ValueError("Either dish_description or dish_image must be provided")
        
        # Generate response
        try:
            if dish_image:
                # For image input
                import PIL.Image
                import io
                image = PIL.Image.open(io.BytesIO(dish_image))
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt, image],
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 500,
                        "response_mime_type": "application/json"
                    }
                )
            else:
                # For text input
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 500,
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
            
            # Parse with repair
            parsed = self._parse_json_response(response_text, " (ingredient identification)")
            
            # Handle different response formats
            if isinstance(parsed, list):
                ingredients = parsed
            elif isinstance(parsed, dict):
                if "ingredients" in parsed:
                    ingredients = parsed["ingredients"]
                elif "ingredient" in parsed:
                    ingredients = [parsed["ingredient"]] if isinstance(parsed["ingredient"], str) else parsed["ingredient"]
                else:
                    # Try to extract array from dict values
                    ingredients = [v for v in parsed.values() if isinstance(v, list)]
                    if ingredients:
                        ingredients = ingredients[0]
                    else:
                        raise ValueError("Could not extract ingredients list from response")
            else:
                raise ValueError("Expected JSON array or object with ingredients")
            
            if not isinstance(ingredients, list):
                raise ValueError("Ingredients must be a list")
            
            return [str(ing).lower().strip() for ing in ingredients if ing]
            
        except Exception as e:
            raise RuntimeError(f"Error identifying ingredients: {e}")
    
    def _find_candidate_wines(self, ingredients: List[str], max_candidates: int = 20) -> List[Dict[str, Any]]:
        """
        Stage 2: Python-based molecular search to find candidate wines
        
        Args:
            ingredients: List of ingredient names
            max_candidates: Maximum number of candidate wines to return
        
        Returns:
            List of candidate wines with match information
        """
        # Helper function to clean ingredient name for matching
        def clean_name(name: str) -> str:
            name = name.lower().strip()
            # Remove special characters
            name = re.sub(r'[^a-z0-9\s]', '', name)
            name = re.sub(r'[_\s]+', ' ', name)
            return name.strip()
        
        # Collect all compounds from dish ingredients
        dish_compounds = set()
        matched_ingredients = []
        
        for ingredient in ingredients:
            cleaned = clean_name(ingredient)
            
            # Try exact match first
            if ingredient in self.ingredient_flavor_map:
                compounds = self.ingredient_flavor_map[ingredient].get("compounds", [])
                dish_compounds.update(compounds)
                matched_ingredients.append(ingredient)
                continue
            
            # Try cleaned name match
            for map_ingredient, data in self.ingredient_flavor_map.items():
                if data.get("cleaned_name") == cleaned:
                    compounds = data.get("compounds", [])
                    dish_compounds.update(compounds)
                    matched_ingredients.append(map_ingredient)
                    break
            
            # Try partial match
            for map_ingredient, data in self.ingredient_flavor_map.items():
                map_cleaned = data.get("cleaned_name", "")
                if cleaned in map_cleaned or map_cleaned in cleaned:
                    compounds = data.get("compounds", [])
                    dish_compounds.update(compounds)
                    if map_ingredient not in matched_ingredients:
                        matched_ingredients.append(map_ingredient)
        
        if not dish_compounds:
            print(f"Warning: No compounds found for ingredients: {ingredients}")
            # Fallback: return wines based on harmonize tags
            candidates = []
            for wine in self.wines:
                harmonize = wine.get("harmonize", [])
                # Simple keyword matching
                for ingredient in ingredients:
                    for tag in harmonize:
                        if ingredient.lower() in tag.lower() or tag.lower() in ingredient.lower():
                            candidates.append({
                                "wine": wine,
                                "shared_compounds": [],
                                "match_count": 0,
                                "match_type": "harmonize"
                            })
                            break
                    if candidates and candidates[-1]["wine"]["wine_id"] == wine["wine_id"]:
                        break
            return candidates[:max_candidates]
        
        # Search wines by compounds
        matches = self.search_wines_by_compounds(list(dish_compounds))
        
        # Also check harmonize tags
        harmonize_matches = []
        for wine in self.wines:
            harmonize = wine.get("harmonize", [])
            for ingredient in ingredients:
                for tag in harmonize:
                    if ingredient.lower() in tag.lower() or tag.lower() in ingredient.lower():
                        # Check if already in matches
                        if not any(m["wine"]["wine_id"] == wine["wine_id"] for m in matches):
                            harmonize_matches.append({
                                "wine": wine,
                                "shared_compounds": [],
                                "match_count": 0,
                                "match_type": "harmonize"
                            })
                        break
                if harmonize_matches and harmonize_matches[-1]["wine"]["wine_id"] == wine["wine_id"]:
                    break
        
        # Combine and deduplicate
        all_matches = matches + harmonize_matches
        seen_ids = set()
        unique_matches = []
        for match in all_matches:
            wine_id = match["wine"]["wine_id"]
            if wine_id not in seen_ids:
                seen_ids.add(wine_id)
                unique_matches.append(match)
        
        # Sort: compound matches first (by match_count), then harmonize matches
        unique_matches.sort(key=lambda x: (x.get("match_type") != "harmonize", -x.get("match_count", 0)))
        
        return unique_matches[:max_candidates]
    
    def _finalize_recommendation(
        self,
        candidate_wines: List[Dict[str, Any]],
        ingredients: List[str],
        dish_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stage 3: Final selection with only top candidates (small prompt)
        
        Args:
            candidate_wines: List of candidate wines from Stage 2
            ingredients: List of identified ingredients
            dish_description: Original dish description
        
        Returns:
            Final recommendation dictionary
        """
        if not candidate_wines:
            raise ValueError("No candidate wines found")
        
        # Prepare candidate wines data (only essential fields to minimize tokens)
        candidates_data = []
        for match in candidate_wines:
            wine = match["wine"]
            candidates_data.append({
                "wine_id": wine.get("wine_id"),
                "wine_name": wine.get("wine_name"),
                "type_name": wine.get("type_name"),
                "body_name": wine.get("body_name"),
                "acidity_name": wine.get("acidity_name"),
                "grapes": wine.get("grapes", []),
                "country": wine.get("country"),
                "region": wine.get("region"),
                "winery": wine.get("winery"),
                "harmonize": wine.get("harmonize", []),
                "flavor_compounds": wine.get("flavor_compounds", []),
                "shared_compounds": match.get("shared_compounds", []),
                "match_count": match.get("match_count", 0)
            })
        
        candidates_json = json.dumps(candidates_data, ensure_ascii=False, indent=2)
        
        prompt = f"""You are a World-Class Molecular Sommelier and Data Analyst.

Analyze these candidate wines and select the top 3 best pairings for this dish.

DISH:
{dish_description or f"Ingredients: {', '.join(ingredients)}"}

CANDIDATE WINES ({len(candidates_data)} wines):
{candidates_json}

SELECTION CRITERIA:
1. Molecular connection: Wines with more shared compounds (higher match_count) are stronger matches
2. Harmonize tags: Wines with matching harmonize tags are good traditional pairings
3. Balance: Consider body, acidity, and type appropriateness
4. Diversity: Select different styles/types for variety

OUTPUT FORMAT (STRICT JSON - NO MARKDOWN, NO CODE BLOCKS):

{{
  "top_matches": [wine_id_1, wine_id_2, wine_id_3],
  "scientific_reasoning": "Detailed explanation mentioning specific shared molecules. Example: 'The sea bass contains Citral and Geraniol compounds, which are also present in Wine #1's flavor profile. These shared terpenes create a harmonious molecular bridge...'",
  "culinary_reasoning": "Human-friendly explanation for restaurant staff. Example: 'This crisp white wine complements the delicate fish with its bright acidity, while the shared citrus notes enhance the lemon butter sauce.'",
  "upsell_tip": "Why this wine increases meal value. Example: 'This premium selection elevates the dish by adding complexity and depth, creating a memorable dining experience that justifies the investment.'"
}}

IMPORTANT:
- Return ONLY valid JSON, no markdown formatting, no code blocks
- Use wine_id values from the candidates
- Be specific about compound names in scientific_reasoning
- Reference the shared_compounds and match_count data
- Make culinary_reasoning accessible to non-experts
- Make upsell_tip compelling but honest
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
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
            
            # Parse JSON response with repair
            result = self._parse_json_response(response_text, " (final recommendation)")
            
            # Validate structure
            required_keys = ["top_matches", "scientific_reasoning", "culinary_reasoning", "upsell_tip"]
            for key in required_keys:
                if key not in result:
                    raise ValueError(f"Missing required key in response: {key}")
            
            # Validate top_matches
            if not isinstance(result["top_matches"], list):
                raise ValueError("top_matches must be a list")
            
            # Ensure exactly 3 matches (pad or truncate if needed)
            if len(result["top_matches"]) < 3:
                # If we have fewer than 3, try to pad with additional candidates
                candidate_ids = [w["wine"]["wine_id"] for w in candidate_wines]
                for cid in candidate_ids:
                    if cid not in result["top_matches"]:
                        result["top_matches"].append(cid)
                        if len(result["top_matches"]) >= 3:
                            break
                # If still less than 3, pad with first candidate
                while len(result["top_matches"]) < 3 and candidate_ids:
                    if candidate_ids[0] not in result["top_matches"]:
                        result["top_matches"].append(candidate_ids[0])
                    candidate_ids = candidate_ids[1:]
            
            # Truncate to 3 if more than 3
            result["top_matches"] = result["top_matches"][:3]
            
            # Ensure all required fields exist with defaults
            if "scientific_reasoning" not in result:
                result["scientific_reasoning"] = "Molecular pairing analysis based on shared flavor compounds."
            if "culinary_reasoning" not in result:
                result["culinary_reasoning"] = "Recommended wine pairing for this dish."
            if "upsell_tip" not in result:
                result["upsell_tip"] = "This wine selection enhances the dining experience."
            
            # Add wine details for convenience
            result["wine_details"] = []
            for wine_id in result["top_matches"]:
                wine = next((w for w in self.wines if w.get("wine_id") == wine_id), None)
                if wine:
                    result["wine_details"].append(wine)
                else:
                    print(f"Warning: Wine ID {wine_id} not found in database")
            
            return result
            
        except ValueError as e:
            # Re-raise ValueError (from _parse_json_response)
            raise
        except Exception as e:
            raise RuntimeError(f"Error finalizing recommendation: {e}")
    
    def recommend(
        self,
        dish_description: Optional[str] = None,
        dish_image: Optional[Union[bytes, str]] = None
    ) -> Dict[str, Any]:
        """
        Recommend wine pairings for a dish using efficient two-stage approach
        
        Stage 1: Identify ingredients (small prompt)
        Stage 2: Python-based molecular search (no API call)
        Stage 3: Final selection with top candidates (small prompt)
        
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
        
        if not dish_description and not image_data:
            raise ValueError("Either dish_description or dish_image must be provided")
        
        # STAGE 1: Identify ingredients (small prompt, ~100-500 tokens)
        print("Stage 1: Identifying ingredients...")
        ingredients = self._identify_ingredients(
            dish_description=dish_description,
            dish_image=image_data
        )
        print(f"  Identified ingredients: {', '.join(ingredients)}")
        
        # STAGE 2: Python-based molecular search (no API call)
        print("Stage 2: Finding candidate wines by molecular match...")
        candidate_wines = self._find_candidate_wines(ingredients, max_candidates=20)
        print(f"  Found {len(candidate_wines)} candidate wines")
        
        if not candidate_wines:
            raise ValueError("No matching wines found. Try a different dish description.")
        
        # STAGE 3: Final selection with only top candidates (small prompt, ~2000-5000 tokens)
        print("Stage 3: Finalizing recommendation...")
        result = self._finalize_recommendation(
            candidate_wines=candidate_wines,
            ingredients=ingredients,
            dish_description=dish_description
        )
        
        return result
    
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
    print("Example: Recommending wine for 'Veal Saltimbocca'")
    print("-" * 70)
    
    try:
        result = sommelier.recommend(
            dish_description="Veal Saltimbocca:Ingredients:2 thin veal scallopini (pounded to uniform thickness), 4 slices of prosciutto, Large bunch of fresh sage leaves, 4 tbsp butter, 2 tbsp olive oil, Splash of white wine (or Marsala), Salt and pepper to taste"
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
