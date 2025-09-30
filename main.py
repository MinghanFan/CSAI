# main.py
"""Main application for CS:GO Player Style Analysis with automatic single-map detection."""

from demo_processor import DemoProcessor
from fingerprint_extractor import PlayerStyleFingerprinter
from results_formatter import ResultsFormatter
from visualization import PlayerVisualization
from output_handler import OutputHandler
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
        # Load and process demos (automatically detects map)
        demos = demo_processor.load_demos(config.DEMO_FILES)
        
        # Extract unique players
        unique_players = demo_processor.extract_unique_players(demos)
        print(f"\nFound {len(unique_players)} unique players")
        
        # Get detected map name for output handler
        map_name = config.get_current_map_name() or "unknown_map"
        
        # Use output handler to manage console and file output
        with OutputHandler(map_name) as output:
            # Extract fingerprints for all players (uses detected map automatically)
            all_players = fingerprinter.extract_all_player_fingerprints(
                demos, unique_players
            )
            
            if len(all_players) == 0:
                print("No player fingerprints extracted!")
                return
            
            # Display results (this will go to both console and file)
            formatter.display_analysis_results(all_players, len(demos), map_name)
        
        # Create visualizations (controlled by config settings)
        if config.CREATE_VISUALIZATIONS:
            print(f"\nCreating player style visualization for {map_name}...")
            visualizer.visualize_player_clusters(all_players, map_name)
            
            # Optional: Create additional visualizations
            if len(all_players) >= 4:
                print(f"Creating similarity heatmap...")
                visualizer.create_similarity_heatmap(all_players, map_name)
            
            if len(all_players) >= 3:
                print(f"Creating statistics comparison...")
                visualizer.create_stat_comparison_plot(all_players, map_name)
            
            if config.SAVE_PLOTS:
                print(f"\nAll visualizations saved to: {config.OUTPUT_DIR}")
        else:
            print("\nVisualization disabled in config.")
        
    except Exception as e:
        print(f"Error in main application: {e}")
        raise

if __name__ == "__main__":
    main()