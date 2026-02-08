"""
Menu extractor module
Uses Gemini to extract dishes and wines from various file formats
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import google.genai as genai
from utils.file_parsers import (
    read_excel_content,
    read_csv_content,
    detect_file_type
)
from core.data_formats import normalize_dish_format, normalize_wine_format
from utils.config import DEFAULT_INGREDIENT_MAP_PATH


class MenuExtractor:
    """
    Extracts dishes and wines from various file formats using Gemini
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3-flash-preview"):
        """
        Initialize the Menu Extractor
        
        Args:
            api_key: Google AI API key (if None, reads from GOOGLE_AI_API_KEY env var)
            model_name: Gemini model to use
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
        
        # Load ingredient flavor map for compound mapping
        self.ingredient_flavor_map = None
        self._load_ingredient_map()
    
    def _load_ingredient_map(self):
        """Load ingredient flavor map from processed data"""
        ingredient_path = Path(DEFAULT_INGREDIENT_MAP_PATH)
        if ingredient_path.exists():
            with open(ingredient_path, 'r', encoding='utf-8') as f:
                self.ingredient_flavor_map = json.load(f)
    
    def _clean_ingredient_name(self, name: str) -> str:
        """Clean ingredient name for matching"""
        name = name.lower().strip()
        name = re.sub(r'[^a-z0-9\s]', '', name)
        name = re.sub(r'[_\s]+', ' ', name)
        return name.strip()
    
    def _get_compounds_for_ingredient(self, ingredient: str) -> List[str]:
        """Get compounds for an ingredient from the flavor map"""
        if not self.ingredient_flavor_map:
            return []
        
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
    
    def _enrich_ingredient_with_compounds(self, ingredient: str) -> List[str]:
        """
        Query Gemini to get flavor compounds for an ingredient not in the map
        Saves the new ingredient to ingredient_flavor_map.json
        
        Args:
            ingredient: Name of the ingredient
            
        Returns:
            List of flavor compound names (up to 70)
        """
        prompt = f"""You are a flavor chemistry expert. Based on online information and scientific knowledge, assign up to 70 flavor compounds to the ingredient: {ingredient}

Return ONLY a JSON array of compound names (no markdown, no code blocks):
["compound1", "compound2", "compound3", ...]

