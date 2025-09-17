# analyzers/movement_analyzer.py
"""Movement pattern analysis for CS:GO players."""

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
        
        # Debug: Print available columns
        print(f"    Available columns: {list(ticks_df.columns)}")
        
        # Check for velocity columns with different possible names
        velocity_cols = self._find_velocity_columns(ticks_df)
        
        if not velocity_cols:
            print("    Warning: No velocity columns found, using basic movement analysis")
            return MovementSignature(
                movement_distance_per_round=self._calculate_movement_distance(ticks_df) / total_rounds,
                position_variance_per_round=self._calculate_position_variance(ticks_df) / total_rounds
            )
        
        print(f"    Found velocity columns: {velocity_cols}")
        
        # Full analysis with velocity data
        counter_strafe_signature = self._analyze_counter_strafing(ticks_df, velocity_cols)
        movement_smoothness = self._calculate_movement_smoothness(ticks_df, velocity_cols)
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
    
    def _find_velocity_columns(self, ticks_df: pd.DataFrame) -> Dict[str, str]:
        """Find velocity columns with different possible naming conventions."""
        velocity_cols = {}
        
        # Possible column names for velocity
        x_velocity_names = ['velocity_X', 'vel_X', 'velocityX', 'vX', 'velocity_x']
        y_velocity_names = ['velocity_Y', 'vel_Y', 'velocityY', 'vY', 'velocity_y']
        z_velocity_names = ['velocity_Z', 'vel_Z', 'velocityZ', 'vZ', 'velocity_z']
        
        # Find X velocity
        for col_name in x_velocity_names:
            if col_name in ticks_df.columns:
                velocity_cols['x'] = col_name
                break
        
        # Find Y velocity
        for col_name in y_velocity_names:
            if col_name in ticks_df.columns:
                velocity_cols['y'] = col_name
                break
                
        # Find Z velocity (optional)
        for col_name in z_velocity_names:
            if col_name in ticks_df.columns:
                velocity_cols['z'] = col_name
                break
        
        # Need at least X and Y velocity
        if 'x' in velocity_cols and 'y' in velocity_cols:
            return velocity_cols
        else:
            return {}
    
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
    
    def _analyze_counter_strafing(self, ticks_df: pd.DataFrame, velocity_cols: Dict[str, str]) -> Dict[str, float]:
        """Analyze counter-strafing patterns."""
        try:
            vel_x_col = velocity_cols['x']
            vel_y_col = velocity_cols['y']
            
            ticks_df['velocity_magnitude'] = np.sqrt(
                ticks_df[vel_x_col]**2 + ticks_df[vel_y_col]**2
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
        except Exception as e:
            print(f"    Warning: Error in counter-strafe analysis: {e}")
            return {'counter_strafe_frequency': 0.0, 'avg_velocity': 0.0}
    
    def _calculate_movement_smoothness(self, ticks_df: pd.DataFrame, velocity_cols: Dict[str, str]) -> float:
        """Calculate movement smoothness (inverse of jerkiness)."""
        try:
            vel_x_col = velocity_cols['x']
            vel_y_col = velocity_cols['y']
            
            vel_x_changes = ticks_df[vel_x_col].diff().abs()
            vel_y_changes = ticks_df[vel_y_col].diff().abs()
            return float(1 / (1 + vel_x_changes.mean() + vel_y_changes.mean()))
        except Exception as e:
            print(f"    Warning: Error in smoothness calculation: {e}")
            return 0.0
    
    def _analyze_peek_patterns(self, ticks_df: pd.DataFrame, total_rounds: int) -> Dict[str, float]:
        """Analyze peeking/positioning change patterns."""
        if 'X' in ticks_df.columns and 'Y' in ticks_df.columns:
            position_changes = np.sqrt(ticks_df['X'].diff()**2 + ticks_df['Y'].diff()**2)
            position_changes = position_changes.dropna()  # Remove NaN values
            
            if len(position_changes) > 0:
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