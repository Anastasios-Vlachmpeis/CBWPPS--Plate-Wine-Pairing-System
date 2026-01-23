"""
Wine Pairing AI - Data Processing Script
Processes XWines and FlavorGraph datasets to create unified JSON Knowledge Base
"""

import pandas as pd
import json
import ast
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class PairingLogic:
    """
    Sommelier Rules for Wine-Food Pairing
    This class defines basic pairing rules that can be referenced by the AI model.
    """
    
    # Tannin levels (1-5 scale)
    TANNIN_SCALE = {
        'Very Low': 1,
        'Low': 2,
        'Medium': 3,
        'High': 4,
        'Very High': 5
    }
    
    # Acidity levels (1-5 scale)
    ACIDITY_SCALE = {
        'Very Low': 1,
        'Low': 2,
        'Medium': 3,
        'High': 4,
        'Very High': 5
    }
    
    # Body levels (1-5 scale)
    BODY_SCALE = {
        'Very light-bodied': 1,
        'Light-bodied': 2,
        'Medium-bodied': 3,
        'Full-bodied': 4,
        'Very full-bodied': 5
    }
    
    @staticmethod
    def tannin_vs_spice_conflict(wine_tannin: int, food_spice: int) -> bool:
        """
        High tannin wines conflict with highly spiced foods.
        Returns True if there's a conflict.
        """
        return wine_tannin >= 4 and food_spice >= 4
    
    @staticmethod
    def acid_vs_acid_congruence(wine_acid: int, food_acid: int) -> bool:
        """
        Acidic wines pair well with acidic foods (congruence).
        Returns True if pairing is good.
        """
        return abs(wine_acid - food_acid) <= 1
    
    @staticmethod
    def body_vs_richness_match(wine_body: int, food_richness: int) -> bool:
        """
        Full-bodied wines pair with rich foods, light wines with delicate foods.
        Returns True if pairing is good.
        """
        return abs(wine_body - food_richness) <= 1
    
    @staticmethod
    def sweetness_balance(wine_sweetness: int, food_sweetness: int) -> bool:
        """
        Wine should be as sweet or sweeter than the food.
        Returns True if pairing is good.
        """
        return wine_sweetness >= food_sweetness


class WineProcessor:
    """Processes XWines dataset"""
    
    TYPE_MAPPING = {
        'Sparkling': 1,
        'White': 2,
        'Rosé': 3,
        'Red': 4,
        'Dessert/Port': 5,
        'Dessert': 5,
        'Port': 5
    }
    
    BODY_MAPPING = {
        'Very light-bodied': 1,
        'Light-bodied': 2,
        'Medium-bodied': 3,
        'Full-bodied': 4,
        'Very full-bodied': 5
    }
    
    ACIDITY_MAPPING = {
        'Very Low': 1,
        'Low': 2,
        'Medium': 3,
        'High': 4,
        'Very High': 5
    }
    
    @staticmethod
    def normalize_type(wine_type: str) -> int:
        """Normalize wine type to 1-5 scale"""
        if pd.isna(wine_type):
            return 3  # Neutral/Unknown
        wine_type = str(wine_type).strip()
        for key, value in WineProcessor.TYPE_MAPPING.items():
            if key.lower() in wine_type.lower():
                return value
        return 3  # Default to neutral
    
    @staticmethod
    def normalize_body(body: str) -> int:
        """Normalize body to 1-5 scale"""
        if pd.isna(body):
            return 3  # Neutral/Unknown
        body = str(body).strip()
        return WineProcessor.BODY_MAPPING.get(body, 3)
    
    @staticmethod
    def normalize_acidity(acidity: str) -> int:
        """Normalize acidity to 1-5 scale"""
        if pd.isna(acidity):
            return 3  # Neutral/Unknown
        acidity = str(acidity).strip()
        # Handle common variations
        if 'high' in acidity.lower():
            return 4
        elif 'medium' in acidity.lower():
            return 3
        elif 'low' in acidity.lower():
            return 2
        return WineProcessor.ACIDITY_MAPPING.get(acidity, 3)
    
    @staticmethod
    def parse_grapes(grapes_str: str) -> List[str]:
        """Parse grapes string into list"""
        if pd.isna(grapes_str):
            return []
        try:
            # Try to parse as Python list literal
            grapes_list = ast.literal_eval(str(grapes_str))
            if isinstance(grapes_list, list):
                return [g.strip() for g in grapes_list if g]
            elif isinstance(grapes_list, str):
                return [grapes_list.strip()]
        except (ValueError, SyntaxError):
            # Fallback: split by comma if not a valid list
            grapes_str = str(grapes_str).strip()
            if grapes_str:
                return [g.strip() for g in grapes_str.split(',') if g.strip()]
        return []
    
    @staticmethod
    def process_wines(csv_path: str) -> List[Dict[str, Any]]:
        """Process XWines CSV into structured JSON"""
        df = pd.read_csv(csv_path)
        wines = []
        
        for _, row in df.iterrows():
            wine = {
                'wine_id': int(row['WineID']) if pd.notna(row['WineID']) else None,
                'wine_name': str(row['WineName']) if pd.notna(row['WineName']) else 'Unknown',
                'type': WineProcessor.normalize_type(row.get('Type', 'Unknown')),
                'type_name': str(row['Type']) if pd.notna(row.get('Type')) else 'Unknown',
                'body': WineProcessor.normalize_body(row.get('Body', 'Unknown')),
                'body_name': str(row['Body']) if pd.notna(row.get('Body')) else 'Unknown',
                'acidity': WineProcessor.normalize_acidity(row.get('Acidity', 'Unknown')),
                'acidity_name': str(row['Acidity']) if pd.notna(row.get('Acidity')) else 'Unknown',
                'grapes': WineProcessor.parse_grapes(row.get('Grapes', '')),
                'abv': float(row['ABV']) if pd.notna(row.get('ABV')) else None,
                'country': str(row['Country']) if pd.notna(row.get('Country')) else 'Unknown',
                'region': str(row['RegionName']) if pd.notna(row.get('RegionName')) else 'Unknown',
                'winery': str(row['WineryName']) if pd.notna(row.get('WineryName')) else 'Unknown',
                'harmonize': ast.literal_eval(row['Harmonize']) if pd.notna(row.get('Harmonize')) else [],
                'flavor_compounds': []  # Will be populated by flavor bridge
            }
            wines.append(wine)
        
        return wines


