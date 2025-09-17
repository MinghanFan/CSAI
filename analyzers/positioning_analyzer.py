# analyzers/positioning_analyzer.py
"""Positioning preference analysis for CS:GO players using detected map."""

import pandas as pd
from typing import Dict
from data_structures import PositioningSignature
import config

class PositioningAnalyzer:
    """Analyzes player positioning preferences and map coverage."""
    
    def analyze(self, ticks_df: pd.DataFrame, total_rounds: int) -> PositioningSignature:
        """Analyze positioning patterns and preferences."""
        if 'X' not in ticks_df.columns or 'Y' not in ticks_df.columns:
            return PositioningSignature(map_coverage_per_round=0.0)
        
        map_name = config.get_current_map_name()
        map_positions = config.get_current_map_positions()
        
        print(f"    Positioning analysis for {total_rounds} rounds on {map_name}")
        
        position_preferences = self._analyze_position_preferences(ticks_df, map_positions)
        map_coverage = self._calculate_map_coverage(ticks_df)
        
        return PositioningSignature(
            map_coverage_per_round=map_coverage / total_rounds,
            position_preferences=position_preferences
        )
    
    def _analyze_position_preferences(self, ticks_df: pd.DataFrame, 
                                    map_positions: Dict) -> Dict[str, float]:
        """Analyze time spent in different map positions."""
        position_time = {}
        total_ticks = len(ticks_df)
        
        if total_ticks == 0 or not map_positions:
            print("    No position definitions available - using basic coverage only")
            return {}
        
        print(f"    Analyzing position preferences across {len(map_positions)} areas")
        
        for pos_name, pos_coords in map_positions.items():
            try:
                # Handle both 2D and 3D coordinate ranges
                x_range = pos_coords['x_range']
                y_range = pos_coords['y_range']
                
                in_position = (
                    (ticks_df['X'].between(x_range[0], x_range[1])) &
                    (ticks_df['Y'].between(y_range[0], y_range[1]))
                )
                
                # Add Z-axis filtering if available
                if 'Z' in ticks_df.columns and 'z_range' in pos_coords:
                    z_range = pos_coords['z_range']
                    in_position = in_position & (
                        ticks_df['Z'].between(z_range[0], z_range[1])
                    )
                
                # Fraction of time spent in each position
                time_fraction = float(in_position.sum() / total_ticks)
                position_time[pos_name] = time_fraction
                
                if time_fraction > 0.01:  # Only log significant positions (>1% time)
                    print(f"      {pos_name}: {time_fraction:.3f} ({time_fraction*100:.1f}%)")
                    
            except Exception as e:
                print(f"      Error analyzing position {pos_name}: {e}")
                position_time[pos_name] = 0.0
        
        return position_time
    
    def _calculate_map_coverage(self, ticks_df: pd.DataFrame) -> float:
        """Calculate total map area covered by player movement."""
        try:
            x_range = ticks_df['X'].max() - ticks_df['X'].min()
            y_range = ticks_df['Y'].max() - ticks_df['Y'].min()
            coverage = float(x_range * y_range)
            print(f"    Map coverage: {coverage:.0f} square units")
            return coverage
        except Exception:
            return 0.0