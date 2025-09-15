# main.py
"""Main application for CS:GO Player Style Analysis."""

from demo_processor import DemoProcessor
from fingerprint_extractor import PlayerStyleFingerprinter
from results_formatter import ResultsFormatter
from visualization import PlayerVisualization
import config

def main():
    """Main application entry point."""
    print("Starting CS:GO Player Style Analysis...")
    
    # Initialize components
    demo_processor = DemoProcessor()
    fingerprinter = PlayerStyleFingerprinter()
    formatter = ResultsFormatter()
    visualizer = PlayerVisualization()
    
    try:
        # Load and process demos
        demos = demo_processor.load_demos(config.DEMO_FILES)
        
        # Extract unique players
        unique_players = demo_processor.extract_unique_players(demos)
        print(f"\nFound {len(unique_players)} unique players")
        
        # Extract fingerprints for all players
        all_players = fingerprinter.extract_all_player_fingerprints(
            demos, unique_players, "de_mirage"
        )
        
        if len(all_players) == 0:
            print("No player fingerprints extracted!")
            return
        
        # Display results
        formatter.display_analysis_results(all_players, len(demos))
        
        # Create visualizations
        print(f"\nCreating player style visualization...")
        visualizer.visualize_player_clusters(all_players)
        
        # Optional: Create additional visualizations
        # visualizer.create_similarity_heatmap(all_players)
        # visualizer.create_stat_comparison_plot(all_players)
        
    except Exception as e:
        print(f"Error in main application: {e}")
        raise

if __name__ == "__main__":
    main()