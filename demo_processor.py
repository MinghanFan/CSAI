# demo_processor.py
"""Demo file loading and basic processing."""

import pandas as pd
from awpy import Demo
from typing import List, Dict
from data_structures import DemoData, PlayerInfo

class DemoProcessor:
    """Handles loading and basic processing of CS:GO demo files."""
    
    def __init__(self):
        self.demos = []
    
    def load_demos(self, demo_files: List[str]) -> List[Demo]:
        """Load demo files and return parsed Demo objects."""
        print(f"Loading {len(demo_files)} demo files...")
        
        demos = []
        for demo_file in demo_files:
            try:
                demo = Demo(demo_file)
                demo.parse()
                
                # Display demo information
                map_name = demo.header["map_name"]
                rounds_df = demo.rounds.to_pandas()
                kills_df = demo.kills.to_pandas()
                ticks_df = demo.ticks.to_pandas()
                damages_df = demo.damages.to_pandas()
                
                print(f"✓ Loaded: {demo_file.split('/')[-1]}")
                print(f"  Map: {map_name}")
                print(f"  Rounds: {len(rounds_df)}, Kills: {len(kills_df)}, "
                      f"Damages: {len(damages_df)}, Ticks: {len(ticks_df)}")
                
                demos.append(demo)
                
            except Exception as e:
                print(f"✗ Failed to load {demo_file}: {e}")
        
        if not demos:
            raise RuntimeError("No demos loaded successfully!")
            
        return demos
    
    def extract_unique_players(self, demos: List[Demo]) -> Dict[str, PlayerInfo]:
        """Extract unique players from demos."""
        steamid_to_names = {}
        
        for demo in demos:
            try:
                if hasattr(demo.ticks, 'to_pandas'):
                    ticks_df = demo.ticks.to_pandas()
                else:
                    ticks_df = demo.ticks
                
                if 'steamid' in ticks_df.columns and 'name' in ticks_df.columns:
                    unique_players_df = ticks_df[['steamid', 'name']].drop_duplicates()
                    
                    for _, row in unique_players_df.iterrows():
                        steamid = str(row['steamid'])
                        name = str(row['name'])
                        
                        if steamid not in steamid_to_names:
                            steamid_to_names[steamid] = []
                        if name not in steamid_to_names[steamid]:
                            steamid_to_names[steamid].append(name)
                            
            except Exception:
                continue
        
        unique_players = {}
        for steamid, names in steamid_to_names.items():
            if names and steamid != 'nan':
                main_name = max(names, key=len)
                unique_players[steamid] = PlayerInfo(
                    steamid=steamid,
                    main_name=main_name,
                    all_names=names
                )
        
        return unique_players
    
    def aggregate_player_data(self, demos: List[Demo], player_steamid: str, 
                            map_name: str = "de_mirage") -> DemoData:
        """Aggregate all data for a specific player across demos."""
        all_ticks = []
        all_kills = []
        all_damages = []
        all_rounds = []
        
        for demo in demos:
            try:
                # Get map name for verification
                map_name_demo = demo.header["map_name"]
                print(f"    Processing {map_name_demo} demo")
                
                # Get all demo data
                ticks_df = demo.ticks.to_pandas()
                kills_df = demo.kills.to_pandas()
                damages_df = demo.damages.to_pandas()
                rounds_df = demo.rounds.to_pandas()
                
                print(f"    Demo has {len(ticks_df)} ticks, {len(kills_df)} kills, "
                      f"{len(damages_df)} damages, {len(rounds_df)} rounds")
                
                # Filter for specific player
                player_ticks = ticks_df[ticks_df['steamid'] == int(player_steamid)]
                if len(player_ticks) > 0:
                    all_ticks.append(player_ticks)
                    print(f"    Found {len(player_ticks)} ticks for player")
                
                # Get player kills (attacker)
                player_kills = kills_df[kills_df['attacker_steamid'] == int(player_steamid)]
                if len(player_kills) > 0:
                    all_kills.append(player_kills)
                    print(f"    Found {len(player_kills)} kills for player")
                
                # Get player damages (attacker)
                player_damages = damages_df[damages_df['attacker_steamid'] == int(player_steamid)]
                if len(player_damages) > 0:
                    all_damages.append(player_damages)
                    print(f"    Found {len(player_damages)} damage events for player")
                
                # Store rounds info for this demo
                all_rounds.append(rounds_df)
                        
            except Exception as e:
                print(f"    Error processing demo: {e}")
                continue
        
        # Combine data
        combined_ticks = pd.concat(all_ticks, ignore_index=True) if all_ticks else pd.DataFrame()
        combined_kills = pd.concat(all_kills, ignore_index=True) if all_kills else pd.DataFrame()
        combined_damages = pd.concat(all_damages, ignore_index=True) if all_damages else pd.DataFrame()
        combined_rounds = pd.concat(all_rounds, ignore_index=True) if all_rounds else pd.DataFrame()
        
        # Calculate total rounds this player participated in
        total_rounds = 0
        if not combined_rounds.empty:
            total_rounds = len(combined_rounds)
        elif not combined_ticks.empty and 'round_num' in combined_ticks.columns:
            total_rounds = combined_ticks['round_num'].nunique()
        else:
            total_rounds = 20  # Fallback estimate
        
        print(f"    Combined: {len(combined_ticks)} ticks, {len(combined_kills)} kills, "
              f"{len(combined_damages)} damages across {total_rounds} rounds")
        
        return DemoData(
            ticks=combined_ticks,
            kills=combined_kills,
            damages=combined_damages,
            rounds=combined_rounds,
            total_rounds=total_rounds
        )