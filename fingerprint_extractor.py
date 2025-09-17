# fingerprint_extractor.py
"""Extracts complete player style fingerprints."""

from typing import Dict, Optional, List
from awpy import Demo
from data_structures import PlayerFingerprint, PlayerInfo, DemoData
from analyzers.movement_analyzer import MovementAnalyzer
from analyzers.positioning_analyzer import PositioningAnalyzer
from analyzers.combat_analyzer import CombatAnalyzer
from demo_processor import DemoProcessor
import config

class PlayerStyleFingerprinter:
    """Extracts comprehensive player style fingerprints from demo data."""
    
    def __init__(self):
        self.movement_analyzer = MovementAnalyzer()
        self.positioning_analyzer = None  # Will be set based on map
        self.combat_analyzer = None       # Will be set based on map
        self.demo_processor = DemoProcessor()
        self.current_map = None
        
    def _setup_analyzers_for_map(self, map_name: str):
        """Setup analyzers for a specific map."""
        if self.current_map != map_name:
            self.current_map = map_name
            self.positioning_analyzer = PositioningAnalyzer(map_name)
            self.combat_analyzer = CombatAnalyzer(map_name)
            
            print(f"Initialized analyzers for map: {map_name}")
            print(f"Available positions: {len(config.get_positions_for_map(map_name))}")
    
    def extract_player_fingerprint(self, demos: List[Demo], player_steamid: str, 
                                 map_name: str = "de_mirage") -> Optional[PlayerFingerprint]:
        """Extract a complete style fingerprint for a specific player."""
        # Setup analyzers for the specific map
        self._setup_analyzers_for_map(map_name)
        
        player_data = self.demo_processor.aggregate_player_data(demos, player_steamid, map_name)
        
        if not player_data or player_data.ticks.empty:
            return None
        
        print(f"Extracting fingerprint for player {player_steamid} on {map_name}")
        
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
        
        print(f"\nExtracting fingerprints for {len(unique_players)} players on {map_name}")
        
        # Check if the requested map has position data
        if map_name not in config.AVAILABLE_MAPS:
            print(f"Warning: {map_name} not found in available maps.")
            print("Available maps:")
            for available_map in config.AVAILABLE_MAPS:
                print(f"  - {available_map}")
            
            # Try to find a similar map
            for available_map in config.AVAILABLE_MAPS:
                if map_name.lower().replace("de_", "") in available_map.lower():
                    print(f"Using {available_map} instead of {map_name}")
                    map_name = available_map
                    break
            else:
                print(f"Using fallback map de_mirage")
                map_name = "de_mirage"
        
        # Setup analyzers for the map
        self._setup_analyzers_for_map(map_name)
        
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
        
        print(f"\n✓ Successfully processed {len(all_fingerprints)} players on {map_name}")
        return all_fingerprints
    
    def get_map_info(self, map_name: str) -> str:
        """Get information about available positions for a map."""
        positions = config.get_positions_for_map(map_name)
        
        if not positions:
            return f"No position data available for {map_name}"
        
        info = f"Map: {map_name}\n"
        info += f"Available positions: {len(positions)}\n"
        
        for pos_name, pos_data in positions.items():
            sample_count = pos_data.get('sample_count', 'N/A')
            info += f"  - {pos_name}: {sample_count} samples\n"
        
        return info
    
    def list_available_maps(self) -> List[str]:
        """List all available maps with position data."""
        return config.AVAILABLE_MAPS.copy()