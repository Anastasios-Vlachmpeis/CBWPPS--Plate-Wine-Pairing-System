"""
Wine list management module
Handles loading and merging wine lists from different sources
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.file_parsers import (
    parse_csv_wine_list,
    parse_json_wine_list,
    parse_xlsx_wine_list,
    detect_file_type,
    extract_text_from_pdf
)
from utils.config import DEFAULT_WINES_PATH


class WineManager:
    """
    Manages wine lists from files and enriches them with flavor compounds
    """
    
    def __init__(self, internal_wines_path: Path = None):
        """
        Initialize the Wine Manager
        
        Args:
            internal_wines_path: Path to internal wines JSON file (default from config)
        """
        if internal_wines_path is None:
            internal_wines_path = DEFAULT_WINES_PATH
        self.internal_wines_path = Path(internal_wines_path)
        self.ingredient_flavor_map = None
        self._load_ingredient_map()
    
    def _load_ingredient_map(self):
        """Load ingredient flavor map for compound mapping"""
        ingredient_path = Path("processed_data") / "ingredient_flavor_map.json"
        if ingredient_path.exists():
            with open(ingredient_path, 'r', encoding='utf-8') as f:
                self.ingredient_flavor_map = json.load(f)
    
    def load_wines(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Load wines from one or more files (JSON, CSV, PDF, or XLSX)
        
        Args:
            file_paths: List of paths to wine list files
            
        Returns:
            List of normalized wine dictionaries
        """
        all_wines = []
        
        for file_path in file_paths:
            file_type = detect_file_type(file_path)
            
            try:
                if file_type == 'json':
                    wines = parse_json_wine_list(file_path)
                elif file_type == 'csv':
                    wines = parse_csv_wine_list(file_path)
                elif file_type == 'xlsx':
                    wines = parse_xlsx_wine_list(file_path)
                elif file_type == 'pdf':
                    wines = self._extract_wines_with_gemini(file_path)
                else:
                    raise ValueError(f"Unsupported file type: {file_type}. Supported: json, csv, xlsx, pdf")
            except ImportError as e:
                raise ImportError(f"Missing required library for {file_type} parsing: {e}. "
                                  f"Please install with: pip install {e.name}")
            except Exception as e:
                raise ValueError(f"Error parsing {file_type} file '{file_path}': {e}")
            
            # Normalize all wines
            normalized = [self.normalize_wine_format(wine) for wine in wines]
            all_wines.extend(normalized)
        
        return all_wines
    
    def enrich_wines_with_flavors(
        self,
        wines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use Gemini to get wine composition and map flavors to compounds
        
        Args:
            wines: List of wine dictionaries (should have wine_name, type_name, etc.)
            
        Returns:
            List of wines enriched with flavor_compounds
        """
        import google.genai as genai
        import re
        
        # Get API key
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if api_key is None:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv("GOOGLE_AI_API_KEY")
            except ImportError:
                pass
        
        if not api_key:
            print("Warning: GOOGLE_AI_API_KEY not found. Skipping flavor enrichment.")
            return wines
        
        # Configure Gemini
        client = genai.Client(api_key=api_key)
        model_name = "gemini-3-flash-preview"
        
        enriched_wines = []
        
        for wine in wines:
            wine_name = wine.get("wine_name", "Unknown")
            type_name = wine.get("type_name", "Unknown")
            grapes = wine.get("grapes", [])
            region = wine.get("region", "")
            winery = wine.get("winery", "")
            
            # Build wine description
            wine_desc = f"{wine_name}"
            if winery:
                wine_desc += f" from {winery}"
            if region:
                wine_desc += f", {region}"
            if grapes:
                wine_desc += f". Grapes: {', '.join(grapes)}"
            wine_desc += f". Type: {type_name}"
            
            prompt = f"""You are a wine expert. For this wine, provide:
1. Grape varieties (if not already provided)
2. Key flavor compounds found in this wine based on its grapes, region, and style

Wine: {wine_desc}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "grapes": ["grape1", "grape2"],
  "flavor_compounds": ["compound1", "compound2", "compound3"]
}}

