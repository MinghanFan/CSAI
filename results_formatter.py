# results_formatter.py
"""Formats and displays analysis results."""

from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
from data_structures import PlayerFingerprint
from player_comparison import PlayerComparison
import config

class ResultsFormatter:
    """Handles formatting and display of analysis results."""
    
    def __init__(self):
        self.player_comparison = PlayerComparison()
    
    def display_analysis_results(self, all_players: Dict[str, PlayerFingerprint], 
                                demos_processed: int, map_name: str):
        """Display comprehensive analysis results."""
        print("\n" + "="*60)
        print("PLAYER STYLE ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\n  Map: {map_name}")
        
        # Show individual fingerprints for key players
        self._display_key_player_fingerprints(all_players)
        
        # Compare players if we have enough data
        if len(all_players) >= 2:
            self._display_player_similarities(all_players)

        self.export_feature_matrix(all_players, map_name)

        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE!")
        print(f"Analyzed {len(all_players)} players across {demos_processed} matches on {map_name}")
        print("="*60)
    
    def _display_key_player_fingerprints(self, all_players: Dict[str, PlayerFingerprint]):
        """Display detailed fingerprints for key players."""
        for player_name in config.KEY_PLAYERS:
            if player_name in all_players:
                fingerprint = all_players[player_name]
                print(f"\n{player_name.upper()}:")
                
                # Display movement stats
                self._display_movement_stats(fingerprint)
                
                # Display positioning stats  
                self._display_positioning_stats(fingerprint)
                
                # Display combat stats
                self._display_combat_stats(fingerprint)

                # Display utility stats
                self._display_utility_stats(fingerprint)
    
    def _display_movement_stats(self, fingerprint: PlayerFingerprint):
        """Display movement statistics for a player."""
        movement = fingerprint.movement
        if movement:
            print("  Movement (per round):")
            self._print_stat("counter_strafe_frequency", movement.counter_strafe_frequency, 
                           precision=config.FLOAT_PRECISION_HIGH)
            self._print_stat("avg_velocity", movement.avg_velocity, 
                           precision=config.FLOAT_PRECISION_MED)
            self._print_stat("max_velocity", movement.max_velocity,
                           precision=config.FLOAT_PRECISION_MED)
            self._print_stat("movement_smoothness", movement.movement_smoothness,
                           precision=config.FLOAT_PRECISION_HIGH)
            self._print_stat("movement_distance_per_round", movement.movement_distance_per_round,
                           precision=config.FLOAT_PRECISION_LOW)
            self._print_stat("position_variance_per_round", movement.position_variance_per_round,
                           precision=config.FLOAT_PRECISION_LOW)
            self._print_stat("avg_peek_distance_per_round", movement.avg_peek_distance_per_round,
                           precision=config.FLOAT_PRECISION_LOW)
            self._print_stat("max_peek_distance_per_round", movement.max_peek_distance_per_round,
                           precision=config.FLOAT_PRECISION_LOW)
            self._print_stat("total_peek_events_per_round", movement.total_peek_events_per_round,
                           precision=config.FLOAT_PRECISION_HIGH)
    
    def _display_positioning_stats(self, fingerprint: PlayerFingerprint):
        """Display positioning statistics for a player with side breakdown."""
        positioning = fingerprint.positioning
        if positioning:
            print("  Positioning (Overall):")
            self._print_stat("map_coverage_per_round", positioning.map_coverage_per_round,
                           precision=config.FLOAT_PRECISION_LOW)
            
            # Show CT side positions
            ct_positions = positioning.get_ct_positions()
            if ct_positions:
                sorted_ct_positions = sorted(ct_positions.items(), key=lambda x: x[1], reverse=True)
                print("    CT Side - Top positions (time spent):")
                for pos_name, time_fraction in sorted_ct_positions[:3]:
                    if time_fraction > 0.01:
                        self._print_stat(f"  {pos_name}", time_fraction,
                                       precision=config.FLOAT_PRECISION_HIGH)
            
            # Show T side positions
            t_positions = positioning.get_t_positions()
            if t_positions:
                sorted_t_positions = sorted(t_positions.items(), key=lambda x: x[1], reverse=True)
                print("    T Side - Top positions (time spent):")
                for pos_name, time_fraction in sorted_t_positions[:3]:
                    if time_fraction > 0.01:
                        self._print_stat(f"  {pos_name}", time_fraction,
                                       precision=config.FLOAT_PRECISION_HIGH)
    
    def _display_combat_stats(self, fingerprint: PlayerFingerprint):
        """Display combat statistics for a player with side breakdown."""
        combat = fingerprint.combat
        if combat:
            print("  Combat (Overall):")
            self._print_stat("kills_per_round", combat.kills_per_round,
                           precision=config.FLOAT_PRECISION_MED)
            self._print_stat("damage_per_round", combat.damage_per_round,
                           precision=config.FLOAT_PRECISION_MED)
            self._print_stat("deaths_per_round", combat.deaths_per_round,
                           precision=config.FLOAT_PRECISION_MED)
            self._print_stat("damage_received_per_round", combat.damage_received_per_round,
                           precision=config.FLOAT_PRECISION_MED)
            self._print_stat("headshot_ratio", combat.headshot_ratio,
                           precision=config.FLOAT_PRECISION_HIGH)
            self._print_stat("clutch_potential", combat.clutch_potential,
                           precision=config.FLOAT_PRECISION_HIGH)
            self._print_stat("kill_efficiency", combat.kill_efficiency,
                           precision=config.FLOAT_PRECISION_HIGH)
            self._print_stat("kill_area_diversity", combat.kill_area_diversity,
                           precision=config.FLOAT_PRECISION_HIGH)
            
            if combat.primary_weapon != 'none':
                print(f"    primary_weapon: {combat.primary_weapon}")

            print(f"    total_rounds_played: {combat.total_rounds}")
            
            # Show side-specific stats
            ct_stats = combat.get_ct_stats()
            t_stats = combat.get_t_stats()

            if ct_stats:
                print("  Combat (CT Side):")
                print(f"    ct_rounds_played: {combat.ct_rounds}")
                self._print_stat("ct_kills_per_round", ct_stats.get('kills_per_round', 0.0),
                               precision=config.FLOAT_PRECISION_MED)
                self._print_stat("ct_damage_per_round", ct_stats.get('damage_per_round', 0.0),
                               precision=config.FLOAT_PRECISION_MED)
                self._print_stat("ct_deaths_per_round", ct_stats.get('deaths_per_round', 0.0),
                               precision=config.FLOAT_PRECISION_MED)
                self._print_stat("ct_damage_received_per_round", ct_stats.get('damage_received_per_round', 0.0),
                               precision=config.FLOAT_PRECISION_MED)
                self._print_stat("ct_headshot_ratio", ct_stats.get('headshot_ratio', 0.0),
                               precision=config.FLOAT_PRECISION_HIGH)

            if t_stats:
                print("  Combat (T Side):")
                print(f"    t_rounds_played: {combat.t_rounds}")
                self._print_stat("t_kills_per_round", t_stats.get('kills_per_round', 0.0),
                               precision=config.FLOAT_PRECISION_MED)
                self._print_stat("t_damage_per_round", t_stats.get('damage_per_round', 0.0),
                               precision=config.FLOAT_PRECISION_MED)
                self._print_stat("t_deaths_per_round", t_stats.get('deaths_per_round', 0.0),
                               precision=config.FLOAT_PRECISION_MED)
                self._print_stat("t_damage_received_per_round", t_stats.get('damage_received_per_round', 0.0),
                               precision=config.FLOAT_PRECISION_MED)
                self._print_stat("t_headshot_ratio", t_stats.get('headshot_ratio', 0.0),
                               precision=config.FLOAT_PRECISION_HIGH)

    def _display_utility_stats(self, fingerprint: PlayerFingerprint):
        """Display utility usage statistics for a player."""
        utility = fingerprint.utility
        if utility:
            print("  Utility (per round):")
            self._print_stat("flashes_thrown_per_round", utility.flashes_thrown_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("enemies_flashed_per_round", utility.enemies_flashed_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("flash_assists_per_round", utility.flash_assists_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("flash_to_frag_rate", utility.flash_to_frag_rate,
                             precision=config.FLOAT_PRECISION_HIGH)
            self._print_stat("smokes_thrown_per_round", utility.smokes_thrown_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("smoke_coverage_seconds_per_round", utility.smoke_coverage_seconds_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("kills_through_smoke_per_round", utility.kills_through_smoke_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("molotovs_thrown_per_round", utility.molotovs_thrown_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("area_denial_seconds_per_round", utility.area_denial_seconds_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("he_damage_per_round", utility.he_damage_per_round,
                             precision=config.FLOAT_PRECISION_MED)
            self._print_stat("utility_damage_per_grenade", utility.utility_damage_per_grenade,
                             precision=config.FLOAT_PRECISION_HIGH)
    
    def _display_player_similarities(self, all_players: Dict[str, PlayerFingerprint]):
        """Display player similarity analysis."""
        print(f"\n{'='*60}")
        print("PLAYER SIMILARITIES")
        print("="*60)
        
        # Find similar players for some key players
        for player in config.COMPARISON_PLAYERS:
            if player in all_players:
                similar_players = self.player_comparison.find_most_similar_players(
                    player, all_players, top_k=3
                )
                
                print(f"\n{player} - Most similar players:")
                for similar in similar_players:
                    print(f"  {similar['player']}: {similar['similarity']:.3f}")
    
    def _print_stat(self, name: str, value: float, precision: int = 3):
        """Print a formatted statistic."""
        if isinstance(value, float):
            print(f"    {name}: {value:.{precision}f}")
        else:
            print(f"    {name}: {value}")
    
    def export_results_to_dict(self, all_players: Dict[str, PlayerFingerprint]) -> Dict:
        """Export results to a structured dictionary for further processing."""
        results = {}
        
        for player_name, fingerprint in all_players.items():
            results[player_name] = {
                'movement': fingerprint.movement.__dict__ if fingerprint.movement else {},
                'positioning': {
                    'map_coverage_per_round': fingerprint.positioning.map_coverage_per_round,
                    'position_preferences': fingerprint.positioning.position_preferences
                } if fingerprint.positioning else {},
                'combat': fingerprint.combat.__dict__ if fingerprint.combat else {}
            }
        
        return results

    def export_feature_matrix(self, all_players: Dict[str, PlayerFingerprint], map_name: str) -> Optional[str]:
        """Export flattened feature vectors to CSV for downstream analysis."""
        if not config.EXPORT_FEATURE_CSV:
            return None

        rows: List[Dict[str, float]] = []
        for player_name, fingerprint in all_players.items():
            feature_dict = fingerprint.to_feature_vector()
            feature_dict['player'] = player_name
            feature_dict['map'] = map_name
            rows.append(feature_dict)

        if not rows:
            return None

        df = pd.DataFrame(rows)
        # Ensure consistent column order with player/map first
        for column in ['player', 'map']:
            if column in df.columns:
                df.insert(0, column, df.pop(column))

        df = df.fillna(0)

        config.OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.CSV_FILENAME_PREFIX}_{map_name}_{timestamp}.csv"
        filepath = config.OUTPUT_DIR / filename
        df.to_csv(filepath, index=False)
        print(f"    Feature matrix exported to {filepath}")
        return str(filepath)
