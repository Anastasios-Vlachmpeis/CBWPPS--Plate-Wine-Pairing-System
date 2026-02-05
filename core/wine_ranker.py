"""
Wine ranking module
Ranks wines based on pairing frequency and match quality
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict


class WineRanker:
    """
    Ranks wines based on number of dishes matched and match quality
    """
    
    def __init__(self):
        """Initialize the Wine Ranker"""
        pass
    
    def rank_by_pairing_frequency(
        self,
        pairings: Dict[str, List[int]]
    ) -> Dict[int, int]:
        """
        Count how many dishes each wine pairs with
        
        Args:
            pairings: Dictionary mapping dish_id -> list of wine_ids
            
        Returns:
            Dictionary mapping wine_id -> pairing count
        """
        frequency = defaultdict(int)
        
        for dish_id, wine_ids in pairings.items():
            for wine_id in wine_ids:
                frequency[wine_id] += 1
        
        return dict(frequency)
    
    def rank_by_match_quality(
        self,
        pairings: Dict[str, List[int]],
        wines: List[Dict[str, Any]],
        menu_profile: Dict[str, Dict[str, Any]],
        pairing_engine = None
    ) -> Dict[int, float]:
        """
        Calculate average match quality score for each wine
        
        Args:
            pairings: Dictionary mapping dish_id -> list of wine_ids
            wines: List of wine dictionaries
            menu_profile: Menu profile dictionary
            pairing_engine: PairingEngine instance for calculating scores (optional)
            
        Returns:
            Dictionary mapping wine_id -> average match quality score (0-1)
        """
        from .pairing_engine import PairingEngine
        
        if pairing_engine is None:
            pairing_engine = PairingEngine()
        
        # Create wine lookup
        wine_dict = {w.get("wine_id"): w for w in wines if w.get("wine_id") is not None}
        
        # Calculate quality scores for each pairing
        quality_scores = defaultdict(list)
        
        for dish_id, wine_ids in pairings.items():
            for wine_id in wine_ids:
                wine = wine_dict.get(wine_id)
                if wine:
                    score = pairing_engine.calculate_pairing_score(
                        dish_id=dish_id,
                        wine=wine,
                        menu_profile=menu_profile
                    )
                    quality_scores[wine_id].append(score)
        
        # Calculate average quality per wine
        avg_quality = {}
        for wine_id, scores in quality_scores.items():
            avg_quality[wine_id] = sum(scores) / len(scores) if scores else 0.0
        
        return avg_quality
    
    def rank_wines(
        self,
        wines: List[Dict[str, Any]],
        pairings: Dict[str, List[int]],
        menu_profile: Dict[str, Dict[str, Any]],
        pairing_engine = None,
        weight_frequency: float = 0.6,
        weight_quality: float = 0.4
    ) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        Rank wines by number of dishes matched and match quality
        
        Args:
            wines: List of wine dictionaries
            pairings: Dictionary mapping dish_id -> list of wine_ids
            menu_profile: Menu profile dictionary
            pairing_engine: PairingEngine instance (optional)
            weight_frequency: Weight for pairing frequency (default 0.6)
            weight_quality: Weight for match quality (default 0.4)
            
        Returns:
            List of (wine_id, combined_score, wine_dict) tuples, sorted by score descending
        """
        # Normalize weights
        total_weight = weight_frequency + weight_quality
        weight_frequency /= total_weight
        weight_quality /= total_weight
        
        # Get frequency rankings (number of dishes matched)
        frequency_scores = self.rank_by_pairing_frequency(pairings)
        
        # Normalize frequency scores (0-1)
        if frequency_scores:
            max_freq = max(frequency_scores.values())
            if max_freq > 0:
                frequency_scores = {wid: score / max_freq for wid, score in frequency_scores.items()}
        
        # Get quality rankings (average match quality)
        quality_scores = self.rank_by_match_quality(
            pairings=pairings,
            wines=wines,
            menu_profile=menu_profile,
            pairing_engine=pairing_engine
        )
        
        # Create wine lookup
        wine_dict = {w.get("wine_id"): w for w in wines if w.get("wine_id") is not None}
        
        # Combine scores
        ranked_wines = []
        
        # Get all wine IDs that appear in pairings
        all_wine_ids = set(frequency_scores.keys())
        all_wine_ids.update(quality_scores.keys())
        
        for wine_id in all_wine_ids:
            freq_score = frequency_scores.get(wine_id, 0.0)
            qual_score = quality_scores.get(wine_id, 0.0)
            
            combined_score = (weight_frequency * freq_score) + (weight_quality * qual_score)
            
            wine = wine_dict.get(wine_id)
            if wine:
                ranked_wines.append((wine_id, combined_score, wine))
        
        # Sort by combined score (descending)
        ranked_wines.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_wines
    
