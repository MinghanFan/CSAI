# analyzers/combat_analyzer.py
"""Combat performance and style analysis for CS:GO players."""

import pandas as pd
from typing import Dict
from data_structures import CombatSignature
import config

class CombatAnalyzer:
    """Analyzes player combat patterns and performance metrics."""
    
    def analyze(self, kills_df: pd.DataFrame, damages_df: pd.DataFrame, 
                total_rounds: int) -> CombatSignature:
        """Analyze combat performance and style patterns."""
        print(f"    CombatAnalyzer: {len(kills_df)} kills, {len(damages_df)} damage events "
              f"across {total_rounds} rounds")
        
        combat_stats = self._analyze_kills(kills_df, total_rounds)
        damage_stats = self._analyze_damage(damages_df, total_rounds)
        combat_stats.update(damage_stats)
        
        # Calculate combined efficiency stats
        if combat_stats['total_damage'] > 0:
            combat_stats['kill_efficiency'] = float(
                combat_stats['total_kills'] / (combat_stats['total_damage'] / 100)
            )
        else:
            combat_stats['kill_efficiency'] = 0.0
        
        print(f"    Combat analysis result: {len(combat_stats)} metrics")
        return CombatSignature(**combat_stats)
    
    def _analyze_kills(self, kills_df: pd.DataFrame, total_rounds: int) -> Dict[str, any]:
        """Analyze kill-related statistics."""
        combat_stats = {}
        
        if not kills_df.empty:
            total_kills = len(kills_df)
            combat_stats['kills_per_round'] = float(total_kills / total_rounds)
            combat_stats['total_kills'] = total_kills
            
            # Weapon preferences
            if 'weapon' in kills_df.columns:
                weapon_counts = kills_df['weapon'].value_counts()
                if len(weapon_counts) > 0:
                    combat_stats['primary_weapon'] = str(weapon_counts.index[0])
                    combat_stats['weapon_diversity'] = len(weapon_counts)
                else:
                    combat_stats['primary_weapon'] = 'unknown'
                    combat_stats['weapon_diversity'] = 0
            
            # Headshot ratio
            if 'headshot' in kills_df.columns:
                headshot_ratio = kills_df['headshot'].sum() / len(kills_df) if len(kills_df) > 0 else 0
                combat_stats['headshot_ratio'] = float(headshot_ratio)
            
            # Multi-kill rounds (clutch potential)
            if 'round_num' in kills_df.columns:
                kills_per_round_series = kills_df.groupby('round_num').size()
                multi_kills = (kills_per_round_series >= 2).sum()
                combat_stats['multi_kill_rounds'] = int(multi_kills)
                combat_stats['clutch_potential'] = float(multi_kills / total_rounds)
            
            # Kill positions (aggressive vs defensive)
            if 'attacker_X' in kills_df.columns and 'attacker_Y' in kills_df.columns:
                kill_positions = self._analyze_kill_positions(kills_df)
                combat_stats.update(kill_positions)
        else:
            combat_stats.update({
                'kills_per_round': 0.0,
                'total_kills': 0,
                'primary_weapon': 'none',
                'weapon_diversity': 0,
                'headshot_ratio': 0.0,
                'multi_kill_rounds': 0,
                'clutch_potential': 0.0
            })
        
        return combat_stats
    
    def _analyze_damage(self, damages_df: pd.DataFrame, total_rounds: int) -> Dict[str, any]:
        """Analyze damage-related statistics."""
        damage_stats = {}
        
        if not damages_df.empty and 'dmg_health' in damages_df.columns:
            total_damage = damages_df['dmg_health'].sum()
            damage_stats['damage_per_round'] = float(total_damage / total_rounds)
            damage_stats['total_damage'] = int(total_damage)
            damage_stats['avg_damage_per_hit'] = float(damages_df['dmg_health'].mean())
            damage_stats['damage_consistency'] = float(1 / (1 + damages_df['dmg_health'].std()))
            
            # First shot accuracy (proxy through damage)
            if 'round_num' in damages_df.columns and 'victim_steamid' in damages_df.columns:
                first_damages = damages_df.groupby(['round_num', 'victim_steamid']).first()
                if len(first_damages) > 0:
                    damage_stats['first_shot_damage'] = float(first_damages['dmg_health'].mean())
                else:
                    damage_stats['first_shot_damage'] = 0.0
        else:
            damage_stats.update({
                'damage_per_round': 0.0,
                'total_damage': 0,
                'avg_damage_per_hit': 0.0,
                'damage_consistency': 0.0,
                'first_shot_damage': 0.0
            })
        
        return damage_stats
    
    def _analyze_kill_positions(self, kills_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze where player gets kills to determine playstyle."""
        total_kills = len(kills_df)
        
        if total_kills == 0:
            return {'kill_area_diversity': 0.0, 'aggressive_kill_ratio': 0.0, 'kill_position_variance': 0.0}
        
        # Count kills in each area
        area_kills = {}
        for area_name, coords in config.KILL_AREAS.items():
            if area_name == 'aggressive_areas':
                continue
                
            area_filter = (
                (kills_df['attacker_X'].between(coords['x_range'][0], coords['x_range'][1])) &
                (kills_df['attacker_Y'].between(coords['y_range'][0], coords['y_range'][1]))
            )
            area_kills[area_name] = area_filter.sum()
        
        # Calculate diversity (how spread out kills are)
        non_zero_areas = sum(1 for kills in area_kills.values() if kills > 0)
        kill_area_diversity = float(non_zero_areas / len(area_kills))
        
        # Estimate aggressive vs defensive kills based on position variance
        position_variance = kills_df['attacker_X'].var() + kills_df['attacker_Y'].var()
        
        return {
            'kill_area_diversity': kill_area_diversity,
            'kill_position_variance': float(position_variance)
        }