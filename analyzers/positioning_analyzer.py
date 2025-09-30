# analyzers/positioning_analyzer.py
"""Positioning preference analysis for CS:GO players with enhanced detection."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from data_structures import PositioningSignature
import config

class PositioningAnalyzer:
    """Analyzes player positioning preferences and map coverage with enhanced detection."""
    
    def analyze(self, ticks_df: pd.DataFrame, total_rounds: int) -> PositioningSignature:
        """Analyze positioning patterns with enhanced detection."""
        if 'X' not in ticks_df.columns or 'Y' not in ticks_df.columns:
            return PositioningSignature(map_coverage_per_round=0.0)
        
        map_name = config.get_current_map_name()
        map_positions = config.get_current_map_positions()
        
        print(f"    Enhanced positioning analysis for {total_rounds} rounds on {map_name}")
        
        # Separate by side
        ct_ticks = ticks_df[ticks_df.get('player_side', '') == 'CT'] if 'player_side' in ticks_df.columns else pd.DataFrame()
        t_ticks = ticks_df[ticks_df.get('player_side', '') == 'T'] if 'player_side' in ticks_df.columns else pd.DataFrame()
        
        position_preferences = {}
        
        # Analyze each side with enhanced detection
        if not ct_ticks.empty:
            ct_positions = self._analyze_positions_enhanced(ct_ticks, map_positions, "CT")
            for pos_name, time_fraction in ct_positions.items():
                position_preferences[f"ct_{pos_name}"] = time_fraction
        
        if not t_ticks.empty:
            t_positions = self._analyze_positions_enhanced(t_ticks, map_positions, "T")
            for pos_name, time_fraction in t_positions.items():
                position_preferences[f"t_{pos_name}"] = time_fraction
        
        # Calculate map coverage
        map_coverage = self._calculate_map_coverage(ticks_df)
        
        # Calculate side-specific coverage
        if not ct_ticks.empty:
            ct_coverage = self._calculate_map_coverage(ct_ticks)
            position_preferences['ct_map_coverage'] = ct_coverage / max(1, len(ct_ticks)) * 1000
        
        if not t_ticks.empty:
            t_coverage = self._calculate_map_coverage(t_ticks)
            position_preferences['t_map_coverage'] = t_coverage / max(1, len(t_ticks)) * 1000
        
        return PositioningSignature(
            map_coverage_per_round=map_coverage / total_rounds,
            position_preferences=position_preferences
        )
    
    def _analyze_positions_enhanced(self, ticks_df: pd.DataFrame, 
                                   map_positions: Dict, side: str) -> Dict[str, float]:
        """Enhanced position analysis using best-match scoring."""
        total_ticks = len(ticks_df)
        if total_ticks == 0 or not map_positions:
            return {}
        
        print(f"    Enhanced analysis for {side} side ({total_ticks} ticks)")
        
        # For each tick, find the best matching position
        position_assignments = []
        
        for idx, row in ticks_df.iterrows():
            x, y = row['X'], row['Y']
            z = row.get('Z', 0)
            
            best_position = find_best_position_match(x, y, z, map_positions)
            position_assignments.append(best_position)
        
        # Count time in each position
        position_time = {}
        for position_name in set(position_assignments):
            if position_name:
                count = position_assignments.count(position_name)
                time_fraction = count / total_ticks
                position_time[position_name] = time_fraction
                
                if time_fraction > 0.02:
                    print(f"      {side} {position_name}: {time_fraction:.3f} ({time_fraction*100:.1f}%)")
        
        return position_time
    
    def _calculate_map_coverage(self, ticks_df: pd.DataFrame) -> float:
        """Calculate total map area covered."""
        try:
            if ticks_df.empty:
                return 0.0
            x_range = ticks_df['X'].max() - ticks_df['X'].min()
            y_range = ticks_df['Y'].max() - ticks_df['Y'].min()
            return float(x_range * y_range)
        except Exception:
            return 0.0


# ============================================================================
# SHARED POSITION DETECTION FUNCTIONS
# Used by both PositioningAnalyzer and CombatAnalyzer
# ============================================================================

def find_best_position_match(x: float, y: float, z: float, 
                            map_positions: Dict) -> Optional[str]:
    """Find the best matching position using weighted scoring.
    
    This is a shared function used by both positioning and combat analysis.
    """
    best_score = -float('inf')
    best_position = None
    
    for pos_name, pos_coords in map_positions.items():
        score = calculate_position_score(x, y, z, pos_coords)
        
        if score > best_score:
            best_score = score
            best_position = pos_name
    
    # Only return position if score is above threshold
    return best_position if best_score > 0 else None


def calculate_position_score(x: float, y: float, z: float, 
                            pos_coords: Dict) -> float:
    """Calculate how well a point matches a position using multiple criteria.
    
    Scoring components:
    1. Range check (is point inside bounds?) - Base requirement
    2. Distance from center - Closer = better
    3. Normalized distance (relative to position size) - More precise
    4. Size factor - Prefer smaller, more specific areas
    """
    x_range = pos_coords['x_range']
    y_range = pos_coords['y_range']
    z_range = pos_coords.get('z_range', (-float('inf'), float('inf')))
    
    # 1. Check if point is within bounds (required)
    in_x_range = x_range[0] <= x <= x_range[1]
    in_y_range = y_range[0] <= y <= y_range[1]
    in_z_range = z_range[0] <= z <= z_range[1]
    
    if not (in_x_range and in_y_range and in_z_range):
        return -1  # Not in this position
    
    # 2. Calculate distance from center
    center = pos_coords.get('center', [
        (x_range[0] + x_range[1]) / 2,
        (y_range[0] + y_range[1]) / 2,
        (z_range[0] + z_range[1]) / 2 if z_range != (-float('inf'), float('inf')) else 0
    ])
    
    distance = np.sqrt(
        (x - center[0])**2 + 
        (y - center[1])**2 + 
        (z - center[2])**2
    )
    
    # 3. Normalize by position size
    position_size = np.sqrt(
        (x_range[1] - x_range[0])**2 + 
        (y_range[1] - y_range[0])**2
    )
    
    # Avoid division by zero
    if position_size == 0:
        normalized_distance = 0
    else:
        normalized_distance = distance / position_size
    
    # 4. Calculate score (inverse of normalized distance)
    # Closer to center = higher score
    score = 1.0 / (1.0 + normalized_distance)
    
    # 5. Bonus for smaller, more specific positions
    # This helps prefer specific areas over large general areas
    size_factor = 1.0 / (1.0 + position_size / 1000)
    
    final_score = score * (1.0 + size_factor * 0.5)
    
    return final_score


# ============================================================================
# HELPER FUNCTIONS FOR MAP EXTRACTION AND ANALYSIS
# ============================================================================

def calculate_enhanced_position_info(place_data: pd.DataFrame) -> Dict:
    """Calculate comprehensive position metadata for map extraction."""
    x_min, x_max = place_data['X'].min(), place_data['X'].max()
    y_min, y_max = place_data['Y'].min(), place_data['Y'].max()
    z_min, z_max = place_data['Z'].min(), place_data['Z'].max()
    
    # Add padding (reduced from 0.1 to 0.05 for better precision)
    x_padding = (x_max - x_min) * 0.05
    y_padding = (y_max - y_min) * 0.05
    z_padding = (z_max - z_min) * 0.05
    
    x_range = [float(x_min - x_padding), float(x_max + x_padding)]
    y_range = [float(y_min - y_padding), float(y_max + y_padding)]
    z_range = [float(z_min - z_padding), float(z_max + z_padding)]
    
    # Calculate comprehensive metadata
    return {
        'x_range': x_range,
        'y_range': y_range,
        'z_range': z_range,
        'center': [
            float(place_data['X'].mean()),
            float(place_data['Y'].mean()),
            float(place_data['Z'].mean())
        ],
        'median_point': [
            float(place_data['X'].median()),
            float(place_data['Y'].median()),
            float(place_data['Z'].median())
        ],
        'sample_count': len(place_data),
        'x_std': float(place_data['X'].std()),
        'y_std': float(place_data['Y'].std()),
        'z_std': float(place_data['Z'].std()),
        # Additional useful metrics
        'density': len(place_data) / (
            (x_range[1] - x_range[0]) * (y_range[1] - y_range[0])
        ) if (x_range[1] - x_range[0]) * (y_range[1] - y_range[0]) > 0 else 0,
        'size': float(np.sqrt(
            (x_range[1] - x_range[0])**2 + 
            (y_range[1] - y_range[0])**2
        )),
        # 95th percentile bounds (tighter, excludes outliers)
        'x_range_95': [
            float(place_data['X'].quantile(0.025)),
            float(place_data['X'].quantile(0.975))
        ],
        'y_range_95': [
            float(place_data['Y'].quantile(0.025)),
            float(place_data['Y'].quantile(0.975))
        ],
        'z_range_95': [
            float(place_data['Z'].quantile(0.025)),
            float(place_data['Z'].quantile(0.975))
        ]
    }


def analyze_position_overlaps(map_positions: Dict) -> Dict:
    """Analyze which positions overlap and by how much."""
    overlaps = {}
    
    position_names = list(map_positions.keys())
    for i, pos1_name in enumerate(position_names):
        for pos2_name in position_names[i+1:]:
            pos1 = map_positions[pos1_name]
            pos2 = map_positions[pos2_name]
            
            overlap = calculate_range_overlap(pos1, pos2)
            
            if overlap > 0:
                pair = f"{pos1_name} <-> {pos2_name}"
                overlaps[pair] = {
                    'overlap_percentage': overlap,
                    'positions': [pos1_name, pos2_name]
                }
    
    return overlaps


def calculate_range_overlap(pos1: Dict, pos2: Dict) -> float:
    """Calculate the percentage overlap between two position ranges."""
    # Calculate overlap in each dimension
    x_overlap = calculate_1d_overlap(pos1['x_range'], pos2['x_range'])
    y_overlap = calculate_1d_overlap(pos1['y_range'], pos2['y_range'])
    z_overlap = calculate_1d_overlap(
        pos1.get('z_range', [-1000, 1000]), 
        pos2.get('z_range', [-1000, 1000])
    )
    
    # 3D overlap is the product of overlaps in each dimension
    return x_overlap * y_overlap * z_overlap


def calculate_1d_overlap(range1: Tuple, range2: Tuple) -> float:
    """Calculate overlap ratio for a single dimension."""
    # Find intersection
    start = max(range1[0], range2[0])
    end = min(range1[1], range2[1])
    
    if start >= end:
        return 0.0
    
    intersection = end - start
    
    # Calculate smaller range size
    size1 = range1[1] - range1[0]
    size2 = range2[1] - range2[0]
    smaller_size = min(size1, size2)
    
    return intersection / smaller_size if smaller_size > 0 else 0.0