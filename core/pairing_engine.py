"""
Pairing engine module
Pairs wines with individual dishes based on flavor compounds
"""

from typing import List, Dict, Any, Set, Optional
from pathlib import Path
from .wine_sommelier_wrapper import WineSommelierWrapper
from .menu_processor import MenuProcessor
from utils.config import DEFAULT_MAX_WINES_PER_COMBO


class PairingEngine:
    """
    Pairs wines with individual dishes based on molecular flavor matching
    """
    
    def __init__(
        self, 
        sommelier: Optional[WineSommelierWrapper] = None,
        menu_processor: Optional[MenuProcessor] = None,
        max_wines_per_dish: int = None
    ):
        """
        Initialize the Pairing Engine
        
        Args:
            sommelier: WineSommelierWrapper instance (creates new if None)
            menu_processor: MenuProcessor instance (creates new if None)
            max_wines_per_dish: Maximum wines per dish (default from config)
        """
        self.sommelier = sommelier or WineSommelierWrapper()
        self.menu_processor = menu_processor or MenuProcessor()
        self.max_wines_per_dish = max_wines_per_dish or DEFAULT_MAX_WINES_PER_COMBO
    
    def _get_dish_compounds(
        self, 
        dish_id: str, 
        menu_profile: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Get flavor compounds for a single dish
        
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
    
    def pair_wines_to_dish(
        self,
        dish_id: str,
        wines: List[Dict[str, Any]],
        menu_profile: Dict[str, Dict[str, Any]],
        max_wines: int = None
    ) -> List[int]:
        """
        Find up to max_wines best wines for a single dish
        
        Args:
            dish_id: Dish identifier
            wines: List of wine dictionaries to search
            menu_profile: Menu profile dictionary
            max_wines: Maximum wines to return (uses default if None)
            
        Returns:
            List of wine IDs (up to max_wines)
        """
        if max_wines is None:
            max_wines = self.max_wines_per_dish
        
        if not dish_id or not wines:
            return []
        
        # Get compounds for this dish
        compounds = self._get_dish_compounds(dish_id, menu_profile)
        
        if not compounds:
            return []
        
        # Find best wines using compound matching
        wine_ids = self.sommelier.find_best_wines_for_compounds(
            compounds=compounds,
            wines=wines,
            max_wines=max_wines
        )
        
        return wine_ids
    
    def pair_wines_to_dishes(
        self,
        dishes: List[Dict[str, Any]],
        wines: List[Dict[str, Any]],
        menu_profile: Dict[str, Dict[str, Any]] = None,
        max_wines_per_dish: int = None
    ) -> Dict[str, List[int]]:
        """
        Pair wines to individual dishes
        
        Args:
            dishes: List of dish dictionaries (or menu_profile dict)
            wines: List of wine dictionaries
            menu_profile: Menu profile dictionary (if dishes is not a dict)
            max_wines_per_dish: Maximum wines per dish (uses default if None)
            
        Returns:
            Dictionary mapping dish_id -> list of wine_ids (up to max_wines_per_dish)
        """
        if max_wines_per_dish is None:
            max_wines_per_dish = self.max_wines_per_dish
        
        # Handle different input formats
        if isinstance(dishes, dict):
            # dishes is actually menu_profile
            menu_profile = dishes
            dish_ids = list(menu_profile.keys())
        else:
            # dishes is a list of dish dicts
            if menu_profile is None:
                # Create menu_profile from dishes list
                menu_profile = {dish.get("dish_id"): dish for dish in dishes if dish.get("dish_id")}
            dish_ids = [dish.get("dish_id") for dish in dishes if dish.get("dish_id")]
        
        pairings = {}
        
        for dish_id in dish_ids:
            wine_ids = self.pair_wines_to_dish(
                dish_id=dish_id,
                wines=wines,
                menu_profile=menu_profile,
                max_wines=max_wines_per_dish
            )
            pairings[dish_id] = wine_ids
        
        return pairings
    
    
    def calculate_pairing_score(
        self,
        dish_id: str,
        wine: Dict[str, Any],
        menu_profile: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate a pairing score between a dish and a wine
        
        Args:
            dish_id: Dish identifier
            wine: Wine dictionary
            menu_profile: Menu profile dictionary
            
        Returns:
            Pairing score (0-1, higher is better)
        """
        # Get compounds from dish
        dish_compounds = set(self._get_dish_compounds(dish_id, menu_profile))
        wine_compounds = set(wine.get("flavor_compounds", []))
        
        if not dish_compounds:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(dish_compounds & wine_compounds)
        union = len(dish_compounds | wine_compounds)
        
        if union == 0:
            return 0.0
        
        return intersection / union
