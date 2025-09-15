# analyzers/positioning_analyzer.py
"""Positioning preference analysis for CS:GO players."""

import pandas as pd
from typing import Dict
from data_structures import PositioningSignature
import config

class PositioningAnalyzer:
    """Analyzes player positioning preferences and map coverage."""
    
    def __init__(self):
        self.mirage_positions = config.MIRAGE_POSITIONS
    
    def analyze(self, ticks_df: pd.DataFrame, total_rounds: int) -> PositioningSignature:
        """Analyze positioning patterns and preferences."""
        if 'X' not in ticks_df.columns or 'Y' not in ticks_df.columns:
            return PositioningSignature(map_coverage_per_round=0.0)
        
        print(f"    Positioning analysis for {total_rounds} rounds")
        
        position_preferences = self._analyze_position_preferences(ticks_df)
        map_coverage = self._calculate_map_coverage(ticks_df)
        
        return PositioningSignature(
            map_coverage_per_round=map_coverage / total_rounds,
            position_preferences=position_preferences
        )
    
    def _analyze_position_preferences(self, ticks_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze time spent in different map positions."""
        position_time = {}
        total_ticks = len(ticks_df)
        
        if total_ticks == 0:
            return {}
        
        for pos_name, pos_coords in self.mirage_positions.items():
            try:
                in_position = (
                    (ticks_df['X'].between(pos_coords['x_range'][0], pos_coords['x_range'][1])) &
                    (ticks_df['Y'].between(pos_coords['y_range'][0], pos_coords['y_range'][1]))
                )
                # Fraction of time spent in each position (already normalized)
                position_time[pos_name] = float(in_position.sum() / total_ticks)
            except Exception:
                position_time[pos_name] = 0.0
        
        return position_time
    
    def _calculate_map_coverage(self, ticks_df: pd.DataFrame) -> float:
        """Calculate total map area covered by player movement."""
        try:
            x_range = ticks_df['X'].max() - ticks_df['X'].min()
            y_range = ticks_df['Y'].max() - ticks_df['Y'].min()
            return float(x_range * y_range)
        except Exception:
            return 0.0