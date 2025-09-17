# fingerprint_extractor.py
"""Extracts complete player style fingerprints."""

from typing import Dict, Optional, List
from awpy import Demo
from data_structures import PlayerFingerprint, PlayerInfo, DemoData
from analyzers.movement_analyzer import MovementAnalyzer
from analyzers.positioning_analyzer import PositioningAnalyzer
from analyzers.combat_analyzer import CombatAnalyzer
from demo_processor import DemoProcessor

class PlayerStyleFingerprinter:
    """Extracts comprehensive player style fingerprints from demo data."""
    
    def __init__(self):
        self.movement_analyzer = MovementAnalyzer()
        self.positioning_analyzer = PositioningAnalyzer()
        self.combat_analyzer = CombatAnalyzer()
        self.demo_processor = DemoProcessor()
        
    def extract_player_fingerprint(self, demos: List[Demo], player_steamid: str, 
                                 map_name: str = "de_mirage") -> Optional[PlayerFingerprint]:
        """Extract a complete style fingerprint for a specific player."""
        player_data = self.demo_processor.aggregate_player_data(demos, player_steamid, map_name)
        
        if not player_data or player_data.ticks.empty:
            return None
        
        print(f"Extracting fingerprint for player {player_steamid}")
        
        # Extract signatures from each analyzer
        movement_signature = self.movement_analyzer.analyze(
            player_data.ticks, player_data.total_rounds
        )
        
        positioning_signature = self.positioning_analyzer.analyze(
            player_data.ticks, player_data.total_rounds
        )
        
        combat_signature = self.combat_analyzer.analyze(
            player_data.kills, player_data.damages, player_data.total_rounds
        )
        
        return PlayerFingerprint(
            movement=movement_signature,
            positioning=positioning_signature,
            combat=combat_signature
        )
    
    def extract_all_player_fingerprints(self, demos: List[Demo], 
                                      unique_players: Dict[str, PlayerInfo],
                                      map_name: str = "de_mirage") -> Dict[str, PlayerFingerprint]:
        """Extract fingerprints for all players in the demos."""
        all_fingerprints = {}
        processed_count = 0
        
        print(f"\nExtracting fingerprints for {len(unique_players)} players")
        
        for steamid, player_info in unique_players.items():
            try:
                print(f"\nProcessing: {player_info.main_name}")
                fingerprint = self.extract_player_fingerprint(demos, steamid, map_name)
                
                if fingerprint:
                    all_fingerprints[player_info.main_name] = fingerprint
                    processed_count += 1
                    
            except Exception as e:
                print(f"✗ Error processing {player_info.main_name}: {e}")
                continue
        
        print(f"\n✓ Successfully processed {len(all_fingerprints)} players")
        return all_fingerprints