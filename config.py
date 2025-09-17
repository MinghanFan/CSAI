# config.py
"""Configuration and constants for CS:GO Player Style Analysis."""

import pathlib
import json
from typing import Dict, Any

# Demo file paths
DEMO_DIR = pathlib.Path("/Users/minghanfan/Documents/Test/test")
DEMO_FILES = [str(f) for f in sorted(DEMO_DIR.glob("*.dem")) if not f.name.startswith("._")]

# Analysis parameters
DEFAULT_ROUNDS_ESTIMATE = 20
COUNTER_STRAFE_MIN_VELOCITY = 200
COUNTER_STRAFE_THRESHOLD = -100
SIGNIFICANT_MOVEMENT_THRESHOLD = 50
MINIMUM_MOVEMENT_VELOCITY = 100

# Load extracted positions from JSON file
def load_map_positions() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Load map positions from the extracted_positions.json file."""
    try:
        with open('extracted_positions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: extracted_positions.json not found. Using fallback positions.")
        return get_fallback_positions()
    except json.JSONDecodeError as e:
        print(f"Error loading extracted_positions.json: {e}. Using fallback positions.")
        return get_fallback_positions()

def get_fallback_positions() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Fallback positions in case the JSON file is not available."""
    return {
        "de_mirage": {
            "A_site": {'x_range': [1400, 1800], 'y_range': [-400, 100]},
            "B_site": {'x_range': [-1400, -800], 'y_range': [400, 800]},
            "mid": {'x_range': [0, 600], 'y_range': [-200, 400]},
            "connector": {'x_range': [800, 1200], 'y_range': [200, 600]},
            "palace": {'x_range': [1000, 1400], 'y_range': [-800, -400]}
        }
    }

# Load all map positions
ALL_MAP_POSITIONS = load_map_positions()

def get_positions_for_map(map_name: str) -> Dict[str, Dict[str, Any]]:
    """Get position definitions for a specific map."""
    if map_name in ALL_MAP_POSITIONS:
        return ALL_MAP_POSITIONS[map_name]
    
    # Try to find map with different naming conventions
    for key in ALL_MAP_POSITIONS.keys():
        if map_name.lower() in key.lower() or key.lower() in map_name.lower():
            return ALL_MAP_POSITIONS[key]
    
    print(f"Warning: No positions found for map {map_name}")
    return {}

# Default to Mirage positions for backward compatibility
MIRAGE_POSITIONS = get_positions_for_map("de_mirage")

# Kill area definitions for analysis (using Mirage as default)
KILL_AREAS = MIRAGE_POSITIONS.copy()
if KILL_AREAS:
    KILL_AREAS['aggressive_areas'] = {'x_range': [-2000, 2000], 'y_range': [-1000, 1000]}

# PCA and similarity analysis settings
PCA_COMPONENTS = 2
TOP_SIMILAR_PLAYERS = 5

# Key players for detailed analysis
KEY_PLAYERS = ['m0NESY', 'ZywOo', 'NiKo', 'Magisk', 'apEX']
COMPARISON_PLAYERS = ['m0NESY', 'ZywOo', 'NiKo', 'Magisk']

# Output formatting
FLOAT_PRECISION_HIGH = 3  # For ratios, percentages
FLOAT_PRECISION_MED = 1   # For general stats
FLOAT_PRECISION_LOW = 0   # For distances, large numbers

# Available maps
AVAILABLE_MAPS = list(ALL_MAP_POSITIONS.keys())

def print_available_maps():
    """Print all available maps and their position counts."""
    print("Available maps:")
    for map_name, positions in ALL_MAP_POSITIONS.items():
        print(f"  {map_name}: {len(positions)} positions")