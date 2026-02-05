"""
Configuration constants for AI Culinary Expert application
"""

from pathlib import Path
from typing import Dict, Any

# Default file paths
DEFAULT_PROCESSED_DATA_DIR = Path("processed_data")
DEFAULT_WINES_PATH = DEFAULT_PROCESSED_DATA_DIR / "processed_wines.json"
DEFAULT_INGREDIENT_MAP_PATH = DEFAULT_PROCESSED_DATA_DIR / "ingredient_flavor_map.json"
DEFAULT_MENU_PROFILE_PATH = DEFAULT_PROCESSED_DATA_DIR / "menu_flavor_profile.json"

# Default thresholds
DEFAULT_SIMILARITY_THRESHOLD = 0.7  # For wine similarity
DEFAULT_FLAVOR_SIMILARITY_THRESHOLD = 0.3  # For dish similarity
DEFAULT_UNPAIRED_THRESHOLD = 0.25  # 25% of combinations can be unpaired

# Default combination patterns (logical combinations)
DEFAULT_LOGICAL_PATTERNS = [
    {"salad": 1, "appetizer": 2, "main": 2, "dessert": 0},
    {"salad": 1, "appetizer": 1, "main": 2, "dessert": 1},
    {"salad": 0, "appetizer": 2, "main": 2, "dessert": 0},
    {"salad": 1, "appetizer": 1, "main": 1, "dessert": 1},
]

# Default pairing settings
DEFAULT_MAX_WINES_PER_COMBO = 3
DEFAULT_MIN_WINES_PER_FLAVOR = 5
DEFAULT_MAX_WINES_PER_FLAVOR = 11

# Default random combination settings
DEFAULT_MAX_PLATES_PER_COMBO = 9
DEFAULT_NUM_RANDOM_COMBOS = 50

# Dish type keywords for categorization
DISH_TYPE_KEYWORDS = {
    "salad": ["salad", "green", "lettuce", "arugula", "spinach", "caesar", "garden"],
    "appetizer": ["appetizer", "starter", "tapas", "small plate", "hors d'oeuvre", "antipasto"],
    "main": ["main", "entree", "mains", "dish", "course", "plate"],
    "dessert": ["dessert", "sweet", "cake", "pie", "ice cream", "pudding", "tart"],
}

# Default configuration dictionary
DEFAULT_CONFIG: Dict[str, Any] = {
    "similarity_threshold": DEFAULT_SIMILARITY_THRESHOLD,
    "flavor_similarity_threshold": DEFAULT_FLAVOR_SIMILARITY_THRESHOLD,
    "unpaired_threshold": DEFAULT_UNPAIRED_THRESHOLD,
    "logical_patterns": DEFAULT_LOGICAL_PATTERNS,
    "max_wines_per_combo": DEFAULT_MAX_WINES_PER_COMBO,
    "min_wines_per_flavor": DEFAULT_MIN_WINES_PER_FLAVOR,
    "max_wines_per_flavor": DEFAULT_MAX_WINES_PER_FLAVOR,
    "max_plates_per_combo": DEFAULT_MAX_PLATES_PER_COMBO,
    "num_random_combos": DEFAULT_NUM_RANDOM_COMBOS,
    "dish_type_keywords": DISH_TYPE_KEYWORDS,
}