class FlavorGraphProcessor:
    """Processes FlavorGraph dataset"""
    
    @staticmethod
    def clean_ingredient_name(name: str) -> str:
        """Clean ingredient name for matching"""
        if pd.isna(name):
            return ""
        name = str(name).lower()
        # Remove special characters, keep alphanumeric and spaces
        name = re.sub(r'[^a-z0-9\s]', '', name)
        # Replace underscores and multiple spaces with single space
        name = re.sub(r'[_\s]+', ' ', name)
        return name.strip()
    
    @staticmethod
    def process_flavor_graph(nodes_path: str, edges_path: str) -> Dict[str, List[str]]:
        """
        Process FlavorGraph to create ingredient -> compounds mapping
        Returns dictionary: {ingredient_name: [compound_names]}
        """
        # Load nodes
        nodes_df = pd.read_csv(nodes_path)
        
        # Create node_id to name mapping for compounds
        compound_map = {}
        ingredient_map = {}
        
        for _, row in nodes_df.iterrows():
            node_id = int(row['node_id'])
            name = str(row['name'])
            node_type = str(row['node_type']).lower()
            
            if node_type == 'compound':
                compound_map[node_id] = name
            elif node_type == 'ingredient':
                ingredient_map[node_id] = name
        
        # Load edges
        edges_df = pd.read_csv(edges_path)
        
        # Create ingredient to compounds mapping
        ingredient_compounds = {}
        
        for _, row in edges_df.iterrows():
            id_1 = int(row['id_1'])
            id_2 = int(row['id_2'])
            edge_type = str(row['edge_type']).lower()
            
            # Check if this edge connects ingredient to compound
            if edge_type in ['ingr-fcomp', 'ingr-dcomp']:
                # Determine which is ingredient and which is compound
                ingredient_id = None
                compound_id = None
                
                if id_1 in ingredient_map and id_2 in compound_map:
                    ingredient_id = id_1
                    compound_id = id_2
                elif id_2 in ingredient_map and id_1 in compound_map:
                    ingredient_id = id_2
                    compound_id = id_1
                
                if ingredient_id and compound_id:
                    ingredient_name = ingredient_map[ingredient_id]
                    compound_name = compound_map[compound_id]
                    
                    # Use cleaned name as key
                    cleaned_name = FlavorGraphProcessor.clean_ingredient_name(ingredient_name)
                    
                    if cleaned_name not in ingredient_compounds:
                        ingredient_compounds[cleaned_name] = []
                    
                    if compound_name not in ingredient_compounds[cleaned_name]:
                        ingredient_compounds[cleaned_name].append(compound_name)
        
        # Also create mapping with original names for reference
        ingredient_flavor_map = {}
        for ingredient_id, ingredient_name in ingredient_map.items():
            cleaned_name = FlavorGraphProcessor.clean_ingredient_name(ingredient_name)
            if cleaned_name in ingredient_compounds:
                ingredient_flavor_map[ingredient_name] = {
                    'cleaned_name': cleaned_name,
                    'compounds': ingredient_compounds[cleaned_name]
                }
        
        return ingredient_flavor_map


