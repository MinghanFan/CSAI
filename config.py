# config.py
"""Configuration and constants for CS:GO Player Style Analysis."""

import pathlib

# Demo file paths
DEMO_DIR = pathlib.Path("/Users/minghanfan/Documents/Test/test")
DEMO_FILES = [str(f) for f in sorted(DEMO_DIR.glob("*.dem")) if not f.name.startswith("._")]

# Analysis parameters
DEFAULT_ROUNDS_ESTIMATE = 20
COUNTER_STRAFE_MIN_VELOCITY = 200
COUNTER_STRAFE_THRESHOLD = -100
SIGNIFICANT_MOVEMENT_THRESHOLD = 50
MINIMUM_MOVEMENT_VELOCITY = 100

# Mirage map position definitions
MIRAGE_POSITIONS = {
    'A_site': {'x_range': (1400, 1800), 'y_range': (-400, 100)},
    'B_site': {'x_range': (-1400, -800), 'y_range': (400, 800)},
    'mid': {'x_range': (0, 600), 'y_range': (-200, 400)},
    'connector': {'x_range': (800, 1200), 'y_range': (200, 600)},
    'palace': {'x_range': (1000, 1400), 'y_range': (-800, -400)}
}

# Kill area definitions for analysis
KILL_AREAS = {
    'A_site': {'x_range': (1400, 1800), 'y_range': (-400, 100)},
    'B_site': {'x_range': (-1400, -800), 'y_range': (400, 800)},
    'mid': {'x_range': (0, 600), 'y_range': (-200, 400)},
    'aggressive_areas': {'x_range': (-2000, 2000), 'y_range': (-1000, 1000)}
}

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