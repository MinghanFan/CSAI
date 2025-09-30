# analyzers/movement_analyzer.py
"""Movement pattern analysis for Counter-Strike players."""

import numpy as np
import pandas as pd
from typing import Dict, Any
from data_structures import MovementSignature
import config

class MovementAnalyzer:
    """Analyzes player movement patterns to create unique signatures."""
    
    def analyze(self, ticks_df: pd.DataFrame, total_rounds: int) -> MovementSignature:
        """Extract movement patterns that uniquely identify players."""
        print(f"    Movement analysis for {total_rounds} rounds")
        
        if 'velocity_X' not in ticks_df.columns or 'velocity_Y' not in ticks_df.columns:
            return MovementSignature(
                movement_distance_per_round=self._calculate_movement_distance(ticks_df) / total_rounds,
                position_variance_per_round=self._calculate_position_variance(ticks_df) / total_rounds
            )
        
        # Full analysis with velocity data
        counter_strafe_signature = self._analyze_counter_strafing(ticks_df)
        movement_smoothness = self._calculate_movement_smoothness(ticks_df)
        peek_behavior = self._analyze_peek_patterns(ticks_df, total_rounds)
        
        return MovementSignature(
            counter_strafe_frequency=counter_strafe_signature.get('counter_strafe_frequency', 0.0),
            avg_velocity=counter_strafe_signature.get('avg_velocity', 0.0),
            movement_smoothness=movement_smoothness,
            avg_peek_distance_per_round=peek_behavior.get('avg_peek_distance_per_round', 0.0),
            max_peek_distance_per_round=peek_behavior.get('max_peek_distance_per_round', 0.0),
            total_peek_events_per_round=peek_behavior.get('total_peek_events_per_round', 0.0),
            movement_distance_per_round=self._calculate_movement_distance(ticks_df) / total_rounds,
            position_variance_per_round=self._calculate_position_variance(ticks_df) / total_rounds
        )
    
    def _calculate_movement_distance(self, ticks_df: pd.DataFrame) -> float:
        """Calculate total movement distance."""
        if 'X' in ticks_df.columns and 'Y' in ticks_df.columns:
            distances = np.sqrt(ticks_df['X'].diff()**2 + ticks_df['Y'].diff()**2)
            return float(distances.sum())
        return 0.0
    
    def _calculate_position_variance(self, ticks_df: pd.DataFrame) -> float:
        """Calculate position variance (movement spread)."""
        if 'X' in ticks_df.columns and 'Y' in ticks_df.columns:
            return float(ticks_df['X'].var() + ticks_df['Y'].var())
        return 0.0
    
    def _analyze_counter_strafing(self, ticks_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze counter-strafing patterns."""
        try:
            ticks_df['velocity_magnitude'] = np.sqrt(
                ticks_df['velocity_X']**2 + ticks_df['velocity_Y']**2
            )
            velocity_changes = ticks_df['velocity_magnitude'].diff()
            rapid_stops = (
                (velocity_changes < config.COUNTER_STRAFE_THRESHOLD) & 
                (ticks_df['velocity_magnitude'].shift(1) > config.COUNTER_STRAFE_MIN_VELOCITY)
            )
            
            total_movements = len(ticks_df[ticks_df['velocity_magnitude'] > config.MINIMUM_MOVEMENT_VELOCITY])
            efficient_stops = len(ticks_df[rapid_stops])
            counter_strafe_ratio = efficient_stops / max(total_movements, 1)
            
            return {
                'counter_strafe_frequency': float(counter_strafe_ratio),
                'avg_velocity': float(ticks_df['velocity_magnitude'].mean())
            }
        except Exception:
            return {'counter_strafe_frequency': 0.0, 'avg_velocity': 0.0}
    
    def _calculate_movement_smoothness(self, ticks_df: pd.DataFrame) -> float:
        """Calculate movement smoothness (inverse of jerkiness)."""
        try:
            if 'velocity_X' in ticks_df.columns and 'velocity_Y' in ticks_df.columns:
                vel_x_changes = ticks_df['velocity_X'].diff().abs()
                vel_y_changes = ticks_df['velocity_Y'].diff().abs()
                return float(1 / (1 + vel_x_changes.mean() + vel_y_changes.mean()))
            return 0.0
        except Exception:
            return 0.0
    
    def _analyze_peek_patterns(self, ticks_df: pd.DataFrame, total_rounds: int) -> Dict[str, float]:
        """Analyze peeking/positioning change patterns."""
        if 'X' in ticks_df.columns and 'Y' in ticks_df.columns:
            position_changes = np.sqrt(ticks_df['X'].diff()**2 + ticks_df['Y'].diff()**2)
            return {
                'avg_peek_distance_per_round': float(position_changes.mean()),
                'max_peek_distance_per_round': float(position_changes.max() / total_rounds),
                'total_peek_events_per_round': float(
                    len(position_changes[position_changes > config.SIGNIFICANT_MOVEMENT_THRESHOLD]) / total_rounds
                )
            }
        return {
            'avg_peek_distance_per_round': 0.0, 
            'max_peek_distance_per_round': 0.0, 
            'total_peek_events_per_round': 0.0
        }