"""
Menu processor wrapper module
Enhanced menu processing with multi-format support and wine detection
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import json

# Import the existing MenuProfiler for backward compatibility
sys.path.insert(0, str(Path(__file__).parent.parent))
from batch_profiler import MenuProfiler

# Import new extractor
from core.menu_extractor import MenuExtractor
from utils.config import DEFAULT_MENU_PROFILE_PATH


class MenuProcessor:
    """
    Enhanced menu processor with multi-format support
    Can process files in various formats and extract dishes and wines
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3-flash-preview"):
        """
        Initialize the Menu Processor
        
        Args:
            api_key: Google AI API key (if None, reads from GOOGLE_AI_API_KEY env var)
            model_name: Gemini model to use
        """
        self.profiler = MenuProfiler(api_key=api_key, model_name=model_name)
        self.extractor = MenuExtractor(api_key=api_key, model_name=model_name)
    
    def process_files(
        self,
        file_paths: List[str],
        extract_wines: bool = True
    ) -> Dict[str, Any]:
        """
        Process multiple files in any format and extract dishes and wines
        
        Args:
            file_paths: List of file paths (txt, pdf, jpg, png, xlsx, csv)
            extract_wines: Whether to extract wines (default: True)
            
        Returns:
            Dictionary with:
            - 'dishes': List of normalized dish dictionaries
            - 'wines': List of normalized wine dictionaries (if extract_wines=True)
            - 'has_wines': Boolean indicating if wines were found
            - 'source_files': List of processed file paths
        """
        # Filter out invalid file paths
        valid_paths = []
        for path in file_paths:
            path_obj = Path(path)
            if path_obj.exists():
                valid_paths.append(path)
            else:
                print(f"  Warning: File not found: {path}")
        
        if not valid_paths:
            return {
                "dishes": [],
                "wines": [],
                "has_wines": False,
                "menu_profile": {},
                "source_files": []
            }
        
        result = self.extractor.extract_from_files(valid_paths)
        
        # Convert dishes list to menu profile format (dict by dish_id)
        menu_profile = {}
        for dish in result.get("dishes", []):
            dish_id = dish.get("dish_id")
            if dish_id:
                menu_profile[dish_id] = dish
        
        return {
            "dishes": result.get("dishes", []),
            "wines": result.get("wines", []) if extract_wines else [],
            "has_wines": len(result.get("wines", [])) > 0,
            "menu_profile": menu_profile,
            "source_files": result.get("source_files", [])
        }
    
    def process_file(
        self,
        file_path: str,
        extract_wines: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single file and extract dishes and wines
        
        Args:
            file_path: Path to file (txt, pdf, jpg, png, xlsx, csv)
            extract_wines: Whether to extract wines (default: True)
            
        Returns:
            Dictionary with dishes, wines, and metadata
        """
        return self.process_files([file_path], extract_wines=extract_wines)
    
    def detect_wines_in_files(self, file_paths: List[str]) -> bool:
        """
        Check if wines are present in the files
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            True if wines are detected, False otherwise
        """
        result = self.extractor.extract_from_files(file_paths)
        return self.extractor.detect_wines(result)
    
    def process_menu_images(self, image_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Process menu images and return menu profile (backward compatibility)
        
        Args:
            image_paths: List of paths to menu/recipe images
            
        Returns:
            Dictionary mapping dish_id to dish profile
        """
        # Use new extractor for better multi-dish extraction
        result = self.process_files(image_paths, extract_wines=False)
        return result.get("menu_profile", {})
    
    def process_recipes_folder(self, recipes_folder: Path = None) -> Dict[str, Dict[str, Any]]:
        """
        Process all recipes in a folder
        
        Args:
            recipes_folder: Path to recipes folder (default: "recipes")
            
        Returns:
            Dictionary mapping dish_id to dish profile
        """
        if recipes_folder is None:
            recipes_folder = Path("recipes")
        
        return self.profiler.process_recipes_folder(recipes_folder)
    
    def load_menu_profile(self, menu_profile_path: Path = None) -> Dict[str, Dict[str, Any]]:
        """
        Load existing menu profile from JSON file
        
        Args:
            menu_profile_path: Path to menu profile JSON (default from config)
            
        Returns:
            Dictionary mapping dish_id to dish profile
        """
        import json
        from utils.config import DEFAULT_MENU_PROFILE_PATH
        
        if menu_profile_path is None:
            menu_profile_path = DEFAULT_MENU_PROFILE_PATH
        
        path = Path(menu_profile_path)
        if not path.exists():
            raise FileNotFoundError(f"Menu profile not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_menu_profile(
        self, 
        menu_profile: Dict[str, Dict[str, Any]], 
        output_path: Path = None
    ):
        """
        Save menu profile to JSON file
        
        Args:
            menu_profile: Dictionary mapping dish_id to dish profile
            output_path: Path to output JSON file (default from config)
        """
        from utils.config import DEFAULT_MENU_PROFILE_PATH
        
        if output_path is None:
            output_path = DEFAULT_MENU_PROFILE_PATH
        
        self.profiler.save_menu_profile(menu_profile, output_path)
    
    def get_dish_compounds(self, dish_id: str, menu_profile: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Get flavor compounds for a specific dish
        
        Args:
            dish_id: Dish identifier
            menu_profile: Menu profile dictionary
            
        Returns:
            List of compound names
        """
        dish = menu_profile.get(dish_id)
        if dish:
            return dish.get("compounds", [])
        return []
    
    def get_combination_compounds(
        self, 
        combination: List[str], 
        menu_profile: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Get aggregated flavor compounds for a plate combination
        
        Args:
            combination: List of dish_ids
            menu_profile: Menu profile dictionary
            
        Returns:
            List of unique compound names from all dishes in combination
        """
        all_compounds = set()
        
        for dish_id in combination:
            compounds = self.get_dish_compounds(dish_id, menu_profile)
            all_compounds.update(compounds)
        
        return sorted(list(all_compounds))
    
    def save_extracted_data(
        self,
        extraction_result: Dict[str, Any],
        menu_output_path: Optional[Path] = None,
        wines_output_path: Optional[Path] = None
    ):
        """
        Save extracted dishes and wines to files
        
        Args:
            extraction_result: Result from process_files()
            menu_output_path: Path to save menu profile (default from config)
            wines_output_path: Path to save wines (optional)
        """
        # Save menu profile
        menu_profile = extraction_result.get("menu_profile", {})
        if menu_profile:
            if menu_output_path is None:
                menu_output_path = Path(DEFAULT_MENU_PROFILE_PATH)
            self.save_menu_profile(menu_profile, menu_output_path)
        
        # Save wines if provided
        wines = extraction_result.get("wines", [])
        if wines and wines_output_path:
            with open(wines_output_path, 'w', encoding='utf-8') as f:
                json.dump(wines, f, indent=2, ensure_ascii=False)