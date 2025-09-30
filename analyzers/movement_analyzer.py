# analyzers/movement_analyzer.py
"""Movement pattern analysis for Counter-Strike players."""

import numpy as np
import pandas as pd
from typing import Dict
from data_structures import MovementSignature
import config

class MovementAnalyzer:
    """Analyzes player movement patterns to create unique signatures."""
    
    def analyze(self, ticks_df: pd.DataFrame, total_rounds: int) -> MovementSignature:
        """Extract movement patterns that uniquely identify players."""
        print(f"    Movement analysis for {total_rounds} rounds")
        
        total_rounds = max(total_rounds, 1)

        # Base metrics always available when we have coordinates
        distance_per_round = self._calculate_movement_distance(ticks_df) / total_rounds
        position_variance_per_round = self._calculate_position_variance(ticks_df)

        if 'velocity_X' not in ticks_df.columns or 'velocity_Y' not in ticks_df.columns:
            return MovementSignature(
                movement_distance_per_round=distance_per_round,
                position_variance_per_round=position_variance_per_round
            )
        
        # Full analysis with velocity data
        counter_strafe_signature = self._analyze_counter_strafing(ticks_df, total_rounds)
        movement_smoothness = self._calculate_movement_smoothness(ticks_df)
        peek_behavior = self._analyze_peek_patterns(ticks_df, total_rounds)

        return MovementSignature(
            counter_strafe_frequency=counter_strafe_signature.get('counter_strafe_frequency', 0.0),
            avg_velocity=counter_strafe_signature.get('avg_velocity', 0.0),
            max_velocity=counter_strafe_signature.get('max_velocity', 0.0),
            movement_smoothness=movement_smoothness,
            avg_peek_distance_per_round=peek_behavior.get('avg_peek_distance_per_round', 0.0),
            max_peek_distance_per_round=peek_behavior.get('max_peek_distance_per_round', 0.0),
            total_peek_events_per_round=peek_behavior.get('total_peek_events_per_round', 0.0),
            movement_distance_per_round=distance_per_round,
            position_variance_per_round=position_variance_per_round
        )
    
    def _calculate_movement_distance(self, ticks_df: pd.DataFrame) -> float:
        """Calculate total movement distance."""
        if 'X' not in ticks_df.columns or 'Y' not in ticks_df.columns:
            return 0.0

        z_diff = ticks_df['Z'].diff().fillna(0.0)**2 if 'Z' in ticks_df.columns else 0.0
        distances = np.sqrt(
            ticks_df['X'].diff().fillna(0.0)**2 +
            ticks_df['Y'].diff().fillna(0.0)**2 +
            z_diff
        )
        return float(distances.sum())

    def _calculate_position_variance(self, ticks_df: pd.DataFrame) -> float:
        """Average positional variance per round."""
        if 'X' not in ticks_df.columns or 'Y' not in ticks_df.columns:
            return 0.0

        coord_cols = ['X', 'Y'] + (['Z'] if 'Z' in ticks_df.columns else [])

        if 'round_num' in ticks_df.columns:
            per_round_variance = (
                ticks_df.groupby('round_num')[coord_cols]
                .var(ddof=0)  # population variance for stability
                .fillna(0.0)
                .sum(axis=1)
            )
            if not per_round_variance.empty:
                return float(per_round_variance.mean())

        total_variance = ticks_df[coord_cols].var(ddof=0).fillna(0.0).sum()
        return float(total_variance)

    def _analyze_counter_strafing(self, ticks_df: pd.DataFrame, total_rounds: int) -> Dict[str, float]:
        """Analyze counter-strafing patterns."""
        try:
            velocity_magnitude = np.sqrt(
                ticks_df['velocity_X']**2 + ticks_df['velocity_Y']**2
            )
            velocity_changes = velocity_magnitude.diff().fillna(0.0)
            rapid_stops = (
                (velocity_changes < config.COUNTER_STRAFE_THRESHOLD) & 
                (velocity_magnitude.shift(1) > config.COUNTER_STRAFE_MIN_VELOCITY)
            )
            counter_strafe_events = int(rapid_stops.sum())

            return {
                'counter_strafe_frequency': float(counter_strafe_events / max(total_rounds, 1)),
                'avg_velocity': float(velocity_magnitude.mean()),
                'max_velocity': float(velocity_magnitude.max())
            }
        except Exception:
            return {'counter_strafe_frequency': 0.0, 'avg_velocity': 0.0, 'max_velocity': 0.0}

    def _calculate_movement_smoothness(self, ticks_df: pd.DataFrame) -> float:
        """Calculate movement smoothness (inverse of jerkiness)."""
        try:
            if 'velocity_X' in ticks_df.columns and 'velocity_Y' in ticks_df.columns:
                velocity_magnitude = np.sqrt(
                    ticks_df['velocity_X']**2 + ticks_df['velocity_Y']**2
                )
                velocity_changes = velocity_magnitude.diff().abs().fillna(0.0)
                return float(1 / (1 + velocity_changes.mean()))
            return 0.0
        except Exception:
            return 0.0

    def _analyze_peek_patterns(self, ticks_df: pd.DataFrame, total_rounds: int) -> Dict[str, float]:
        """Analyze peeking/positioning change patterns."""
        if 'X' not in ticks_df.columns or 'Y' not in ticks_df.columns:
            return {
                'avg_peek_distance_per_round': 0.0,
                'max_peek_distance_per_round': 0.0,
                'total_peek_events_per_round': 0.0
            }

        displacement = np.sqrt(
            ticks_df['X'].diff().fillna(0.0)**2 +
            ticks_df['Y'].diff().fillna(0.0)**2
        )

        if 'round_num' in ticks_df.columns:
            round_numbers = ticks_df['round_num']
            per_round_total = displacement.groupby(round_numbers).sum()
            per_round_max = displacement.groupby(round_numbers).max()
            per_round_events = (
                (displacement > config.SIGNIFICANT_MOVEMENT_THRESHOLD)
                .groupby(round_numbers)
                .sum()
            )

            return {
                'avg_peek_distance_per_round': float(per_round_total.mean() if not per_round_total.empty else 0.0),
                'max_peek_distance_per_round': float(per_round_max.mean() if not per_round_max.empty else 0.0),
                'total_peek_events_per_round': float(per_round_events.mean() if not per_round_events.empty else 0.0)
            }

        # Fallback when round attribution is missing
        return {
            'avg_peek_distance_per_round': float(displacement.sum() / max(total_rounds, 1)),
            'max_peek_distance_per_round': float(displacement.max()),
            'total_peek_events_per_round': float(
                displacement.gt(config.SIGNIFICANT_MOVEMENT_THRESHOLD).sum() / max(total_rounds, 1)
            )
        }
