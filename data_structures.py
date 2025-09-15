# data_structures.py
"""Data structures and type definitions for player analysis."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import pandas as pd

@dataclass
class PlayerInfo:
    """Basic player information."""
    steamid: str
    main_name: str
    all_names: List[str]

@dataclass
class MovementSignature:
    """Player's movement characteristics."""
    counter_strafe_frequency: float = 0.0
    avg_velocity: float = 0.0
    movement_smoothness: float = 0.0
    avg_peek_distance_per_round: float = 0.0
    max_peek_distance_per_round: float = 0.0
    total_peek_events_per_round: float = 0.0
    movement_distance_per_round: float = 0.0
    position_variance_per_round: float = 0.0

@dataclass
class PositioningSignature:
    """Player's positioning preferences."""
    map_coverage_per_round: float = 0.0
    position_preferences: Dict[str, float] = None
    
    def __post_init__(self):
        if self.position_preferences is None:
            self.position_preferences = {}

@dataclass
class CombatSignature:
    """Player's combat statistics."""
    kills_per_round: float = 0.0
    total_kills: int = 0
    primary_weapon: str = 'none'
    weapon_diversity: int = 0
    headshot_ratio: float = 0.0
    multi_kill_rounds: int = 0
    clutch_potential: float = 0.0
    damage_per_round: float = 0.0
    total_damage: int = 0
    avg_damage_per_hit: float = 0.0
    damage_consistency: float = 0.0
    first_shot_damage: float = 0.0
    kill_efficiency: float = 0.0
    kill_area_diversity: float = 0.0
    aggressive_kill_ratio: float = 0.0
    kill_position_variance: float = 0.0

@dataclass
class PlayerFingerprint:
    """Complete player style fingerprint."""
    movement: MovementSignature
    positioning: PositioningSignature
    combat: CombatSignature
    
    def to_feature_vector(self) -> Dict[str, float]:
        """Convert fingerprint to flat feature dictionary."""
        features = {}
        
        # Movement features
        for key, value in self.movement.__dict__.items():
            features[f"movement_{key}"] = value
            
        # Positioning features
        features[f"positioning_map_coverage_per_round"] = self.positioning.map_coverage_per_round
        for pos_name, time_fraction in self.positioning.position_preferences.items():
            features[f"positioning_{pos_name}"] = time_fraction
            
        # Combat features
        for key, value in self.combat.__dict__.items():
            if isinstance(value, (int, float)):
                features[f"combat_{key}"] = value
                
        return features

@dataclass
class DemoData:
    """Container for all demo data."""
    ticks: pd.DataFrame
    kills: pd.DataFrame
    damages: pd.DataFrame
    rounds: pd.DataFrame
    total_rounds: int