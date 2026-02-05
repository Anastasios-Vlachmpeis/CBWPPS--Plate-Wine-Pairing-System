"""
Wine Sommelier wrapper module
Wraps WineSommelier for use in core modules while maintaining backward compatibility
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Import the existing WineSommelier
sys.path.insert(0, str(Path(__file__).parent.parent))
from wine_sommelier import WineSommelier


class WineSommelierWrapper:
    """
    Wrapper around WineSommelier that provides a consistent interface
    for use in core modules, especially for compound-based wine searching
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3-flash-preview"):
        """
        Initialize the Wine Sommelier Wrapper
        
        Args:
            api_key: Google AI API key (if None, reads from GOOGLE_AI_API_KEY env var)
            model_name: Gemini model to use
        """
        self.sommelier = WineSommelier(api_key=api_key, model_name=model_name)
    
    def search_wines_by_compounds(
        self, 
        compounds: List[str], 
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search wines by flavor compounds (reuses WineSommelier logic)
        
        Args:
            compounds: List of compound names to search for
            max_results: Maximum number of results to return (None = all)
            
        Returns:
            List of wine match dictionaries with 'wine', 'shared_compounds', 'match_count'
        """
        matches = self.sommelier.search_wines_by_compounds(compounds)
        
        if max_results is not None:
            matches = matches[:max_results]
        
        return matches
    
    def get_wine_by_id(self, wine_id: int) -> Optional[Dict[str, Any]]:
        """
        Get full wine details by ID
        
        Args:
            wine_id: Wine ID
            
        Returns:
            Wine dictionary or None if not found
        """
        return self.sommelier.get_wine_by_id(wine_id)
    
    def get_all_wines(self) -> List[Dict[str, Any]]:
        """
        Get all wines from the internal database
        
        Returns:
            List of all wine dictionaries
        """
        return self.sommelier.wines
    
    def recommend_wine_for_dish(
        self,
        dish_description: Optional[str] = None,
        dish_image: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Recommend wines for a single dish (reuses WineSommelier.recommend)
        
        Args:
            dish_description: Text description of the dish
            dish_image: Image bytes or path to image file
            
        Returns:
            Recommendation dictionary with top_matches, reasoning, etc.
        """
        return self.sommelier.recommend(
            dish_description=dish_description,
            dish_image=dish_image
        )
    
    def find_best_wines_for_compounds(
        self,
        compounds: List[str],
        wines: List[Dict[str, Any]] = None,
        max_wines: int = 3
    ) -> List[int]:
        """
        Find best wines for a set of compounds from a given wine list
        
        Args:
            compounds: List of compound names
            wines: List of wines to search (if None, uses internal database)
            max_wines: Maximum number of wines to return
            
        Returns:
            List of wine IDs
        """
        if wines is None:
            # Use internal database
            matches = self.search_wines_by_compounds(compounds, max_results=max_wines * 10)
            wine_ids = [match["wine"]["wine_id"] for match in matches[:max_wines]]
        else:
            # Search in provided wine list
            compounds_set = set(compounds)
            matches = []
            
            for wine in wines:
                wine_compounds = set(wine.get("flavor_compounds", []))
                shared = compounds_set.intersection(wine_compounds)
                if shared:
                    matches.append({
                        "wine": wine,
                        "shared_compounds": list(shared),
                        "match_count": len(shared)
                    })
            
            # Sort by match count
            matches.sort(key=lambda x: x["match_count"], reverse=True)
            wine_ids = [match["wine"]["wine_id"] for match in matches[:max_wines]]
        
        return wine_ids