If grapes are already provided, use those. Otherwise, identify the most likely grape varieties.
For flavor compounds, use standard chemical names (e.g., "Citral", "Geraniol", "Linalool")."""
            
            try:
                response = client.models.generate_content(
                    model=model_name,
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
                else:
                    response_text = str(response).strip()
                
                # Clean JSON
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                # Parse JSON
                result = json.loads(response_text)
                
                # Update wine with enriched data
                enriched_wine = wine.copy()
                if "grapes" in result and result["grapes"]:
                    enriched_wine["grapes"] = result["grapes"]
                
                # Map grapes to compounds using ingredient_flavor_map
                compounds = set()
                if self.ingredient_flavor_map:
                    for grape in enriched_wine.get("grapes", []):
                        grape_cleaned = self._clean_ingredient_name(grape)
                        # Try to find grape in ingredient map
                        for ingredient_name, data in self.ingredient_flavor_map.items():
                            if data.get("cleaned_name") == grape_cleaned:
                                compounds.update(data.get("compounds", []))
                                break
                
                # Add compounds from Gemini (if any)
                if "flavor_compounds" in result:
                    compounds.update(result["flavor_compounds"])
                
                enriched_wine["flavor_compounds"] = list(compounds)
                enriched_wines.append(enriched_wine)
                
            except Exception as e:
                # If enrichment fails, use original wine
                print(f"Warning: Failed to enrich wine {wine_name}: {e}")
                enriched_wines.append(wine)
        
        return enriched_wines
    
    def _clean_ingredient_name(self, name: str) -> str:
        """Clean ingredient name for matching"""
        import re
        name = name.lower().strip()
        name = re.sub(r'[^a-z0-9\s]', '', name)
        name = re.sub(r'[_\s]+', ' ', name)
        return name.strip()
    
    def normalize_wine_format(self, wine_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize wine data to standard format
        
        Expected standard format:
        {
            'wine_id': int,
            'wine_name': str,
            'type_name': str,
            'body_name': str,
            'acidity_name': str,
            'grapes': List[str],
            'country': str,
            'region': str,
            'winery': str,
            'flavor_compounds': List[str],
            'harmonize': List[str],
            ...
        }
        
        Args:
            wine_data: Wine data dictionary (may have different field names)
            
        Returns:
            Normalized wine dictionary
        """
        normalized = {}
        
        # Map common field name variations
        field_mapping = {
            'wine_id': ['wine_id', 'id', 'wineid', 'wine_id'],
            'wine_name': ['wine_name', 'name', 'winename', 'wine_name', 'title'],
            'type_name': ['type_name', 'type', 'winetype', 'wine_type', 'color'],
            'body_name': ['body_name', 'body', 'winebody', 'wine_body'],
            'acidity_name': ['acidity_name', 'acidity', 'wineacidity', 'wine_acidity'],
            'grapes': ['grapes', 'grape', 'varietal', 'varietals'],
            'country': ['country', 'country_name', 'origin'],
            'region': ['region', 'region_name', 'appellation'],
            'winery': ['winery', 'winery_name', 'producer', 'maker'],
            'flavor_compounds': ['flavor_compounds', 'compounds', 'flavor_compounds'],
            'harmonize': ['harmonize', 'harmonizes', 'pairings', 'food_pairings'],
        }
        
        # Try to find each field
        for standard_field, possible_fields in field_mapping.items():
            value = None
            for field in possible_fields:
                # Try exact match (case-insensitive)
                for key in wine_data.keys():
                    if key.lower() == field.lower():
                        value = wine_data[key]
                        break
                if value is not None:
                    break
            
            # Use default if not found
            if value is None:
                if standard_field in ['grapes', 'flavor_compounds', 'harmonize']:
                    value = []
                elif standard_field == 'wine_id':
                    # Generate a temporary ID if missing
                    value = hash(wine_data.get('wine_name', str(wine_data)))
                else:
                    value = 'Unknown'
            
            normalized[standard_field] = value
        
        # Ensure grapes is a list
        if not isinstance(normalized['grapes'], list):
            if isinstance(normalized['grapes'], str):
                normalized['grapes'] = [g.strip() for g in normalized['grapes'].split(',') if g.strip()]
            else:
                normalized['grapes'] = []
        
        # Ensure flavor_compounds is a list
        if not isinstance(normalized['flavor_compounds'], list):
            normalized['flavor_compounds'] = []
        
        # Ensure harmonize is a list
        if not isinstance(normalized['harmonize'], list):
            if isinstance(normalized['harmonize'], str):
                normalized['harmonize'] = [h.strip() for h in normalized['harmonize'].split(',') if h.strip()]
            else:
                normalized['harmonize'] = []
        
        # Copy any additional fields
        for key, value in wine_data.items():
            if key.lower() not in [f.lower() for f in field_mapping.keys()]:
                normalized[key] = value
        
        return normalized
    
    def _extract_wines_with_gemini(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Use Gemini to extract wines from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of wine dictionaries
        """
        try:
            import google.genai as genai
            
            # Get API key
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            if api_key is None:
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    api_key = os.getenv("GOOGLE_AI_API_KEY")
                except ImportError:
                    pass
            
            if not api_key:
                raise ValueError("GOOGLE_AI_API_KEY not found. Cannot extract wines from PDF.")
            
            # Extract text from PDF
            text_content = extract_text_from_pdf(pdf_path)
            
            # Configure Gemini
            client = genai.Client(api_key=api_key)
            model_name = "gemini-3-flash-preview"
            
            prompt = """You are a wine expert analyzing a wine list document.

Extract ALL wines from this document. For each wine, extract:
- wine_name: Name of the wine (required)
- type_name: "Red", "White", "Rosé", "Sparkling", or "Dessert" (required)
- region: Wine region (if mentioned)
- winery: Winery name (if mentioned)
- country: Country of origin (if mentioned)
- grapes: List of grape varieties (if mentioned)

IGNORE: Beers, soft drinks, cocktails, spirits, and other non-wine beverages
IGNORE: Food items, menu descriptions, prices, page numbers, headers, footers

Return ONLY valid JSON in this format (no markdown, no code blocks):
{
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
            
            full_prompt = prompt + text_content[:50000]  # Limit to avoid token limits
            
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 8192,
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
            
            # Clean JSON
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Try to parse JSON with error recovery
            try:
                result = json.loads(response_text)
                wines = result.get("wines", [])
                return wines
            except json.JSONDecodeError as parse_error:
                # Try to recover partial JSON
                wines = self._recover_partial_json(response_text)
                if wines:
                    return wines
                raise ValueError(f"Failed to parse Gemini JSON response: {parse_error}")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini JSON response: {e}")
        except Exception as e:
            raise ValueError(f"Failed to extract wines from PDF: {e}")
    
    
    def _recover_partial_json(self, json_text: str) -> List[Dict[str, Any]]:
        """
        Attempt to recover partial JSON from truncated or malformed response
        
        Args:
            json_text: JSON text that failed to parse
            
        Returns:
            List of wine dictionaries extracted from valid portions
        """
        wines = []
        import re
        
        try:
            # Strategy: Extract wine_name and type_name directly using regex groups
            # This is more robust than trying to parse incomplete JSON objects
            # First try to find wines array - use greedy match to get all content until end or closing bracket
            wines_array_match = re.search(r'"wines"\s*:\s*\[(.*)', json_text, re.DOTALL)
            if wines_array_match:
                wines_content = wines_array_match.group(1)
                # Use non-greedy match to avoid matching across multiple wine objects
                # Also handle cases where wine object might be incomplete (no closing brace)
                wine_pattern = r'\{\s*"wine_name"\s*:\s*"([^"]+)"[^}]*?"type_name"\s*:\s*"([^"]+)"'
                matches = list(re.finditer(wine_pattern, wines_content, re.DOTALL))
            else:
                # Fallback: Find individual wine objects anywhere
                wine_pattern = r'\{\s*"wine_name"\s*:\s*"([^"]+)"[^}]*?"type_name"\s*:\s*"([^"]+)"'
                matches = list(re.finditer(wine_pattern, json_text, re.DOTALL))
            
            for entry in matches:
                try:
                    # Extract from regex groups (more robust than parsing JSON)
                    wine_name = entry.group(1)
                    type_name = entry.group(2)
                    wine = {"wine_name": wine_name, "type_name": type_name}
                    
                    # Try to extract additional fields if present
                    full_match = entry.group(0)
                    if '"region"' in full_match:
                        region_match = re.search(r'"region"\s*:\s*"([^"]+)"', full_match)
                        if region_match:
                            wine["region"] = region_match.group(1)
                    if '"winery"' in full_match:
                        winery_match = re.search(r'"winery"\s*:\s*"([^"]+)"', full_match)
                        if winery_match:
                            wine["winery"] = winery_match.group(1)
                    if '"country"' in full_match:
                        country_match = re.search(r'"country"\s*:\s*"([^"]+)"', full_match)
                        if country_match:
                            wine["country"] = country_match.group(1)
                    if '"grapes"' in full_match:
                        grapes_match = re.search(r'"grapes"\s*:\s*\[(.*?)\]', full_match, re.DOTALL)
                        if grapes_match:
                            grapes_str = grapes_match.group(1)
                            grapes = [g.strip().strip('"') for g in grapes_str.split(',') if g.strip()]
                            wine["grapes"] = grapes
                    
                    wines.append(wine)
                except Exception as e:
                    continue
        except Exception as e:
            pass
        
        return wines