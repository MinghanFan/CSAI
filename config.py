# config.py
"""Configuration and constants for CS:GO Player Style Analysis."""

import pathlib
from all_maps_3d_positions import *  # Import all position definitions

# Demo file paths
DEMO_DIR = pathlib.Path("/Users/minghanfan/Documents/Test/test")
DEMO_FILES = [str(f) for f in sorted(DEMO_DIR.glob("*.dem")) if not f.name.startswith("._")]

# Analysis parameters
DEFAULT_ROUNDS_ESTIMATE = 20
COUNTER_STRAFE_MIN_VELOCITY = 50
COUNTER_STRAFE_THRESHOLD = -30
SIGNIFICANT_MOVEMENT_THRESHOLD = 50
MINIMUM_MOVEMENT_VELOCITY = 100

# Map position definitions - automatically use the correct positions based on detected map
MAP_POSITIONS = {
    'de_anubis': ANUBIS_POSITIONS,
    'de_nuke': NUKE_POSITIONS,
    'de_dust2': DUST2_POSITIONS,
    'de_mirage': MIRAGE_POSITIONS,
    'de_ancient': ANCIENT_POSITIONS,
    'de_inferno': INFERNO_POSITIONS,
    'de_train': TRAIN_POSITIONS,
    'de_overpass': OVERPASS_POSITIONS
}

# Global variables to store detected map info (set during demo loading)
CURRENT_MAP_NAME = None
CURRENT_MAP_POSITIONS = {}

def set_current_map(map_name: str):
    """Set the current map being analyzed."""
    global CURRENT_MAP_NAME, CURRENT_MAP_POSITIONS
    CURRENT_MAP_NAME = map_name
    CURRENT_MAP_POSITIONS = MAP_POSITIONS.get(map_name, {})
    print(f"🗺️  Using position definitions for {map_name} ({len(CURRENT_MAP_POSITIONS)} areas)")

def get_current_map_positions():
    """Get position definitions for the current map."""
    return CURRENT_MAP_POSITIONS

def get_current_map_name():
    """Get the name of the current map."""
    return CURRENT_MAP_NAME

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