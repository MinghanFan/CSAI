# analyzers/combat_analyzer.py
"""Combat performance and style analysis for CS:GO players with side separation."""

import pandas as pd
from typing import Dict
from data_structures import CombatSignature
import config

class CombatAnalyzer:
    """Analyzes player combat patterns and performance metrics by side."""
    
    def analyze(self, kills_df: pd.DataFrame, damages_df: pd.DataFrame, 
                total_rounds: int) -> CombatSignature:
        """Analyze combat performance separated by CT and T sides."""
        
        map_name = config.get_current_map_name()
        kill_areas = config.get_current_map_positions()
        
        print(f"    CombatAnalyzer: {len(kills_df)} kills, {len(damages_df)} damage events "
              f"across {total_rounds} rounds on {map_name}")
        
        # Separate by side using the 'player_side' column we added
        ct_kills = kills_df[kills_df.get('player_side', '') == 'CT'] if 'player_side' in kills_df.columns else pd.DataFrame()
        t_kills = kills_df[kills_df.get('player_side', '') == 'T'] if 'player_side' in kills_df.columns else pd.DataFrame()
        ct_damages = damages_df[damages_df.get('player_side', '') == 'CT'] if 'player_side' in damages_df.columns else pd.DataFrame()
        t_damages = damages_df[damages_df.get('player_side', '') == 'T'] if 'player_side' in damages_df.columns else pd.DataFrame()
        
        print(f"    CT: {len(ct_kills)} kills, {len(ct_damages)} damages")
        print(f"    T: {len(t_kills)} kills, {len(t_damages)} damages")
        
        # Analyze each side separately
        combat_stats = {}
        
        # Overall stats (combined)
        overall_kills = self._analyze_kills(kills_df, total_rounds, kill_areas, "Overall")
        overall_damage = self._analyze_damage(damages_df, total_rounds, "Overall")
        combat_stats.update(overall_kills)
        combat_stats.update(overall_damage)
        
        # CT side stats
        if not ct_kills.empty or not ct_damages.empty:
            ct_kill_stats = self._analyze_kills(ct_kills, total_rounds, kill_areas, "CT")
            ct_damage_stats = self._analyze_damage(ct_damages, total_rounds, "CT")
            
            # Add CT prefix to stats
            for key, value in ct_kill_stats.items():
                if key not in ['primary_weapon']:  # Don't prefix weapon names
                    combat_stats[f"ct_{key}"] = value
            for key, value in ct_damage_stats.items():
                combat_stats[f"ct_{key}"] = value
        
        # T side stats
        if not t_kills.empty or not t_damages.empty:
            t_kill_stats = self._analyze_kills(t_kills, total_rounds, kill_areas, "T")
            t_damage_stats = self._analyze_damage(t_damages, total_rounds, "T")
            
            # Add T prefix to stats
            for key, value in t_kill_stats.items():
                if key not in ['primary_weapon']:  # Don't prefix weapon names
                    combat_stats[f"t_{key}"] = value
            for key, value in t_damage_stats.items():
                combat_stats[f"t_{key}"] = value
        
        # Calculate combined efficiency stats
        if combat_stats['total_damage'] > 0:
            combat_stats['kill_efficiency'] = float(
                combat_stats['total_kills'] / (combat_stats['total_damage'] / 100)
            )
        else:
            combat_stats['kill_efficiency'] = 0.0
        
        print(f"    Combat analysis result: {len(combat_stats)} metrics")
        
        # Create CombatSignature and add dynamic attributes for side-specific stats
        signature = CombatSignature(**{k: v for k, v in combat_stats.items() 
                                     if k in CombatSignature.__dataclass_fields__})
        
        # Add side-specific stats as dynamic attributes
        for key, value in combat_stats.items():
            if key.startswith(('ct_', 't_')) and key not in CombatSignature.__dataclass_fields__:
                setattr(signature, key, value)
        
        return signature
    
    def _analyze_kills(self, kills_df: pd.DataFrame, total_rounds: int, 
                      kill_areas: Dict, side: str = "") -> Dict[str, any]:
        """Analyze kill-related statistics for a specific side."""
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
            
            # Kill positions analysis (now map and side specific)
            if 'attacker_X' in kills_df.columns and 'attacker_Y' in kills_df.columns:
                kill_positions = self._analyze_kill_positions(kills_df, kill_areas, side)
                combat_stats.update(kill_positions)
                
            if side:
                print(f"      {side} side: {total_kills} kills analyzed")
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
    
    def _analyze_damage(self, damages_df: pd.DataFrame, total_rounds: int, 
                       side: str = "") -> Dict[str, any]:
        """Analyze damage-related statistics for a specific side."""
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
                    
            if side:
                print(f"      {side} side: {total_damage} total damage analyzed")
        else:
            damage_stats.update({
                'damage_per_round': 0.0,
                'total_damage': 0,
                'avg_damage_per_hit': 0.0,
                'damage_consistency': 0.0,
                'first_shot_damage': 0.0
            })
        
        return damage_stats
    
    def _analyze_kill_positions(self, kills_df: pd.DataFrame, 
                               kill_areas: Dict, side: str = "") -> Dict[str, float]:
        """Analyze where player gets kills to determine playstyle by side."""
        total_kills = len(kills_df)
        
        if total_kills == 0:
            return {'kill_area_diversity': 0.0, 'aggressive_kill_ratio': 0.0, 'kill_position_variance': 0.0}
        
        if not kill_areas:
            try:
                position_variance = float(kills_df['attacker_X'].var() + kills_df['attacker_Y'].var())
            except:
                position_variance = 0.0
            return {'kill_area_diversity': 0.0, 'aggressive_kill_ratio': 0.0, 'kill_position_variance': position_variance}
        
        side_prefix = f"{side} " if side else ""
        print(f"      Analyzing {side_prefix}kill positions across {len(kill_areas)} areas")
        
        # Count kills in each area
        area_kills = {}
        total_categorized_kills = 0
        
        for area_name, coords in kill_areas.items():
            try:
                x_range = coords['x_range']
                y_range = coords['y_range']
                
                area_filter = (
                    (kills_df['attacker_X'].between(x_range[0], x_range[1])) &
                    (kills_df['attacker_Y'].between(y_range[0], y_range[1]))
                )
                
                # Add Z-axis filtering if available
                if 'attacker_Z' in kills_df.columns and 'z_range' in coords:
                    z_range = coords['z_range']
                    area_filter = area_filter & (
                        kills_df['attacker_Z'].between(z_range[0], z_range[1])
                    )
                
                kills_in_area = area_filter.sum()
                area_kills[area_name] = kills_in_area
                total_categorized_kills += kills_in_area
                
                if kills_in_area > 0:
                    percentage = (kills_in_area / total_kills) * 100
                    print(f"        {side_prefix}{area_name}: {kills_in_area} kills ({percentage:.1f}%)")
                    
            except Exception as e:
                print(f"        Error analyzing {side_prefix}kills in {area_name}: {e}")
                area_kills[area_name] = 0
        
        # Calculate diversity (how spread out kills are)
        non_zero_areas = sum(1 for kills in area_kills.values() if kills > 0)
        kill_area_diversity = float(non_zero_areas / len(area_kills)) if len(area_kills) > 0 else 0.0
        
        # Calculate aggressive vs defensive based on specific areas and side
        aggressive_kills = 0
        
        # Different aggression metrics based on side
        if side == "CT":
            # For CT: kills in T areas or bomb sites are aggressive
            for area_name, kills in area_kills.items():
                if any(keyword in area_name.lower() for keyword in ['tspawn', 'bombsite', 'site']):
                    aggressive_kills += kills
        elif side == "T":
            # For T: kills in CT areas or defensive positions are aggressive
            for area_name, kills in area_kills.items():
                if any(keyword in area_name.lower() for keyword in ['ctspawn', 'site']):
                    aggressive_kills += kills
        else:
            # Overall: general aggressive areas
            for area_name, kills in area_kills.items():
                if any(keyword in area_name.lower() for keyword in ['bombsite', 'site']) and 'spawn' not in area_name.lower():
                    aggressive_kills += kills
        
        aggressive_ratio = float(aggressive_kills / total_kills) if total_kills > 0 else 0.0
        
        # Position variance (spread of kill locations)
        try:
            position_variance = float(kills_df['attacker_X'].var() + kills_df['attacker_Y'].var())
        except:
            position_variance = 0.0
        
        print(f"        {side_prefix}Kill analysis: {non_zero_areas}/{len(area_kills)} areas used, "
              f"{total_categorized_kills}/{total_kills} kills categorized")
        
        return {
            'kill_area_diversity': kill_area_diversity,
            'aggressive_kill_ratio': aggressive_ratio,
            'kill_position_variance': position_variance
        }