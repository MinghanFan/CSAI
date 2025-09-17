# visualization.py
"""Data visualization for player analysis results."""

import matplotlib.pyplot as plt
from typing import Dict
from data_structures import PlayerFingerprint
from player_comparison import PlayerComparison

class PlayerVisualization:
    """Handles visualization of player analysis results."""
    
    def __init__(self):
        self.player_comparison = PlayerComparison()
    
    def visualize_player_clusters(self, all_players: Dict[str, PlayerFingerprint], 
                                map_name: str = "de_mirage"):
        """Create and display a 2D visualization of player style clusters."""
        comparison = self.player_comparison.compare_players(all_players)
        if not comparison:
            print("Not enough players for visualization")
            return
        
        plt.figure(figsize=(12, 8))
        plt.scatter(
            comparison['visualization_coords'][:, 0],
            comparison['visualization_coords'][:, 1],
            s=100,
            alpha=0.7
        )
        
        # Annotate each point with player name
        for i, player in enumerate(comparison['player_names']):
            plt.annotate(player, 
                        (comparison['visualization_coords'][i, 0], 
                         comparison['visualization_coords'][i, 1]),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8)
        
        plt.title(f"Player Style Clusters ({map_name})")
        plt.xlabel("Style Component 1")
        plt.ylabel("Style Component 2")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    def create_similarity_heatmap(self, all_players: Dict[str, PlayerFingerprint], 
                                map_name: str = "de_mirage"):
        """Create a heatmap showing player similarities."""
        comparison = self.player_comparison.compare_players(all_players)
        if not comparison:
            print("Not enough players for similarity heatmap")
            return
        
        plt.figure(figsize=(10, 8))
        plt.imshow(comparison['similarity_matrix'], cmap='RdYlBu', aspect='auto')
        plt.colorbar(label='Similarity Score')
        
        # Set tick labels to player names
        player_names = comparison['player_names']
        plt.xticks(range(len(player_names)), player_names, rotation=45)
        plt.yticks(range(len(player_names)), player_names)
        
        plt.title(f"Player Style Similarity Matrix ({map_name})")
        plt.tight_layout()
        plt.show()
    
    def create_stat_comparison_plot(self, all_players: Dict[str, PlayerFingerprint], 
                                  stats_to_compare: list = None, map_name: str = "de_mirage"):
        """Create a comparison plot for specific statistics across players."""
        if stats_to_compare is None:
            stats_to_compare = [
                'kills_per_round', 'damage_per_round', 'headshot_ratio', 
                'movement_distance_per_round', 'clutch_potential'
            ]
        
        # Extract stats for each player
        player_names = []
        stat_values = {stat: [] for stat in stats_to_compare}
        
        for player_name, fingerprint in all_players.items():
            player_names.append(player_name)
            feature_dict = fingerprint.to_feature_vector()
            
            for stat in stats_to_compare:
                # Look for the stat in the feature dictionary
                found_value = None
                for key, value in feature_dict.items():
                    if stat in key.lower():
                        found_value = value
                        break
                stat_values[stat].append(found_value or 0)
        
        # Create subplots
        fig, axes = plt.subplots(len(stats_to_compare), 1, figsize=(12, 3 * len(stats_to_compare)))
        if len(stats_to_compare) == 1:
            axes = [axes]
        
        for i, stat in enumerate(stats_to_compare):
            axes[i].bar(player_names, stat_values[stat])
            axes[i].set_title(f'{stat.replace("_", " ").title()} ({map_name})')
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def create_position_preference_plot(self, all_players: Dict[str, PlayerFingerprint], 
                                      map_name: str = "de_mirage", top_positions: int = 5):
        """Create a plot showing position preferences for top players."""
        if not all_players:
            print("No players to visualize")
            return
        
        # Get all position names
        all_positions = set()
        for fingerprint in all_players.values():
            if fingerprint.positioning and fingerprint.positioning.position_preferences:
                all_positions.update(fingerprint.positioning.position_preferences.keys())
        
        if not all_positions:
            print("No position data available for visualization")
            return
        
        # Select top players (by total positioning data)
        player_scores = {}
        for player_name, fingerprint in all_players.items():
            if fingerprint.positioning and fingerprint.positioning.position_preferences:
                total_time = sum(fingerprint.positioning.position_preferences.values())
                player_scores[player_name] = total_time
        
        top_players = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not top_players:
            print("No position preference data to visualize")
            return
        
        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=(14, 8))
        
        positions_list = sorted(list(all_positions))[:top_positions]  # Limit to top N positions
        player_names = [p[0] for p in top_players]
        
        # Prepare data for stacked bar chart
        position_data = {}
        for pos in positions_list:
            position_data[pos] = []
            for player_name in player_names:
                fingerprint = all_players[player_name]
                if (fingerprint.positioning and 
                    fingerprint.positioning.position_preferences and 
                    pos in fingerprint.positioning.position_preferences):
                    position_data[pos].append(fingerprint.positioning.position_preferences[pos])
                else:
                    position_data[pos].append(0)
        
        # Create stacked bar chart
        bottom = [0] * len(player_names)
        colors = plt.cm.Set3(range(len(positions_list)))
        
        for i, pos in enumerate(positions_list):
            ax.bar(player_names, position_data[pos], bottom=bottom, 
                  label=pos, color=colors[i], alpha=0.8)
            bottom = [b + v for b, v in zip(bottom, position_data[pos])]
        
        ax.set_title(f'Position Preferences by Player ({map_name})')
        ax.set_ylabel('Fraction of Time')
        ax.set_xlabel('Players')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()