class FlavorBridge:
    """Creates flavor bridge connecting wines to chemicals via grapes"""
    
    # Common grape to ingredient/flavor mappings
    # This is a simplified mapping - in production, this could be expanded
    GRAPE_FLAVOR_MAPPINGS = {
        'syrah': ['blackberry', 'pepper', 'spice'],
        'shiraz': ['blackberry', 'pepper', 'spice'],
        'cabernet sauvignon': ['blackcurrant', 'cedar', 'tobacco'],
        'merlot': ['plum', 'cherry', 'chocolate'],
        'pinot noir': ['cherry', 'strawberry', 'earth'],
        'chardonnay': ['apple', 'butter', 'vanilla'],
        'sauvignon blanc': ['gooseberry', 'citrus', 'grass'],
        'riesling': ['apple', 'peach', 'honey'],
        'muscat': ['grape', 'floral', 'honey'],
        'moscato': ['grape', 'floral', 'honey'],
        'grenache': ['raspberry', 'strawberry', 'spice'],
        'tempranillo': ['cherry', 'plum', 'leather'],
        'sangiovese': ['cherry', 'herbs', 'earth'],
        'nebbiolo': ['rose', 'tar', 'truffle'],
        'zinfandel': ['berry', 'spice', 'jam'],
    }
    
    @staticmethod
    def create_flavor_bridge(wines: List[Dict[str, Any]], 
                            ingredient_flavor_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Tag wines with flavor compounds based on their grapes
        """
        # Create a lookup for ingredient names (cleaned)
        cleaned_to_compounds = {}
        for ingredient_name, data in ingredient_flavor_map.items():
            cleaned_name = data['cleaned_name']
            if cleaned_name not in cleaned_to_compounds:
                cleaned_to_compounds[cleaned_name] = []
            cleaned_to_compounds[cleaned_name].extend(data['compounds'])
        
        for wine in wines:
            flavor_compounds = []
            grapes = wine.get('grapes', [])
            
            for grape in grapes:
                grape_lower = grape.lower().strip()
                
                # Try direct match with grape name
                grape_cleaned = FlavorGraphProcessor.clean_ingredient_name(grape)
                if grape_cleaned in cleaned_to_compounds:
                    flavor_compounds.extend(cleaned_to_compounds[grape_cleaned])
                
                # Try grape flavor mappings
                for grape_key, flavor_terms in FlavorBridge.GRAPE_FLAVOR_MAPPINGS.items():
                    if grape_key in grape_lower:
                        # Search for these flavor terms in ingredient map
                        for flavor_term in flavor_terms:
                            flavor_cleaned = FlavorGraphProcessor.clean_ingredient_name(flavor_term)
                            if flavor_cleaned in cleaned_to_compounds:
                                flavor_compounds.extend(cleaned_to_compounds[flavor_cleaned])
            
            # Remove duplicates while preserving order
            wine['flavor_compounds'] = list(dict.fromkeys(flavor_compounds))
        
        return wines


def main():
    """Main processing function"""
    # Define paths
    datasets_dir = Path("Datasets")
    output_dir = Path("processed_data")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print("Step 1: Processing XWines dataset...")
    wines = WineProcessor.process_wines(datasets_dir / "XWines_Slim_1K_wines.csv")
    print(f"  Processed {len(wines)} wines")
    
    print("\nStep 2: Processing FlavorGraph dataset...")
    ingredient_flavor_map = FlavorGraphProcessor.process_flavor_graph(
        datasets_dir / "nodes_191120.csv",
        datasets_dir / "edges_191120.csv"
    )
    print(f"  Mapped {len(ingredient_flavor_map)} ingredients to compounds")
    
    print("\nStep 3: Creating flavor bridge...")
    wines = FlavorBridge.create_flavor_bridge(wines, ingredient_flavor_map)
    wines_with_compounds = sum(1 for w in wines if w['flavor_compounds'])
    print(f"  Tagged {wines_with_compounds} wines with flavor compounds")
    
    print("\nStep 4: Saving processed data...")
    
    # Save processed wines
    wines_output_path = output_dir / "processed_wines.json"
    with open(wines_output_path, 'w', encoding='utf-8') as f:
        json.dump(wines, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(wines)} wines to {wines_output_path}")
    
    # Save ingredient flavor map
    ingredient_output_path = output_dir / "ingredient_flavor_map.json"
    with open(ingredient_output_path, 'w', encoding='utf-8') as f:
        json.dump(ingredient_flavor_map, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(ingredient_flavor_map)} ingredient mappings to {ingredient_output_path}")
    
    print("\nProcessing complete!")
    print(f"\nOutput files:")
    print(f"  - {wines_output_path}")
    print(f"  - {ingredient_output_path}")
    print(f"\nPairingLogic class is available for reference in processing.py")


if __name__ == "__main__":
    main()
