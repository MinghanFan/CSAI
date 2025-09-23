# results_formatter.py
"""Formats and displays analysis results."""

from typing import Dict, List, Optional
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
    
    def _display_movement_stats(self, fingerprint: PlayerFingerprint):
        """Display movement statistics for a player."""
        movement = fingerprint.movement
        if movement:
            print("  Movement (per round):")
            self._print_stat("counter_strafe_frequency", movement.counter_strafe_frequency, 
                           precision=config.FLOAT_PRECISION_HIGH)
            self._print_stat("avg_velocity", movement.avg_velocity, 
                           precision=config.FLOAT_PRECISION_MED)
            self._print_stat("movement_smoothness", movement.movement_smoothness,
                           precision=config.FLOAT_PRECISION_HIGH)
            self._print_stat("movement_distance_per_round", movement.movement_distance_per_round,
                           precision=config.FLOAT_PRECISION_LOW)
            self._print_stat("position_variance_per_round", movement.position_variance_per_round,
                           precision=config.FLOAT_PRECISION_LOW)
    
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
            
            # Show side-specific stats
            ct_stats = combat.get_ct_stats()
            t_stats = combat.get_t_stats()
            
            if ct_stats:
                print("  Combat (CT Side):")
                for key, value in ct_stats.items():
                    if isinstance(value, (int, float)) and key in ['kills_per_round', 'damage_per_round', 'headshot_ratio']:
                        self._print_stat(f"ct_{key}", value, precision=config.FLOAT_PRECISION_MED)
            
            if t_stats:
                print("  Combat (T Side):")
                for key, value in t_stats.items():
                    if isinstance(value, (int, float)) and key in ['kills_per_round', 'damage_per_round', 'headshot_ratio']:
                        self._print_stat(f"t_{key}", value, precision=config.FLOAT_PRECISION_MED)
    
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