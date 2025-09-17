# analyzers/positioning_analyzer.py
"""Positioning preference analysis for CS:GO players."""

import pandas as pd
from typing import Dict
from data_structures import PositioningSignature
import config

class PositioningAnalyzer:
    """Analyzes player positioning preferences and map coverage."""
    
    def __init__(self, map_name: str = "de_mirage"):
        self.map_name = map_name
        self.map_positions = config.get_positions_for_map(map_name)
        
        if not self.map_positions:
            print(f"Warning: No positions found for {map_name}, using fallback")
            self.map_positions = config.MIRAGE_POSITIONS
    
    def set_map(self, map_name: str):
        """Change the map being analyzed."""
        self.map_name = map_name
        self.map_positions = config.get_positions_for_map(map_name)
        
        if not self.map_positions:
            print(f"Warning: No positions found for {map_name}")
    
    def analyze(self, ticks_df: pd.DataFrame, total_rounds: int) -> PositioningSignature:
        """Analyze positioning patterns and preferences."""
        if 'X' not in ticks_df.columns or 'Y' not in ticks_df.columns:
            return PositioningSignature(map_coverage_per_round=0.0)
        
        print(f"    Positioning analysis for {total_rounds} rounds on {self.map_name}")
        
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
        
        for pos_name, pos_coords in self.map_positions.items():
            try:
                # Handle both list and tuple formats for coordinate ranges
                x_range = pos_coords.get('x_range', [0, 0])
                y_range = pos_coords.get('y_range', [0, 0])
                
                # Ensure we have valid ranges
                if len(x_range) >= 2 and len(y_range) >= 2:
                    in_position = (
                        (ticks_df['X'].between(x_range[0], x_range[1])) &
                        (ticks_df['Y'].between(y_range[0], y_range[1]))
                    )
                    # Fraction of time spent in each position (already normalized)
                    position_time[pos_name] = float(in_position.sum() / total_ticks)
                else:
                    position_time[pos_name] = 0.0
                    
            except Exception as e:
                print(f"    Warning: Error processing position {pos_name}: {e}")
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
    
    def get_position_summary(self) -> str:
        """Get a summary of available positions for the current map."""
        if not self.map_positions:
            return f"No positions available for {self.map_name}"
        
        summary = f"Map: {self.map_name}\n"
        summary += f"Available positions ({len(self.map_positions)}):\n"
        
        for pos_name, pos_data in self.map_positions.items():
            x_range = pos_data.get('x_range', [0, 0])
            y_range = pos_data.get('y_range', [0, 0])
            sample_count = pos_data.get('sample_count', 'N/A')
            
            summary += f"  {pos_name}: X({x_range[0]:.0f}, {x_range[1]:.0f}), "
            summary += f"Y({y_range[0]:.0f}, {y_range[1]:.0f}), "
            summary += f"Samples: {sample_count}\n"
        
        return summary