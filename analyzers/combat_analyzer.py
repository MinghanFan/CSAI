# analyzers/combat_analyzer.py
"""Combat performance and style analysis for CS:GO players with side separation."""

import pandas as pd
from typing import Any, Dict, List, Optional
from data_structures import CombatSignature
import config
# Import the shared position detection functions
from analyzers.positioning_analyzer import find_best_position_match

class CombatAnalyzer:
    """Analyzes player combat patterns and performance metrics"""
    
    def analyze(self, kills_df: pd.DataFrame, damages_df: pd.DataFrame,
                deaths_df: pd.DataFrame, damage_taken_df: pd.DataFrame,
                total_rounds: int, side_rounds: Optional[Dict[str, int]] = None) -> CombatSignature:
        """Analyze combat performance separated by CT and T sides."""

        map_name = config.get_current_map_name()
        kill_areas = config.get_current_map_positions()

        print(f"    CombatAnalyzer: {len(kills_df)} kills, {len(damages_df)} damage events, "
              f"{len(deaths_df)} deaths, {len(damage_taken_df)} damage taken events "
              f"across {total_rounds} rounds on {map_name}")
        
        # Separate by side using the 'player_side' column we added
        ct_kills = kills_df[kills_df.get('player_side', '') == 'CT'] if 'player_side' in kills_df.columns else pd.DataFrame()
        t_kills = kills_df[kills_df.get('player_side', '') == 'T'] if 'player_side' in kills_df.columns else pd.DataFrame()
        ct_damages = damages_df[damages_df.get('player_side', '') == 'CT'] if 'player_side' in damages_df.columns else pd.DataFrame()
        t_damages = damages_df[damages_df.get('player_side', '') == 'T'] if 'player_side' in damages_df.columns else pd.DataFrame()
        ct_deaths = deaths_df[deaths_df.get('player_side', '') == 'CT'] if 'player_side' in deaths_df.columns else pd.DataFrame()
        t_deaths = deaths_df[deaths_df.get('player_side', '') == 'T'] if 'player_side' in deaths_df.columns else pd.DataFrame()
        ct_damage_taken = damage_taken_df[damage_taken_df.get('player_side', '') == 'CT'] if 'player_side' in damage_taken_df.columns else pd.DataFrame()
        t_damage_taken = damage_taken_df[damage_taken_df.get('player_side', '') == 'T'] if 'player_side' in damage_taken_df.columns else pd.DataFrame()
        
        print(f"    CT: {len(ct_kills)} kills, {len(ct_damages)} damage events, {len(ct_deaths)} deaths, {len(ct_damage_taken)} damage taken")
        print(f"    T: {len(t_kills)} kills, {len(t_damages)} damage events, {len(t_deaths)} deaths, {len(t_damage_taken)} damage taken")
        
        # Determine rounds played per side for proper normalization
        side_rounds = side_rounds or {}
        ct_rounds = self._resolve_rounds_played(side_rounds.get('CT'),
                                               [ct_kills, ct_damages, ct_deaths, ct_damage_taken],
                                               total_rounds)
        t_rounds = self._resolve_rounds_played(side_rounds.get('T'),
                                              [t_kills, t_damages, t_deaths, t_damage_taken],
                                              total_rounds)

        # Analyze each side separately
        combat_stats = {}

        # Overall stats (combined)
        overall_kills = self._analyze_kills(kills_df, total_rounds, kill_areas, "Overall")
        overall_damage = self._analyze_damage(damages_df, total_rounds, "Overall")
        overall_deaths = self._analyze_deaths(deaths_df, total_rounds, kill_areas, "Overall")
        overall_dmg_received = self._analyze_damage_received(damage_taken_df, total_rounds, "Overall")
        
        combat_stats.update(overall_kills)
        combat_stats.update(overall_damage)
        combat_stats.update(overall_deaths)
        combat_stats.update(overall_dmg_received)
        
        # CT side stats
        if not ct_kills.empty or not ct_damages.empty or not ct_deaths.empty or not ct_damage_taken.empty:
            ct_kill_stats = self._analyze_kills(ct_kills, ct_rounds, kill_areas, "CT")
            ct_damage_stats = self._analyze_damage(ct_damages, ct_rounds, "CT")
            ct_death_stats = self._analyze_deaths(ct_deaths, ct_rounds, kill_areas, "CT")
            ct_dmg_received_stats = self._analyze_damage_received(ct_damage_taken, ct_rounds, "CT")
            
            # Add CT prefix to stats
            for key, value in ct_kill_stats.items():
                if key not in ['primary_weapon']:  # Don't prefix weapon names
                    combat_stats[f"ct_{key}"] = value
            for key, value in ct_damage_stats.items():
                combat_stats[f"ct_{key}"] = value
            for key, value in ct_death_stats.items():
                combat_stats[f"ct_{key}"] = value
            for key, value in ct_dmg_received_stats.items():
                combat_stats[f"ct_{key}"] = value
        
        # T side stats
        if not t_kills.empty or not t_damages.empty or not t_deaths.empty or not t_damage_taken.empty:
            t_kill_stats = self._analyze_kills(t_kills, t_rounds, kill_areas, "T")
            t_damage_stats = self._analyze_damage(t_damages, t_rounds, "T")
            t_death_stats = self._analyze_deaths(t_deaths, t_rounds, kill_areas, "T")
            t_dmg_received_stats = self._analyze_damage_received(t_damage_taken, t_rounds, "T")
            
            # Add T prefix to stats
            for key, value in t_kill_stats.items():
                if key not in ['primary_weapon']:  # Don't prefix weapon names
                    combat_stats[f"t_{key}"] = value
            for key, value in t_damage_stats.items():
                combat_stats[f"t_{key}"] = value
            for key, value in t_death_stats.items():
                combat_stats[f"t_{key}"] = value
            for key, value in t_dmg_received_stats.items():
                combat_stats[f"t_{key}"] = value
        
        # TODO: need better way to define efficiency
        # Calculate combined efficiency stats
        total_damage = combat_stats.get('total_damage', 0)
        combat_stats['kill_efficiency'] = (
            float((combat_stats.get('total_kills', 0) / max(total_damage, 1)) * 100)
            if total_damage > 0 else 0.0
        )
        
        combat_stats['total_rounds'] = int(total_rounds)
        combat_stats['ct_rounds'] = int(ct_rounds)
        combat_stats['t_rounds'] = int(t_rounds)

        print(f"    Combat analysis result: {len(combat_stats)} metrics")
        
        # Create CombatSignature and add dynamic attributes for side-specific stats
        signature = CombatSignature(**{k: v for k, v in combat_stats.items() 
                                     if k in CombatSignature.__dataclass_fields__})
        
        # Add side-specific stats as dynamic attributes
        for key, value in combat_stats.items():
            if key.startswith(('ct_', 't_')) and key not in CombatSignature.__dataclass_fields__:
                setattr(signature, key, value)
        
        return signature
    
    def _analyze_kills(self, kills_df: pd.DataFrame, rounds_played: int,
                      kill_areas: Dict, side: str = "") -> Dict[str, Any]:
        """Analyze kill-related statistics for a specific side."""
        combat_stats = {}

        if not kills_df.empty:
            total_kills = len(kills_df)
            combat_stats['kills_per_round'] = float(total_kills / max(rounds_played, 1))
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
            
            # TODO: rename clutch potential
            # Multi-kill rounds
            if 'round_num' in kills_df.columns:
                kills_per_round_series = kills_df.groupby('round_num').size()
                multi_kills = (kills_per_round_series >= 2).sum()
                combat_stats['multi_kill_rounds'] = int(multi_kills)
                combat_stats['clutch_potential'] = float(multi_kills / max(rounds_played, 1))
            
            # Kill positions analysis (now using enhanced detection)
            if 'attacker_X' in kills_df.columns and 'attacker_Y' in kills_df.columns:
                kill_positions = self._analyze_kill_positions_enhanced(kills_df, kill_areas, side)
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
    
    def _analyze_damage(self, damages_df: pd.DataFrame, rounds_played: int, 
                       side: str = "") -> Dict[str, Any]:
        """Analyze damage-related statistics for a specific side."""
        damage_stats = {}

        # TODO: consider 'dmg_health_real'?
        if not damages_df.empty and 'dmg_health' in damages_df.columns:
            total_damage = damages_df['dmg_health'].sum()
            damage_stats['damage_per_round'] = float(total_damage / max(rounds_played, 1))
            damage_stats['total_damage'] = int(total_damage)
            damage_stats['avg_damage_per_hit'] = float(damages_df['dmg_health'].mean())
            mean_damage = damages_df['dmg_health'].mean()
            std_damage = damages_df['dmg_health'].std()
            if mean_damage and mean_damage > 0:
                damage_stats['damage_consistency'] = float(1 / (1 + (std_damage / mean_damage)))
            else:
                damage_stats['damage_consistency'] = 0.0
            
            # TODO: modify this to be more meaningful
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

    def _analyze_deaths(self, deaths_df: pd.DataFrame, rounds_played: int,
                        kill_areas: Dict, side: str = "") -> Dict[str, Any]:
        """Analyze death-related statistics for a specific side."""
        death_stats = {
            'death_area_diversity': 0.0,
            'death_bombsite_ratio': 0.0,
            'death_position_variance': 0.0
        }
        
        if not deaths_df.empty and 'victim_steamid' in deaths_df.columns:
            total_deaths = len(deaths_df)
            death_stats['deaths_per_round'] = float(total_deaths / max(rounds_played, 1))
            death_stats['total_deaths'] = total_deaths
            
            if 'victim_X' in deaths_df.columns and 'victim_Y' in deaths_df.columns:
                death_positions = self._analyze_death_positions_enhanced(deaths_df, kill_areas, side)
                death_stats.update(death_positions)
            
            if side:
                print(f"      {side} side: {total_deaths} deaths analyzed")
        else:
            death_stats.update({
                'deaths_per_round': 0.0,
                'total_deaths': 0
            })
        
        return death_stats

    def _analyze_damage_received(self, damages_df: pd.DataFrame, rounds_played: int, 
                                 side: str = "") -> Dict[str, Any]:
        """Analyze damage received statistics for a specific side."""
        dmg_received_stats = {}
        
        if not damages_df.empty and 'dmg_health' in damages_df.columns:
            total_dmg_received = damages_df['dmg_health'].sum()
            dmg_received_stats['damage_received_per_round'] = float(total_dmg_received / max(rounds_played, 1))
            dmg_received_stats['total_damage_received'] = int(total_dmg_received)
            
            if side:
                print(f"      {side} side: {total_dmg_received} total damage received")
        else:
            dmg_received_stats.update({
                'damage_received_per_round': 0.0,
                'total_damage_received': 0
            })
        
        return dmg_received_stats

    def _analyze_death_positions_enhanced(self, deaths_df: pd.DataFrame,
                                          kill_areas: Dict, side: str = "") -> Dict[str, float]:
        """Analyze where the player dies using enhanced position detection."""
        total_deaths = len(deaths_df)
        if total_deaths == 0:
            return {
                'death_area_diversity': 0.0,
                'death_bombsite_ratio': 0.0,
                'death_position_variance': 0.0
            }

        if not kill_areas:
            try:
                position_variance = float(
                    deaths_df['victim_X'].var() +
                    deaths_df['victim_Y'].var() +
                    deaths_df.get('victim_Z', pd.Series([0]*len(deaths_df))).var()
                )
            except Exception:
                position_variance = 0.0
            return {
                'death_area_diversity': 0.0,
                'death_bombsite_ratio': 0.0,
                'death_position_variance': position_variance
            }

        side_prefix = f"{side} " if side else ""
        print(f"      Analyzing {side_prefix}death positions with enhanced detection")

        position_assignments = []
        for _, row in deaths_df.iterrows():
            x = row['victim_X']
            y = row['victim_Y']
            z = row.get('victim_Z', 0)
            best_position = find_best_position_match(x, y, z, kill_areas)
            position_assignments.append(best_position)

        area_deaths = {}
        for position_name in set(position_assignments):
            if position_name:
                count = position_assignments.count(position_name)
                area_deaths[position_name] = count
                percentage = (count / total_deaths) * 100
                print(f"        {side_prefix}{position_name}: {count} deaths ({percentage:.1f}%)")

        total_categorized = sum(area_deaths.values())
        non_zero_areas = len(area_deaths)
        death_area_diversity = float(non_zero_areas / max(len(kill_areas), 1))

        site_deaths = sum(
            deaths for area_name, deaths in area_deaths.items()
            if 'site' in area_name.lower()
        )
        bombsite_ratio = float(site_deaths / total_deaths)

        try:
            position_variance = float(
                deaths_df['victim_X'].var() +
                deaths_df['victim_Y'].var() +
                deaths_df.get('victim_Z', pd.Series([0]*len(deaths_df))).var()
            )
        except Exception:
            position_variance = 0.0

        print(f"        {side_prefix}Death analysis: {non_zero_areas}/{len(kill_areas)} areas used, "
              f"{total_categorized}/{total_deaths} deaths categorized")

        return {
            'death_area_diversity': death_area_diversity,
            'death_bombsite_ratio': bombsite_ratio,
            'death_position_variance': position_variance
        }

    def _resolve_rounds_played(self, provided_rounds: Optional[int],
                               data_frames: List[pd.DataFrame],
                               fallback_rounds: int) -> int:
        """Determine how many rounds were played for a side."""
        if provided_rounds and provided_rounds > 0:
            return int(provided_rounds)

        candidate = 0
        for df in data_frames:
            if df is None or df.empty:
                continue
            if 'round_id' in df.columns:
                candidate = max(candidate, df['round_id'].nunique())
            elif 'round_num' in df.columns:
                candidate = max(candidate, df['round_num'].nunique())

        if candidate > 0:
            return int(candidate)

        return max(int(fallback_rounds), 1)

    def _analyze_kill_positions_enhanced(self, kills_df: pd.DataFrame, 
                                        kill_areas: Dict, side: str = "") -> Dict[str, float]:
        """Analyze where player gets kills using enhanced position detection."""
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
        print(f"      Analyzing {side_prefix}kill positions with enhanced detection")
        
        # Use enhanced position detection for each kill
        position_assignments = []
        
        for idx, row in kills_df.iterrows():
            x = row['attacker_X']
            y = row['attacker_Y']
            z = row.get('attacker_Z', 0)
            
            best_position = find_best_position_match(x, y, z, kill_areas)
            position_assignments.append(best_position)
        
        # Count kills in each area
        area_kills = {}
        for position_name in set(position_assignments):
            if position_name:
                count = position_assignments.count(position_name)
                area_kills[position_name] = count
                
                percentage = (count / total_kills) * 100
                print(f"        {side_prefix}{position_name}: {count} kills ({percentage:.1f}%)")
        
        # Calculate diversity (how spread out kills are)
        total_categorized_kills = sum(area_kills.values())
        non_zero_areas = len(area_kills)
        kill_area_diversity = float(non_zero_areas / max(len(kill_areas), 1))

        # Share of kills taken at bomb sites (useful aggression proxy)
        site_kills = sum(
            kills for area_name, kills in area_kills.items()
            if 'site' in area_name.lower()
        )
        aggressive_ratio = float(site_kills / total_kills)

        # Position variance (spread of kill locations)
        try:
            position_variance = float(
                kills_df['attacker_X'].var() + 
                kills_df['attacker_Y'].var() + 
                kills_df.get('attacker_Z', pd.Series([0]*len(kills_df))).var()
            )
        except:
            position_variance = 0.0
        
        print(f"        {side_prefix}Kill analysis: {non_zero_areas}/{len(kill_areas)} areas used, "
              f"{total_categorized_kills}/{total_kills} kills categorized")
        
        return {
            'kill_area_diversity': kill_area_diversity,
            'aggressive_kill_ratio': aggressive_ratio,
            'kill_position_variance': position_variance
        }
