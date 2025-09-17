# main.py
"""Main application for CS:GO Player Style Analysis."""

from demo_processor import DemoProcessor
from fingerprint_extractor import PlayerStyleFingerprinter
from results_formatter import ResultsFormatter
from visualization import PlayerVisualization
import config

def detect_map_from_demos(demos) -> str:
    """Detect the most common map from the loaded demos."""
    map_counts = {}
    
    for demo in demos:
        try:
            map_name = demo.header.get("map_name", "unknown")
            map_counts[map_name] = map_counts.get(map_name, 0) + 1
        except Exception:
            continue
    
    if map_counts:
        most_common_map = max(map_counts, key=map_counts.get)
        print(f"Detected maps in demos: {dict(map_counts)}")
        print(f"Most common map: {most_common_map}")
        return most_common_map
    
    return "de_mirage"  # Default fallback

def main():
    """Main application entry point."""
    print("Starting CS:GO Player Style Analysis...")
    
    # Print available maps
    print(f"\nAvailable maps with position data:")
    config.print_available_maps()
    
    # Initialize components
    demo_processor = DemoProcessor()
    fingerprinter = PlayerStyleFingerprinter()
    formatter = ResultsFormatter()
    visualizer = PlayerVisualization()
    
    try:
        # Load and process demos
        demos = demo_processor.load_demos(config.DEMO_FILES)
        
        # Detect the map from demos
        detected_map = detect_map_from_demos(demos)
        
        # Check if detected map has position data
        if detected_map in config.AVAILABLE_MAPS:
            target_map = detected_map
        else:
            print(f"Warning: Detected map '{detected_map}' not in available position data.")
            
            # Try to find a matching map
            target_map = None
            for available_map in config.AVAILABLE_MAPS:
                if detected_map.lower().replace("de_", "") in available_map.lower():
                    target_map = available_map
                    print(f"Using similar map: {target_map}")
                    break
            
            if not target_map:
                target_map = "de_mirage"
                print(f"Using default map: {target_map}")
        
        print(f"\nAnalyzing demos for map: {target_map}")
        
        # Show map information
        print(fingerprinter.get_map_info(target_map))
        
        # Extract unique players
        unique_players = demo_processor.extract_unique_players(demos)
        print(f"\nFound {len(unique_players)} unique players")
        
        # Extract fingerprints for all players
        all_players = fingerprinter.extract_all_player_fingerprints(
            demos, unique_players, target_map
        )
        
        if len(all_players) == 0:
            print("No player fingerprints extracted!")
            return
        
        # Display results
        formatter.display_analysis_results(all_players, len(demos), target_map)
        
        # Create visualizations
        print(f"\nCreating player style visualization for {target_map}...")
        visualizer.visualize_player_clusters(all_players, target_map)
        
        # Optional: Create additional visualizations
        # visualizer.create_similarity_heatmap(all_players)
        # visualizer.create_stat_comparison_plot(all_players)
        
    except Exception as e:
        print(f"Error in main application: {e}")
        raise

if __name__ == "__main__":
    main()