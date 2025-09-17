# analyzers/positioning_analyzer.py
"""Positioning preference analysis for CS:GO players with side separation."""

import pandas as pd
from typing import Dict
from data_structures import PositioningSignature
import config

class PositioningAnalyzer:
    """Analyzes player positioning preferences and map coverage by side."""
    
    def analyze(self, ticks_df: pd.DataFrame, total_rounds: int) -> PositioningSignature:
        """Analyze positioning patterns separated by CT and T sides."""
        if 'X' not in ticks_df.columns or 'Y' not in ticks_df.columns:
            return PositioningSignature(map_coverage_per_round=0.0)
        
        map_name = config.get_current_map_name()
        map_positions = config.get_current_map_positions()
        
        print(f"    Positioning analysis for {total_rounds} rounds on {map_name}")
        
        # Separate analysis by side using the 'player_side' column we added
        ct_ticks = ticks_df[ticks_df.get('player_side', '') == 'CT'] if 'player_side' in ticks_df.columns else pd.DataFrame()
        t_ticks = ticks_df[ticks_df.get('player_side', '') == 'T'] if 'player_side' in ticks_df.columns else pd.DataFrame()
        
        print(f"    CT ticks: {len(ct_ticks)}, T ticks: {len(t_ticks)}")
        
        # Analyze positioning for each side
        position_preferences = {}
        
        if not ct_ticks.empty:
            ct_positions = self._analyze_position_preferences(ct_ticks, map_positions, "CT")
            for pos_name, time_fraction in ct_positions.items():
                position_preferences[f"ct_{pos_name}"] = time_fraction
        
        if not t_ticks.empty:
            t_positions = self._analyze_position_preferences(t_ticks, map_positions, "T")
            for pos_name, time_fraction in t_positions.items():
                position_preferences[f"t_{pos_name}"] = time_fraction
        
        # Calculate overall map coverage (both sides combined)
        map_coverage = self._calculate_map_coverage(ticks_df)
        
        # Calculate side-specific coverage
        if not ct_ticks.empty:
            ct_coverage = self._calculate_map_coverage(ct_ticks)
            position_preferences['ct_map_coverage'] = ct_coverage / max(1, len(ct_ticks)) * 1000  # Normalize
        
        if not t_ticks.empty:
            t_coverage = self._calculate_map_coverage(t_ticks)
            position_preferences['t_map_coverage'] = t_coverage / max(1, len(t_ticks)) * 1000  # Normalize
        
        return PositioningSignature(
            map_coverage_per_round=map_coverage / total_rounds,
            position_preferences=position_preferences
        )
    
    def _analyze_position_preferences(self, ticks_df: pd.DataFrame, 
                                    map_positions: Dict, side: str) -> Dict[str, float]:
        """Analyze time spent in different map positions for a specific side."""
        position_time = {}
        total_ticks = len(ticks_df)
        
        if total_ticks == 0 or not map_positions:
            return {}
        
        print(f"    Analyzing {side} side position preferences across {len(map_positions)} areas")
        
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
                
                if time_fraction > 0.02:  # Only log significant positions (>2% time)
                    print(f"      {side} {pos_name}: {time_fraction:.3f} ({time_fraction*100:.1f}%)")
                    
            except Exception as e:
                print(f"      Error analyzing {side} position {pos_name}: {e}")
                position_time[pos_name] = 0.0
        
        return position_time
    
    def _calculate_map_coverage(self, ticks_df: pd.DataFrame) -> float:
        """Calculate total map area covered by player movement."""
        try:
            if ticks_df.empty:
                return 0.0
            x_range = ticks_df['X'].max() - ticks_df['X'].min()
            y_range = ticks_df['Y'].max() - ticks_df['Y'].min()
            coverage = float(x_range * y_range)
            return coverage
        except Exception:
            return 0.0