Focus on the most important and characteristic flavor compounds for this ingredient. Use standard chemical compound names."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 2000,
                    "response_mime_type": "application/json"
                }
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                response_text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text.strip()
            else:
                response_text = str(response).strip()
            
            # Clean JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse compounds
            compounds = json.loads(response_text)
            if not isinstance(compounds, list):
                compounds = []
            
            # Limit to 70 compounds
            compounds = compounds[:70]
            
            # Save to ingredient flavor map
            if self.ingredient_flavor_map is not None:
                cleaned_name = self._clean_ingredient_name(ingredient)
                self.ingredient_flavor_map[ingredient] = {
                    "cleaned_name": cleaned_name,
                    "compounds": compounds
                }
                
                # Save to file
                ingredient_path = Path(DEFAULT_INGREDIENT_MAP_PATH)
                if ingredient_path.exists():
                    with open(ingredient_path, 'w', encoding='utf-8') as f:
                        json.dump(self.ingredient_flavor_map, f, indent=2, ensure_ascii=False)
                    print(f"  Saved new ingredient '{ingredient}' with {len(compounds)} compounds to flavor map")
            
            return compounds
            
        except Exception as e:
            print(f"  Warning: Failed to enrich ingredient '{ingredient}': {e}")
            return []
    
    def _build_compounds_for_dish(self, ingredients: List[str]) -> List[str]:
        """
        Build compound list for a dish from its ingredients
        If ingredient not found in map, queries Gemini and saves it
        """
        all_compounds = set()
        for ingredient in ingredients:
            compounds = self._get_compounds_for_ingredient(ingredient)
            
            # If not found, enrich with Gemini
            if not compounds:
                print(f"  Ingredient '{ingredient}' not in flavor map, querying Gemini...")
                compounds = self._enrich_ingredient_with_compounds(ingredient)
            
            all_compounds.update(compounds)
        return sorted(list(all_compounds))
    
    def _suggest_wine_type(self, dominant_flavors: List[str], compounds: List[str]) -> str:
        """Suggest wine type based on dominant flavors and compounds"""
        flavors_lower = [f.lower() for f in dominant_flavors]
        compounds_lower = [c.lower() for c in compounds]
        
        if any(f in flavors_lower for f in ['spicy', 'rich', 'heavy', 'umami', 'meaty']):
            return "Red"
        elif any(f in flavors_lower for f in ['light', 'acidic', 'citrus', 'fresh', 'crisp']):
            return "White"
        elif any(f in flavors_lower for f in ['sweet', 'dessert', 'creamy']):
            return "Dessert"
        elif any(f in flavors_lower for f in ['celebratory', 'bubbly']):
            return "Sparkling"
        else:
            if any('citral' in c or 'geraniol' in c or 'linalool' in c for c in compounds_lower):
                return "White"
            return "Red"
    
    def _extract_with_gemini(self, content: Any, is_image: bool = False, is_pdf_file: bool = False, pdf_file_path: str = None) -> Dict[str, Any]:
        """
        Use Gemini to extract dishes and wines from content
        
        Args:
            content: Text content, image bytes, PIL Image, or uploaded file reference
            is_image: Whether content is an image
            is_pdf_file: Whether content is a PDF file (uploaded via Files API)
            pdf_file_path: Path to PDF file (if is_pdf_file is True)
            
        Returns:
            Dictionary with 'dishes' and 'wines' arrays
        """
        prompt = """You are a culinary expert analyzing a menu, recipe book, or wine list document.

CRITICAL: Extract EVERY SINGLE dish and wine from this document. Do not skip any items. If the document contains 50 wines, return all 50. If it contains 100 dishes, return all 100. Be thorough and complete.

For each DISH, extract:
- dish_name: Name of the dish
- category: "salad", "appetizer", "main", or "dessert" (choose the most appropriate)
- key_ingredients: List of main ingredients (proteins, vegetables, herbs, spices, sauces)
- dominant_flavors: List of dominant flavor profiles (e.g., "Spicy", "Acidic", "Umami", "Sweet", "Bitter", "Salty", "Rich", "Light", "Heavy", "Creamy", "Smoky")

For each WINE (if any), extract:
- wine_name: Name of the wine
- type_name: "Red", "White", "Rosé", "Sparkling", or "Dessert"
- region: Wine region (if mentioned)
- winery: Winery name (if mentioned)
- country: Country of origin (if mentioned)
- grapes: List of grape varieties (if mentioned)

IMPORTANT:
- IGNORE: Beers, soft drinks, cocktails, spirits, and other non-wine beverages
- CRITICAL: Extract ALL items, not just a few. Count all dishes and wines in the document and extract every single one.
- If document contains only wines, return empty dishes array
- If document contains only dishes, return empty wines array
- If document contains both, extract BOTH completely - do not skip dishes when wines are present, and do not skip wines when dishes are present

Return ONLY valid JSON in this format (no markdown, no code blocks):
{
  "dishes": [
    {
      "dish_name": "Dish Name",
      "category": "main",
      "key_ingredients": ["ingredient1", "ingredient2", ...],
      "dominant_flavors": ["flavor1", "flavor2", ...]
    }
  ],
  "wines": [
    {
      "wine_name": "Wine Name",
      "type_name": "Red",
      "region": "Region Name",
      "winery": "Winery Name",
      "country": "Country Name",
      "grapes": ["grape1", "grape2"]
    }
  ]
}

Document: """
        
        # Retry logic for rate limiting (429 errors)
        max_retries = 3
        import time
        import re
        
        for attempt in range(max_retries):
            try:
                if is_pdf_file and pdf_file_path:
                    # Upload PDF file directly to Gemini Files API
                    # Based on debug logs: client.files.upload() accepts file parameter (path string, PathLike, or file object)
                    # Signature: (*, file: Union[str, os.PathLike[str], io.IOBase], config: ...)
                    uploaded_file = self.client.files.upload(file=pdf_file_path)
                    print(f"  Uploaded PDF file: {uploaded_file.name}")
                    
                    # Use uploaded file in prompt
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[prompt, uploaded_file],
                        config={
                            "temperature": 0.3,
                            "max_output_tokens": 32768,  # Increased for large wine lists (50+ wines)
                            "response_mime_type": "application/json"
                        }
                    )
                elif is_image:
                import PIL.Image
                import io
                if isinstance(content, bytes):
                    image = PIL.Image.open(io.BytesIO(content))
                else:
                    image = content  # Assume it's already a PIL Image
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt, image],
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 32768,  # Increased for large menus
                        "response_mime_type": "application/json"
                    }
                )
            else:
                full_prompt = prompt + str(content)
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": 32768,  # Increased for large menus
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
            response_text_cleaned = response_text.strip()
            if response_text_cleaned.startswith("```json"):
                response_text_cleaned = response_text_cleaned[7:]
            if response_text_cleaned.startswith("```"):
                response_text_cleaned = response_text_cleaned[3:]
            if response_text_cleaned.endswith("```"):
                response_text_cleaned = response_text_cleaned[:-3]
            response_text_cleaned = response_text_cleaned.strip()
            
            # Check for truncation indicators
            is_truncated = (
                response_text_cleaned.rstrip().endswith('"') and not response_text_cleaned.rstrip().endswith('"}') and not response_text_cleaned.rstrip().endswith('"]') or
                response_text_cleaned.rstrip().endswith('"dish_') or
                response_text_cleaned.rstrip().endswith('"wine_') or
                (response_text_cleaned.count('{') > response_text_cleaned.count('}')) or
                (response_text_cleaned.count('[') > response_text_cleaned.count(']'))
            )
            
            # Try to parse JSON, with fallback for truncated responses
            try:
                result = json.loads(response_text_cleaned)
            except json.JSONDecodeError as parse_error:
                # If truncated, try to extract partial data
                if is_truncated or "Unterminated string" in str(parse_error):
                    # Try to extract valid partial JSON
                    result = self._recover_partial_json(response_text_cleaned)
                else:
                    raise
            
            # Ensure required structure
            if "dishes" not in result:
                result["dishes"] = []
            if "wines" not in result:
                result["wines"] = []
            
            # Validate structure
            if not isinstance(result["dishes"], list):
                result["dishes"] = []
            if not isinstance(result["wines"], list):
                result["wines"] = []
            
            # Log extraction results
            dish_count = len(result["dishes"])
            wine_count = len(result["wines"])
            print(f"  Extracted {dish_count} dishes and {wine_count} wines")
            
            # Warn if extraction seems incomplete (only a few items from what might be a large document)
            if wine_count > 0 and wine_count < 5:
                print(f"  Warning: Only {wine_count} wines extracted - this might be incomplete. Check if document contains more wines.")
            if dish_count > 0 and dish_count < 3:
                print(f"  Warning: Only {dish_count} dishes extracted - this might be incomplete. Check if document contains more dishes.")
            
                return result
                
            except json.JSONDecodeError as e:
                print(f"  Error: Failed to parse JSON response: {e}")
                print(f"  Response text (first 500 chars): {response_text[:500] if 'response_text' in locals() else 'N/A'}")
                return {"dishes": [], "wines": []}
            except Exception as e:
                error_str = str(e)
                # Check for 429 rate limit error
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    # Extract retry delay from error message if available
                    retry_delay = 15  # Default 15 seconds
                    delay_match = re.search(r'retry in ([\d.]+)s', error_str, re.IGNORECASE)
                    if delay_match:
                        retry_delay = max(int(float(delay_match.group(1))) + 2, 15)  # Add 2s buffer, min 15s
                    
                    if attempt < max_retries - 1:
                        print(f"  ⚠️  API quota exceeded (429). Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                        print(f"  💡 Free tier limit: 20 requests/day. Consider upgrading or waiting until quota resets.")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"  ❌ API quota exceeded after {max_retries} attempts.")
                        print(f"  💡 Free tier limit: 20 requests/day. Please wait for quota reset or upgrade your plan.")
                        print(f"  📖 More info: https://ai.google.dev/gemini-api/docs/rate-limits")
                        raise ValueError(
                            f"Gemini API quota exceeded. Free tier allows 20 requests/day. "
                            f"Please wait for quota reset or upgrade your plan. "
                            f"Error: {error_str[:200]}"
                        )
                else:
                    # Non-quota error - don't retry
                    if attempt == 0:  # Only print full traceback on first attempt
                        print(f"  Error: Error extracting content: {e}")
                        import traceback
                        traceback.print_exc()
                    raise
            
        # Should not reach here, but just in case
        return {"dishes": [], "wines": []}
    
    def _recover_partial_json(self, json_text: str) -> Dict[str, Any]:
        """
        Attempt to recover partial JSON from truncated response
        
        Args:
            json_text: Truncated JSON text
            
        Returns:
            Dictionary with partial dishes/wines extracted
        """
        result = {"dishes": [], "wines": []}
        
        try:
            # Try to find complete dish entries before truncation
            import re
            
            # Find all complete dish entries (ending with })
            dish_pattern = r'\{\s*"dish_name"\s*:\s*"[^"]*",\s*"category"\s*:\s*"[^"]*",\s*"key_ingredients"\s*:\s*\[[^\]]*\],\s*"dominant_flavors"\s*:\s*\[[^\]]*\]\s*\}'
            dish_matches = re.findall(dish_pattern, json_text, re.DOTALL)
            
            for match in dish_matches:
                try:
                    dish = json.loads(match)
                    result["dishes"].append(dish)
                except:
                    continue
            
            # Find all complete wine entries
            wine_pattern = r'\{\s*"wine_name"\s*:\s*"[^"]*"[^}]*\}'
            wine_matches = re.findall(wine_pattern, json_text, re.DOTALL)
            
            for match in wine_matches:
                try:
                    wine = json.loads(match)
                    result["wines"].append(wine)
                except:
                    continue
                    
        except Exception as e:
            pass
        
        return result
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract dishes and wines from any file format
        
        Args:
            file_path: Path to file (txt, pdf, jpg, png, xlsx, csv)
            
        Returns:
            Dictionary with 'dishes' and 'wines' arrays (normalized)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_type = detect_file_type(file_path)
        source_file = str(path)
        
        # Route to appropriate extraction method
        if file_type == 'pdf':
            # Upload PDF directly to Gemini Files API (no text extraction)
            print(f"  Processing PDF file directly via Gemini Files API: {file_path}")
            extracted = self._extract_with_gemini(None, is_image=False, is_pdf_file=True, pdf_file_path=file_path)
        
        elif file_type in ['xlsx', 'xls']:
            # Convert Excel to text
            text_content = read_excel_content(file_path)
            extracted = self._extract_with_gemini(text_content, is_image=False)
        
        elif file_type == 'csv':
            # Convert CSV to text
            text_content = read_csv_content(file_path)
            extracted = self._extract_with_gemini(text_content, is_image=False)
        
        elif file_type in ['jpg', 'jpeg', 'png']:
            # Read image and send to Gemini
            with open(path, 'rb') as f:
                image_bytes = f.read()
            extracted = self._extract_with_gemini(image_bytes, is_image=True)
        
        elif file_type == 'txt':
            # Read text file
            with open(path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            extracted = self._extract_with_gemini(text_content, is_image=False)
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Normalize dishes
        normalized_dishes = []
        for dish in extracted.get("dishes", []):
            # #region agent log
            log_path = Path(".cursor/debug.log")
            try:
                import json as json_module
                dish_name_raw = dish.get("dish_name") or dish.get("name", "MISSING")
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json_module.dumps({"id":"log_dish_norm_1","timestamp":int(__import__('time').time()*1000),"location":"menu_extractor.py:485","message":"Normalizing dish","data":{"dish_name_raw":dish_name_raw,"has_key_ingredients":bool(dish.get("key_ingredients")),"ingredient_count":len(dish.get("key_ingredients", []))},"runId":"run1","hypothesisId":"A"}) + "\n")
            except: pass
            # #endregion
            
            # Build compounds from ingredients
            ingredients = dish.get("key_ingredients", [])
            
            # Check if dish has ingredients
            if not ingredients or len(ingredients) == 0:
                # Tag dish with no flavor profile
                normalized_dish = normalize_dish_format(
                    dish,
                    source_file=source_file
                )
                normalized_dish["compounds"] = []
                normalized_dish["suggested_wine_type"] = "Unknown"
                normalized_dish["flavor_profile_note"] = "No Flavour Profile could be made, as no ingredients were listed"
                normalized_dishes.append(normalized_dish)
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json_module.dumps({"id":"log_dish_norm_2","timestamp":int(__import__('time').time()*1000),"location":"menu_extractor.py:500","message":"Dish normalized (no ingredients)","data":{"dish_id":normalized_dish.get("dish_id"),"name":normalized_dish.get("name")},"runId":"run1","hypothesisId":"A"}) + "\n")
                except: pass
                # #endregion
                continue
            
            # Build compounds from ingredients (will query Gemini if needed)
            compounds = self._build_compounds_for_dish(ingredients)
            
            # Suggest wine type
            dominant_flavors = dish.get("dominant_flavors", [])
            suggested_wine_type = self._suggest_wine_type(dominant_flavors, compounds)
            
            # Normalize dish format
            normalized_dish = normalize_dish_format(
                dish,
                source_file=source_file
            )
            
            # Add computed fields
            normalized_dish["compounds"] = compounds
            normalized_dish["suggested_wine_type"] = suggested_wine_type
            
            # #region agent log
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json_module.dumps({"id":"log_dish_norm_3","timestamp":int(__import__('time').time()*1000),"location":"menu_extractor.py:520","message":"Dish normalized (with ingredients)","data":{"dish_id":normalized_dish.get("dish_id"),"name":normalized_dish.get("name"),"compound_count":len(compounds)},"runId":"run1","hypothesisId":"A"}) + "\n")
            except: pass
            # #endregion
            
            normalized_dishes.append(normalized_dish)
        
        # Normalize wines and remove duplicates
        normalized_wines = []
        seen_wine_names = set()
        # #region agent log
        log_path = Path(".cursor/debug.log")
        try:
            import json as json_module
            raw_wines = extracted.get("wines", [])
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json_module.dumps({"id":"log_wine_norm_1","timestamp":int(__import__('time').time()*1000),"location":"menu_extractor.py:544","message":"Normalizing wines","data":{"raw_wine_count":len(raw_wines)},"runId":"run1","hypothesisId":"E"}) + "\n")
        except: pass
        # #endregion
        
        for wine in extracted.get("wines", []):
            normalized_wine = normalize_wine_format(wine)
            wine_name = normalized_wine.get("wine_name", "").lower().strip()
            
            # Check for duplicates
            if wine_name and wine_name in seen_wine_names:
                # #region agent log
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json_module.dumps({"id":"log_wine_norm_2","timestamp":int(__import__('time').time()*1000),"location":"menu_extractor.py:555","message":"Duplicate wine skipped","data":{"wine_name":wine_name},"runId":"run1","hypothesisId":"E"}) + "\n")
                except: pass
                # #endregion
                continue
            
            seen_wine_names.add(wine_name)
            normalized_wines.append(normalized_wine)
        
        # #region agent log
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json_module.dumps({"id":"log_wine_norm_3","timestamp":int(__import__('time').time()*1000),"location":"menu_extractor.py:565","message":"Wine normalization complete","data":{"normalized_count":len(normalized_wines),"duplicates_removed":len(extracted.get("wines", [])) - len(normalized_wines)},"runId":"run1","hypothesisId":"E"}) + "\n")
        except: pass
        # #endregion
        
        return {
            "dishes": normalized_dishes,
            "wines": normalized_wines,
            "source_file": source_file
        }
    
    def extract_from_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Extract dishes and wines from multiple files
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary with combined 'dishes' and 'wines' arrays
        """
        all_dishes = []
        all_wines = []
        source_files = []
        
        for file_path in file_paths:
            try:
                result = self.extract_from_file(file_path)
                all_dishes.extend(result.get("dishes", []))
                all_wines.extend(result.get("wines", []))
                source_files.append(result.get("source_file", file_path))
            except Exception as e:
                print(f"  Warning: Failed to process {file_path}: {e}")
                continue
        
        return {
            "dishes": all_dishes,
            "wines": all_wines,
            "source_files": source_files
        }
    
    def detect_wines(self, extraction_result: Dict[str, Any]) -> bool:
        """
        Detect if wines are present in extraction result
        
        Args:
            extraction_result: Result from extract_from_file or extract_from_files
            
        Returns:
            True if wines are present, False otherwise
        """
        wines = extraction_result.get("wines", [])
        return len(wines) > 0
