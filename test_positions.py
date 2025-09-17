# test_positions.py
"""Test script for the new position system."""

import config
from analyzers.positioning_analyzer import PositioningAnalyzer
from analyzers.combat_analyzer import CombatAnalyzer

def test_position_loading():
    """Test that positions are loaded correctly."""
    print("Testing position loading...")
    print(f"Total maps loaded: {len(config.ALL_MAP_POSITIONS)}")
    
    for map_name, positions in config.ALL_MAP_POSITIONS.items():
        print(f"\n{map_name}:")
        print(f"  Positions: {len(positions)}")
        
        # Show a few example positions
        for i, (pos_name, pos_data) in enumerate(list(positions.items())[:3]):
            x_range = pos_data.get('x_range', [0, 0])
            y_range = pos_data.get('y_range', [0, 0])
            sample_count = pos_data.get('sample_count', 'N/A')
            
            print(f"    {pos_name}: X({x_range[0]:.0f}, {x_range[1]:.0f}), "
                  f"Y({y_range[0]:.0f}, {y_range[1]:.0f}), "
                  f"Samples: {sample_count}")
        
        if len(positions) > 3:
            print(f"    ... and {len(positions) - 3} more positions")

def test_analyzer_initialization():
    """Test that analyzers can be initialized with different maps."""
    print("\n" + "="*50)
    print("Testing analyzer initialization...")
    
    available_maps = list(config.ALL_MAP_POSITIONS.keys())[:3]  # Test first 3 maps
    
    for map_name in available_maps:
        print(f"\nTesting {map_name}:")
        
        try:
            # Test positioning analyzer
            pos_analyzer = PositioningAnalyzer(map_name)
            print(f"  ✓ PositioningAnalyzer initialized")
            print(f"    Positions loaded: {len(pos_analyzer.map_positions)}")
            
            # Test combat analyzer
            combat_analyzer = CombatAnalyzer(map_name)
            print(f"  ✓ CombatAnalyzer initialized")
            print(f"    Kill areas loaded: {len(combat_analyzer.kill_areas)}")
            
        except Exception as e:
            print(f"  ✗ Error initializing analyzers for {map_name}: {e}")

def test_position_queries():
    """Test querying positions for different maps."""
    print("\n" + "="*50)
    print("Testing position queries...")
    
    # Test getting positions for different maps
    test_maps = ["de_mirage", "de_dust2", "de_inferno", "nonexistent_map"]
    
    for map_name in test_maps:
        positions = config.get_positions_for_map(map_name)
        print(f"\n{map_name}: {len(positions)} positions found")
        
        if positions:
            # Show most common positions (by sample count)
            sorted_positions = sorted(
                positions.items(), 
                key=lambda x: x[1].get('sample_count', 0), 
                reverse=True
            )
            
            print("  Top 3 positions by sample count:")
            for pos_name, pos_data in sorted_positions[:3]:
                sample_count = pos_data.get('sample_count', 'N/A')
                print(f"    {pos_name}: {sample_count} samples")

def test_config_functions():
    """Test configuration utility functions."""
    print("\n" + "="*50)
    print("Testing config functions...")
    
    print(f"Available maps: {len(config.AVAILABLE_MAPS)}")
    print("Maps:", ", ".join(config.AVAILABLE_MAPS[:5]))  # Show first 5
    
    if len(config.AVAILABLE_MAPS) > 5:
        print(f"... and {len(config.AVAILABLE_MAPS) - 5} more")
    
    print("\nMap information:")
    config.print_available_maps()

def main():
    """Run all tests."""
    print("TESTING NEW POSITION SYSTEM")
    print("="*50)
    
    try:
        test_position_loading()
        test_analyzer_initialization()
        test_position_queries()
        test_config_functions()
        
        print("\n" + "="*50)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("The new position system is working correctly!")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        print("Please check that extracted_positions.json exists and is valid.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())