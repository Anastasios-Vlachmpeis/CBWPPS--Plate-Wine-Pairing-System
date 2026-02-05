"""
Wine similarity analysis module
Analyzes wines for similarity based on flavor compounds
"""

from typing import List, Dict, Any, Tuple, Set
from utils.config import DEFAULT_SIMILARITY_THRESHOLD


class WineSimilarityAnalyzer:
    """
    Analyzes wines for similarity based on flavor compounds
    """
    
    def __init__(self, similarity_threshold: float = None):
        """
        Initialize the similarity analyzer
        
        Args:
            similarity_threshold: Default threshold for similarity (default from config)
        """
        self.similarity_threshold = similarity_threshold or DEFAULT_SIMILARITY_THRESHOLD
    
    def calculate_similarity(self, wine1: Dict[str, Any], wine2: Dict[str, Any]) -> float:
        """
        Calculate Jaccard similarity between two wines based on flavor compounds
        
        Jaccard similarity: |compounds1 ∩ compounds2| / |compounds1 ∪ compounds2|
        
        Args:
            wine1: First wine dictionary (must have 'flavor_compounds' field)
            wine2: Second wine dictionary (must have 'flavor_compounds' field)
            
        Returns:
            Similarity score between 0 and 1
        """
        compounds1 = set(wine1.get("flavor_compounds", []))
        compounds2 = set(wine2.get("flavor_compounds", []))
        
        # If both wines have no compounds, return 0
        if not compounds1 and not compounds2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(compounds1 & compounds2)
        union = len(compounds1 | compounds2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def find_similar_pairs(
        self, 
        wines: List[Dict[str, Any]], 
        threshold: float = None
    ) -> List[Tuple[int, int, float]]:
        """
        Find all wine pairs above similarity threshold
        
        Args:
            wines: List of wine dictionaries
            threshold: Similarity threshold (uses default if None)
            
        Returns:
            List of tuples: (wine_id1, wine_id2, similarity_score)
        """
        if threshold is None:
            threshold = self.similarity_threshold
        
        similar_pairs = []
        
        # Compare all pairs
        for i, wine1 in enumerate(wines):
            wine_id1 = wine1.get("wine_id")
            if wine_id1 is None:
                continue
            
            for wine2 in wines[i+1:]:
                wine_id2 = wine2.get("wine_id")
                if wine_id2 is None:
                    continue
                
                similarity = self.calculate_similarity(wine1, wine2)
                
                if similarity >= threshold:
                    similar_pairs.append((wine_id1, wine_id2, similarity))
        
        # Sort by similarity (highest first)
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_pairs
    
    def group_similar_wines(
        self, 
        wines: List[Dict[str, Any]], 
        threshold: float = None
    ) -> List[List[int]]:
        """
        Group wines into similarity clusters
        
        Uses a simple clustering approach: wines are grouped if they share
        similarity >= threshold with at least one other wine in the cluster.
        
        Args:
            wines: List of wine dictionaries
            threshold: Similarity threshold (uses default if None)
            
        Returns:
            List of clusters, where each cluster is a list of wine_ids
        """
        if threshold is None:
            threshold = self.similarity_threshold
        
        # Find all similar pairs
        similar_pairs = self.find_similar_pairs(wines, threshold)
        
        # Build clusters using union-find approach
        wine_to_cluster = {}
        clusters = []
        
        for wine_id1, wine_id2, similarity in similar_pairs:
            cluster1 = wine_to_cluster.get(wine_id1)
            cluster2 = wine_to_cluster.get(wine_id2)
            
            if cluster1 is None and cluster2 is None:
                # Create new cluster
                new_cluster = [wine_id1, wine_id2]
                clusters.append(new_cluster)
                wine_to_cluster[wine_id1] = new_cluster
                wine_to_cluster[wine_id2] = new_cluster
            elif cluster1 is None:
                # Add wine1 to cluster2
                cluster2.append(wine_id1)
                wine_to_cluster[wine_id1] = cluster2
            elif cluster2 is None:
                # Add wine2 to cluster1
                cluster1.append(wine_id2)
                wine_to_cluster[wine_id2] = cluster1
            elif cluster1 != cluster2:
                # Merge clusters
                cluster1.extend(cluster2)
                for wine_id in cluster2:
                    wine_to_cluster[wine_id] = cluster1
                clusters.remove(cluster2)
        
        # Convert clusters to lists of unique wine_ids
        result = []
        seen_clusters = set()
        
        for cluster in clusters:
            cluster_id = id(cluster)
            if cluster_id not in seen_clusters:
                result.append(list(set(cluster)))  # Remove duplicates
                seen_clusters.add(cluster_id)
        
        return result
    
    def get_similarity_matrix(
        self, 
        wines: List[Dict[str, Any]]
    ) -> Dict[Tuple[int, int], float]:
        """
        Calculate similarity matrix for all wine pairs
        
        Args:
            wines: List of wine dictionaries
            
        Returns:
            Dictionary mapping (wine_id1, wine_id2) -> similarity_score
        """
        matrix = {}
        
        for i, wine1 in enumerate(wines):
            wine_id1 = wine1.get("wine_id")
            if wine_id1 is None:
                continue
            
            for wine2 in wines[i+1:]:
                wine_id2 = wine2.get("wine_id")
                if wine_id2 is None:
                    continue
                
                similarity = self.calculate_similarity(wine1, wine2)
                matrix[(wine_id1, wine_id2)] = similarity
                matrix[(wine_id2, wine_id1)] = similarity  # Symmetric
        
        return matrix
