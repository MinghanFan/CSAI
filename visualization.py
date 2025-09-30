# visualization.py
"""Data visualization for player analysis results."""

import matplotlib.pyplot as plt
from typing import Dict
from pathlib import Path
from data_structures import PlayerFingerprint
from player_comparison import PlayerComparison
import config

class PlayerVisualization:
    """Handles visualization of player analysis results."""
    
    def __init__(self):
        self.player_comparison = PlayerComparison()
        
        # Create output directory for plots if needed
        if config.SAVE_PLOTS:
            config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    def visualize_player_clusters(self, all_players: Dict[str, PlayerFingerprint], 
                                map_name: str = "Analysis"):
        """Create and display a 2D visualization of player style clusters."""
        if not config.CREATE_VISUALIZATIONS:
            return
        
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
        
        # Save and/or show plot
        self._handle_plot_output(f"player_clusters_{map_name}")
    
    def create_similarity_heatmap(self, all_players: Dict[str, PlayerFingerprint], 
                                map_name: str = "Analysis"):
        """Create a heatmap showing player similarities."""
        if not config.CREATE_VISUALIZATIONS:
            return
        
        comparison = self.player_comparison.compare_players(all_players)
        if not comparison:
            print("Not enough players for similarity heatmap")
            return
        
        plt.figure(figsize=(10, 8))
        plt.imshow(comparison['similarity_matrix'], cmap='RdYlBu', aspect='auto')
        plt.colorbar(label='Similarity Score')
        
        # Set tick labels to player names
        player_names = comparison['player_names']
        plt.xticks(range(len(player_names)), player_names, rotation=45, ha='right')
        plt.yticks(range(len(player_names)), player_names)
        
        plt.title(f"Player Style Similarity Matrix ({map_name})")
        plt.tight_layout()
        
        # Save and/or show plot
        self._handle_plot_output(f"similarity_heatmap_{map_name}")
    
    def create_stat_comparison_plot(self, all_players: Dict[str, PlayerFingerprint], 
                                  map_name: str = "Analysis",
                                  stats_to_compare: list = None):
        """Create a comparison plot for specific statistics across players."""
        if not config.CREATE_VISUALIZATIONS:
            return
        
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
        fig, axes = plt.subplots(len(stats_to_compare), 1, 
                                figsize=(12, 3 * len(stats_to_compare)))
        if len(stats_to_compare) == 1:
            axes = [axes]
        
        for i, stat in enumerate(stats_to_compare):
            axes[i].bar(player_names, stat_values[stat])
            axes[i].set_title(f'{stat.replace("_", " ").title()} ({map_name})')
            axes[i].tick_params(axis='x', rotation=45)
            axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save and/or show plot
        self._handle_plot_output(f"stat_comparison_{map_name}")
    
    def _handle_plot_output(self, filename: str):
        """Handle saving and/or showing a plot based on config."""
        if config.SAVE_PLOTS:
            # Add timestamp to filename to avoid overwriting
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = config.OUTPUT_DIR / f"{filename}_{timestamp}.png"
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {filepath}")
        
        if config.SHOW_PLOTS:
            plt.show()
        else:
            plt.close()  # Close figure to free memory