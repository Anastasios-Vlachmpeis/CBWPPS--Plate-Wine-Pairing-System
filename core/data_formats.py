"""
Standard data format definitions for dishes and wines
"""

from typing import Dict, List, Any, Optional


# Standard dish format structure
STANDARD_DISH_FORMAT = {
    "dish_id": str,  # Auto-generated or from source
    "name": str,
    "category": str,  # "salad", "appetizer", "main", "dessert"
    "ingredients": List[str],
    "compounds": List[str],  # Flavor compounds (from ingredient map)
    "tags": List[str],  # Dominant flavors
    "suggested_wine_type": str,  # "Red", "White", etc.
    "source_file": str,  # Original file path
}

# Standard wine format structure (matches wine_manager format)
STANDARD_WINE_FORMAT = {
    "wine_id": int,  # Auto-generated if missing
    "wine_name": str,
    "type_name": str,  # "Red", "White", "Rosé", "Sparkling", "Dessert"
    "body_name": str,
    "acidity_name": str,
    "grapes": List[str],
    "country": str,
    "region": str,
    "winery": str,
    "flavor_compounds": List[str],
    "harmonize": List[str],
}


def validate_dish_format(dish: Dict[str, Any]) -> bool:
    """
    Validate that a dish dictionary matches the standard format
    
    Args:
        dish: Dish dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["name", "category", "ingredients"]
    return all(field in dish for field in required_fields)


def validate_wine_format(wine: Dict[str, Any]) -> bool:
    """
    Validate that a wine dictionary matches the standard format
    
    Args:
        wine: Wine dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["wine_name"]
    return all(field in wine for field in required_fields)


def normalize_dish_format(
    dish: Dict[str, Any],
    dish_id: Optional[str] = None,
    source_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Normalize a dish dictionary to standard format
    
    Args:
        dish: Raw dish dictionary from extraction
        dish_id: Optional dish ID (auto-generated if None)
        source_file: Optional source file path
        
    Returns:
        Normalized dish dictionary
    """
    import hashlib
    import uuid
    
    # Generate dish_id if not provided
    if dish_id is None:
        dish_name = dish.get("dish_name") or dish.get("name", "")
        if dish_name:
            dish_id = hashlib.md5(dish_name.encode()).hexdigest()[:12]
        else:
            dish_id = str(uuid.uuid4())[:12]
    
    normalized = {
        "dish_id": dish_id,
        "name": dish.get("dish_name") or dish.get("name", "Unknown Dish"),
        "category": dish.get("category", "main").lower(),
        "ingredients": dish.get("key_ingredients") or dish.get("ingredients", []),
        "compounds": dish.get("compounds", []),  # Will be populated later
        "tags": dish.get("dominant_flavors") or dish.get("tags", []),
        "suggested_wine_type": dish.get("suggested_wine_type", "Unknown"),
        "source_file": source_file or dish.get("source_file", ""),
    }
    
    # Ensure lists are actually lists
    if not isinstance(normalized["ingredients"], list):
        normalized["ingredients"] = []
    if not isinstance(normalized["compounds"], list):
        normalized["compounds"] = []
    if not isinstance(normalized["tags"], list):
        normalized["tags"] = []
    
    # Validate category
    valid_categories = ["salad", "appetizer", "main", "dessert"]
    if normalized["category"] not in valid_categories:
        normalized["category"] = "main"  # Default
    
    return normalized


def normalize_wine_format(wine: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a wine dictionary to standard format
    (Reuses logic from wine_manager, but provides standalone function)
    
    Args:
        wine: Raw wine dictionary from extraction
        
    Returns:
        Normalized wine dictionary
    """
    import hashlib
    
    # Generate wine_id if not provided
    wine_id = wine.get("wine_id")
    if wine_id is None:
        wine_name = wine.get("wine_name") or wine.get("name", "")
        if wine_name:
            wine_id = hash(wine_name) % (10 ** 9)  # Generate numeric ID
        else:
            wine_id = hash(str(wine)) % (10 ** 9)
    
    normalized = {
        "wine_id": int(wine_id) if isinstance(wine_id, (int, float)) else hash(str(wine_id)) % (10 ** 9),
        "wine_name": wine.get("wine_name") or wine.get("name", "Unknown Wine"),
        "type_name": wine.get("type_name") or wine.get("type", "Unknown"),
        "body_name": wine.get("body_name") or wine.get("body", "Unknown"),
        "acidity_name": wine.get("acidity_name") or wine.get("acidity", "Unknown"),
        "grapes": wine.get("grapes", []),
        "country": wine.get("country", "Unknown"),
        "region": wine.get("region", "Unknown"),
        "winery": wine.get("winery") or wine.get("winery_name", "Unknown"),
        "flavor_compounds": wine.get("flavor_compounds", []),
        "harmonize": wine.get("harmonize", []),
    }
    
    # Ensure lists are actually lists
    if not isinstance(normalized["grapes"], list):
        if isinstance(normalized["grapes"], str):
            normalized["grapes"] = [g.strip() for g in normalized["grapes"].split(",") if g.strip()]
        else:
            normalized["grapes"] = []
    
    if not isinstance(normalized["flavor_compounds"], list):
        normalized["flavor_compounds"] = []
    
    if not isinstance(normalized["harmonize"], list):
        normalized["harmonize"] = []
    
    return normalized
