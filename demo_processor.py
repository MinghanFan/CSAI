# demo_processor.py
"""Demo file loading and processing with proper freeze time filtering."""

import pandas as pd
from awpy import Demo
from typing import List, Dict, Tuple
from data_structures import DemoData, PlayerInfo
import config

class DemoProcessor:
    """Handles loading and basic processing of Couter-Strike demo files."""
    
    def __init__(self):
        self.demos = []
        self.detected_map = None
    
    def load_demos(self, demo_files: List[str]) -> List[Demo]:
        """Load demo files and detect the map being used."""
        print(f"Loading {len(demo_files)} demo files...")
        
        demos = []
        map_names = []
        
        for demo_file in demo_files:
            try:
                demo = Demo(demo_file)
                demo.parse(
                    player_props=[
                        "team_name", "X", "Y", "Z", "health", "steamid", "name",
                        "velocity_X", "velocity_Y", "velocity_Z",
                        "last_place_name", "pitch", "yaw", "armor_value"
                    ]
                )
                
                # Get map name from demo header
                map_name = demo.header["map_name"] if "map_name" in demo.header else None
                
                # Backup for map name
                if not map_name or map_name == "None":
                    # Try to extract from filename
                    filename = demo_file.split('/')[-1].lower()
                    for known_map in config.MAP_POSITIONS.keys():
                        if known_map.replace('de_', '') in filename:
                            map_name = known_map
                            break
                    
                    # If still no, ask user or use default
                    if not map_name:
                        print(f"    Could not detect map from demo header or filename")
                        print(f"     Available maps: {list(config.MAP_POSITIONS.keys())}")
                        map_name = input(f"     Please enter map name for {demo_file.split('/')[-1]}: ").strip()
                        if not map_name:
                            map_name = "de_mirage"  # Default fallback
                
                map_names.append(map_name)
                
                rounds_df = demo.rounds.to_pandas()
                kills_df = demo.kills.to_pandas()
                ticks_df = demo.ticks.to_pandas()
                damages_df = demo.damages.to_pandas()
                
                print(f"✓ Loaded: {demo_file.split('/')[-1]}")
                print(f"  Map: {map_name}")
                print(f"  Rounds: {len(rounds_df)}, Kills: {len(kills_df)}, "
                      f"Damages: {len(damages_df)}, Ticks: {len(ticks_df)}")
                
                # DEBUG: Check rounds structure
                if not rounds_df.empty:
                    print(f"  Rounds columns: {list(rounds_df.columns)}")
                    sample_round = rounds_df.iloc[0]
                    if 'freeze_end' in rounds_df.columns:
                        print(f"  Sample freeze_end: {sample_round['freeze_end']}")
                    if 'end_tick' in rounds_df.columns:
                        print(f"  Sample end_tick: {sample_round['end_tick']}")
                
                demos.append(demo)
                
            except Exception as e:
                print(f"✗ Failed to load {demo_file}: {e}")
        
        if not demos:
            raise RuntimeError("No demos loaded successfully")
        
        # Detect the primary map
        unique_maps = list(set(map_names))
        
        if len(unique_maps) == 1:
            self.detected_map = unique_maps[0]
            print(f"\n  Detected map: {self.detected_map}")
        else:
            from collections import Counter
            map_counts = Counter(map_names)
            self.detected_map = map_counts.most_common(1)[0][0]
            print(f"\n  Multiple maps detected, using most common: {self.detected_map}")
            print(f"   Map distribution: {dict(map_counts)}")
        
        # Set the map in config
        config.set_current_map(self.detected_map)
        
        if self.detected_map not in config.MAP_POSITIONS:
            print(f"  Warning: {self.detected_map} is not in supported maps!")
            print(f"   Analysis will use basic positioning without map-specific areas.")
        
        return demos
    
    def extract_unique_players(self, demos: List[Demo]) -> Dict[str, PlayerInfo]:
        """Extract unique players from demos."""
        steamid_to_names = {}
        
        for demo in demos:
            try:
                ticks_df = demo.ticks.to_pandas()
                
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
    
    # TODO: unitility data aggregation
    def aggregate_player_data(self, demos: List[Demo], player_steamid: str) -> DemoData:
        """Aggregate player data with proper freeze time filtering and side separation."""
        all_ticks_ct = []
        all_ticks_t = []
        all_kills_ct = []
        all_kills_t = []
        all_damages_ct = []
        all_damages_t = []
        all_rounds = []
        
        total_ct_rounds = 0
        total_t_rounds = 0
        
        for demo in demos:
            try:
                print(f"    Processing {self.detected_map} demo")
                
                # Get all demo data
                ticks_df = demo.ticks.to_pandas()
                kills_df = demo.kills.to_pandas()
                damages_df = demo.damages.to_pandas()
                rounds_df = demo.rounds.to_pandas()
                
                print(f"    Demo has {len(rounds_df)} rounds, {len(ticks_df)} total ticks")
                
                # Process each round with proper freeze time filtering
                ct_data, t_data, round_counts = self._process_rounds_with_freeze_filter(
                    ticks_df, kills_df, damages_df, rounds_df, int(player_steamid)
                )
                
                # Accumulate data by side
                if len(ct_data['ticks']) > 0:
                    all_ticks_ct.append(ct_data['ticks'])
                    print(f"    Found {len(ct_data['ticks'])} CT gameplay ticks for player")
                
                if len(t_data['ticks']) > 0:
                    all_ticks_t.append(t_data['ticks'])
                    print(f"    Found {len(t_data['ticks'])} T gameplay ticks for player")
                
                if len(ct_data['kills']) > 0:
                    all_kills_ct.append(ct_data['kills'])
                    print(f"    Found {len(ct_data['kills'])} CT kills for player")
                
                if len(t_data['kills']) > 0:
                    all_kills_t.append(t_data['kills'])
                    print(f"    Found {len(t_data['kills'])} T kills for player")
                
                if len(ct_data['damages']) > 0:
                    all_damages_ct.append(ct_data['damages'])
                    print(f"    Found {len(ct_data['damages'])} CT damage events for player")
                
                if len(t_data['damages']) > 0:
                    all_damages_t.append(t_data['damages'])
                    print(f"    Found {len(t_data['damages'])} T damage events for player")
                
                total_ct_rounds += round_counts['ct']
                total_t_rounds += round_counts['t']
                all_rounds.append(rounds_df)
                        
            except Exception as e:
                print(f"    Error processing demo: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Combine data by side
        combined_ticks_ct = pd.concat(all_ticks_ct, ignore_index=True) if all_ticks_ct else pd.DataFrame()
        combined_ticks_t = pd.concat(all_ticks_t, ignore_index=True) if all_ticks_t else pd.DataFrame()
        combined_kills_ct = pd.concat(all_kills_ct, ignore_index=True) if all_kills_ct else pd.DataFrame()
        combined_kills_t = pd.concat(all_kills_t, ignore_index=True) if all_kills_t else pd.DataFrame()
        combined_damages_ct = pd.concat(all_damages_ct, ignore_index=True) if all_damages_ct else pd.DataFrame()
        combined_damages_t = pd.concat(all_damages_t, ignore_index=True) if all_damages_t else pd.DataFrame()
        combined_rounds = pd.concat(all_rounds, ignore_index=True) if all_rounds else pd.DataFrame()
        
        # Add side indicators to the data
        if not combined_ticks_ct.empty:
            combined_ticks_ct['player_side'] = 'CT'
        if not combined_ticks_t.empty:
            combined_ticks_t['player_side'] = 'T'
        if not combined_kills_ct.empty:
            combined_kills_ct['player_side'] = 'CT'
        if not combined_kills_t.empty:
            combined_kills_t['player_side'] = 'T'
        if not combined_damages_ct.empty:
            combined_damages_ct['player_side'] = 'CT'
        if not combined_damages_t.empty:
            combined_damages_t['player_side'] = 'T'
        
        # Combine both sides
        combined_ticks = pd.concat([combined_ticks_ct, combined_ticks_t], ignore_index=True)
        combined_kills = pd.concat([combined_kills_ct, combined_kills_t], ignore_index=True)
        combined_damages = pd.concat([combined_damages_ct, combined_damages_t], ignore_index=True)
        
        total_rounds = total_ct_rounds + total_t_rounds
        
        print(f"    Combined: {len(combined_ticks)} gameplay ticks "
              f"({len(combined_ticks_ct)} CT, {len(combined_ticks_t)} T)")
        print(f"    {len(combined_kills)} kills, {len(combined_damages)} damages "
              f"across {total_rounds} rounds ({total_ct_rounds} CT, {total_t_rounds} T)")
        
        return DemoData(
            ticks=combined_ticks,
            kills=combined_kills,
            damages=combined_damages,
            rounds=combined_rounds,
            total_rounds=total_rounds,
            ct_rounds=total_ct_rounds,
            t_rounds=total_t_rounds
        )
    
    def _process_rounds_with_freeze_filter(self, ticks_df: pd.DataFrame, kills_df: pd.DataFrame, 
                                         damages_df: pd.DataFrame, rounds_df: pd.DataFrame, 
                                         player_steamid: int) -> Tuple[Dict, Dict, Dict]:
        """Process rounds with proper freeze time filtering, separated by side."""
        
        ct_data = {'ticks': [], 'kills': [], 'damages': []}
        t_data = {'ticks': [], 'kills': [], 'damages': []}
        round_counts = {'ct': 0, 't': 0}
        
        for _, round_row in rounds_df.iterrows():
            try:
                rnum = round_row["round_num"]
                
                # Get freeze time end - this is when actual gameplay starts
                freeze_end = round_row["freeze_end"]
                
                # Get round end - this is when the round actually ends
                round_end = round_row["end"]
                
                if pd.isna(freeze_end) or pd.isna(round_end):
                    print(f"      Skipping round {rnum} - missing timing data")
                    continue
                
                # Filter ticks for this round (gameplay only, no freeze time)
                round_ticks = ticks_df[
                    (ticks_df['round_num'] == rnum) & 
                    (ticks_df['tick'] >= freeze_end) & 
                    (ticks_df['tick'] <= round_end) &
                    (ticks_df['steamid'] == player_steamid)
                ]
                
                if round_ticks.empty:
                    continue
                
                # Determine player's side for this round
                player_side = round_ticks['side'].iloc[0] if 'side' in round_ticks.columns else None
                
                if player_side is None:
                    print(f"      Skipping round {rnum} - no side information")
                    continue
                
                # Filter kills and damages for this round (gameplay only)
                round_kills = kills_df[
                    (kills_df['round_num'] == rnum) & 
                    (kills_df['tick'] >= freeze_end) & 
                    (kills_df['tick'] <= round_end) &
                    (kills_df['attacker_steamid'] == player_steamid)
                ]
                
                round_damages = damages_df[
                    (damages_df['round_num'] == rnum) & 
                    (damages_df['tick'] >= freeze_end) & 
                    (damages_df['tick'] <= round_end) &
                    (damages_df['attacker_steamid'] == player_steamid)
                ]
                
                # Separate by side
                if player_side.lower() == 'ct':
                    ct_data['ticks'].append(round_ticks)
                    if not round_kills.empty:
                        ct_data['kills'].append(round_kills)
                    if not round_damages.empty:
                        ct_data['damages'].append(round_damages)
                    round_counts['ct'] += 1
                    
                elif player_side.lower() == 't':
                    t_data['ticks'].append(round_ticks)
                    if not round_kills.empty:
                        t_data['kills'].append(round_kills)
                    if not round_damages.empty:
                        t_data['damages'].append(round_damages)
                    round_counts['t'] += 1
                
                # Debug info for first few rounds
                if rnum <= 3:
                    print(f"      Round {rnum}: {player_side} side, "
                          f"ticks {freeze_end}-{round_end} ({len(round_ticks)} gameplay ticks)")
                    
            except Exception as e:
                print(f"      Error processing round {rnum}: {e}")
                continue
        
        # Combine data within each side
        for side_data in [ct_data, t_data]:
            side_data['ticks'] = pd.concat(side_data['ticks'], ignore_index=True) if side_data['ticks'] else pd.DataFrame()
            side_data['kills'] = pd.concat(side_data['kills'], ignore_index=True) if side_data['kills'] else pd.DataFrame()
            side_data['damages'] = pd.concat(side_data['damages'], ignore_index=True) if side_data['damages'] else pd.DataFrame()
        
        print(f"    Processed {round_counts['ct']} CT rounds, {round_counts['t']} T rounds")
        
        return ct_data, t_data, round_counts
