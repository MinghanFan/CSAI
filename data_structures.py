# data_structures.py
"""Data structures and type definitions for player analysis with side separation."""

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
    max_velocity: float = 0.0
    movement_smoothness: float = 0.0
    avg_peek_distance_per_round: float = 0.0
    max_peek_distance_per_round: float = 0.0
    total_peek_events_per_round: float = 0.0
    movement_distance_per_round: float = 0.0
    position_variance_per_round: float = 0.0

@dataclass
class PositioningSignature:
    """Player's positioning preferences with side-specific data."""
    map_coverage_per_round: float = 0.0
    position_preferences: Dict[str, float] = None
    
    def __post_init__(self):
        if self.position_preferences is None:
            self.position_preferences = {}
    
    def get_ct_positions(self) -> Dict[str, float]:
        """Get CT-side position preferences."""
        return {k[3:]: v for k, v in self.position_preferences.items() 
                if k.startswith('ct_') and k != 'ct_map_coverage'}
    
    def get_t_positions(self) -> Dict[str, float]:
        """Get T-side position preferences."""
        return {k[2:]: v for k, v in self.position_preferences.items() 
                if k.startswith('t_') and k != 't_map_coverage'}
    
    def get_ct_coverage(self) -> float:
        """Get CT-side map coverage."""
        return self.position_preferences.get('ct_map_coverage', 0.0)
    
    def get_t_coverage(self) -> float:
        """Get T-side map coverage."""
        return self.position_preferences.get('t_map_coverage', 0.0)

@dataclass
class CombatSignature:
    """Player's combat statistics with side-specific data."""
    # Overall stats
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
    total_rounds: int = 0
    ct_rounds: int = 0
    t_rounds: int = 0
    
    # Death stats
    deaths_per_round: float = 0.0
    total_deaths: int = 0
    death_area_diversity: float = 0.0
    death_bombsite_ratio: float = 0.0
    death_position_variance: float = 0.0

    # Damage received stats
    damage_received_per_round: float = 0.0
    total_damage_received: int = 0

    # CT-side specific stats (will be populated dynamically)
    # t_kills_per_round, ct_damage_per_round, etc.

    def __post_init__(self):
        """Allow dynamic attributes for side-specific stats."""
        pass

    def __setattr__(self, name, value):
        """Allow setting dynamic attributes."""
        super().__setattr__(name, value)

    def get_ct_stats(self) -> Dict[str, Any]:
        """Get CT-side combat statistics."""
        ct_stats = {}
        for key, value in self.__dict__.items():
            if key.startswith('ct_'):
                ct_stats[key[3:]] = value
        return ct_stats

    def get_t_stats(self) -> Dict[str, Any]:
        """Get T-side combat statistics."""
        t_stats = {}
        for key, value in self.__dict__.items():
            if key.startswith('t_'):
                t_stats[key[2:]] = value
        return t_stats

@dataclass
class UtilitySignature:
    """Player's utility usage statistics."""
    flashes_thrown_per_round: float = 0.0
    enemies_flashed_per_round: float = 0.0
    flash_assists_per_round: float = 0.0
    flash_to_frag_rate: float = 0.0
    smokes_thrown_per_round: float = 0.0
    smoke_coverage_seconds_per_round: float = 0.0
    kills_through_smoke_per_round: float = 0.0
    molotovs_thrown_per_round: float = 0.0
    area_denial_seconds_per_round: float = 0.0
    he_damage_per_round: float = 0.0
    utility_damage_per_grenade: float = 0.0

    # Placeholder for potential extension (no dynamic attributes required).

@dataclass
class PlayerFingerprint:
    """Complete player style fingerprint with side separation."""
    movement: MovementSignature
    positioning: PositioningSignature
    combat: CombatSignature
    utility: UtilitySignature
    
    def to_feature_vector(self) -> Dict[str, float]:
        """Convert fingerprint to flat feature dictionary."""
        features = {}
        
        # Movement features (same for both sides)
        for key, value in self.movement.__dict__.items():
            features[f"movement_{key}"] = value
            
        # Positioning features (overall and side-specific)
        features[f"positioning_map_coverage_per_round"] = self.positioning.map_coverage_per_round
        
        # Add CT positioning
        ct_positions = self.positioning.get_ct_positions()
        for pos_name, time_fraction in ct_positions.items():
            features[f"positioning_ct_{pos_name}"] = time_fraction
        
        # Add T positioning
        t_positions = self.positioning.get_t_positions()
        for pos_name, time_fraction in t_positions.items():
            features[f"positioning_t_{pos_name}"] = time_fraction
        
        # Add side-specific coverage
        features[f"positioning_ct_coverage"] = self.positioning.get_ct_coverage()
        features[f"positioning_t_coverage"] = self.positioning.get_t_coverage()
        
        # Combat features (overall and side-specific)
        for key, value in self.combat.__dict__.items():
            if isinstance(value, (int, float)):
                features[f"combat_{key}"] = value

        for key, value in self.utility.__dict__.items():
            if isinstance(value, (int, float)):
                features[f"utility_{key}"] = value

        return features
    
    def get_side_comparison(self) -> Dict[str, Dict]:
        """Get a comparison of CT vs T side performance."""
        ct_combat = self.combat.get_ct_stats()
        t_combat = self.combat.get_t_stats()
        ct_positions = self.positioning.get_ct_positions()
        t_positions = self.positioning.get_t_positions()
        
        return {
            'ct_side': {
                'combat': ct_combat,
                'positions': ct_positions,
                'coverage': self.positioning.get_ct_coverage()
            },
            't_side': {
                'combat': t_combat,
                'positions': t_positions,
                'coverage': self.positioning.get_t_coverage()
            }
        }

@dataclass
class DemoData:
    """Container for all demo data."""
    ticks: pd.DataFrame
    kills: pd.DataFrame
    damages: pd.DataFrame
    deaths: pd.DataFrame
    damage_taken: pd.DataFrame
    assisted_kills: pd.DataFrame
    grenades: pd.DataFrame
    smokes: pd.DataFrame
    infernos: pd.DataFrame
    rounds: pd.DataFrame
    total_rounds: int
    ct_rounds: int
    t_rounds: int
