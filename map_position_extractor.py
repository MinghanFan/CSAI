# map_position_extractor.py
"""
Extract position ranges for each place/location on CS2 maps from demo files.
This program analyzes demo files to automatically generate coordinate ranges
for different map locations, replacing hardcoded position definitions.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from awpy import Demo
from typing import Dict, List, Tuple, Optional
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

class MapPositionExtractor:
    """Extracts and analyzes position data from CS2 demo files."""
    
    def __init__(self, demo_directory: str, map_name: Optional[str] = None):
        """
        Initialize the position extractor.
        
        Args:
            demo_directory: Directory containing demo files
            map_name: Specific map to analyze (if None, will auto-detect)
        """
        self.demo_directory = Path(demo_directory)
        self.map_name = map_name
        self.position_data = defaultdict(list)
        self.coordinate_ranges = {}
        
    def load_and_analyze_demos(self) -> Dict[str, Dict]:
        """
        Load all demo files and extract position data.
        
        Returns:
            Dictionary containing position analysis results
        """
        # Recursively search for demo files in all subdirectories
        demo_files = [f for f in self.demo_directory.rglob("*.dem") 
                     if not f.name.startswith('.')]  # Skip hidden files
        
        if not demo_files:
            raise FileNotFoundError(f"No demo files found in {self.demo_directory} or its subdirectories")
        
        print(f"Found {len(demo_files)} demo files in directory tree")
        
        # Show the directory structure
        subdirs = set(f.parent.relative_to(self.demo_directory) for f in demo_files)
        if subdirs:
            print("Demo files found in subdirectories:")
            for subdir in sorted(subdirs):
                subdir_files = [f for f in demo_files if f.parent.relative_to(self.demo_directory) == subdir]
                print(f"  {subdir}: {len(subdir_files)} files")
        print()
        
        all_position_data = []
        processed_demos = 0
        
        for demo_file in demo_files:
            try:
                print(f"Processing: {demo_file.name}")
                demo = Demo(demo_file)
                demo.parse()
                
                # Get map name from header
                current_map = demo.header.get("map_name", "unknown")
                print(f"  Map: {current_map}")
                
                # If specific map requested, skip others
                if self.map_name and current_map != self.map_name:
                    print(f"  Skipping - not {self.map_name}")
                    continue
                
                # Extract position data
                ticks_df = demo.ticks.to_pandas()
                position_df = self._extract_position_data(ticks_df, current_map)
                
                if not position_df.empty:
                    all_position_data.append(position_df)
                    processed_demos += 1
                    print(f"  Extracted {len(position_df)} position records")
                
            except Exception as e:
                print(f"  Error processing {demo_file.name}: {e}")
                continue
        
        if not all_position_data:
            raise ValueError("No position data extracted from any demo")
        
        # Combine all position data
        combined_df = pd.concat(all_position_data, ignore_index=True)
        print(f"\nCombined data: {len(combined_df)} total position records from {processed_demos} demos")
        
        # Analyze positions
        return self._analyze_positions(combined_df)
    
    def _extract_position_data(self, ticks_df: pd.DataFrame, map_name: str) -> pd.DataFrame:
        """Extract relevant position data from ticks DataFrame."""
        required_columns = ['X', 'Y', 'Z', 'last_place_name']
        
        # Check which columns exist (handle different naming conventions)
        available_columns = []
        column_mapping = {}
        
        for col in required_columns:
            if col in ticks_df.columns:
                available_columns.append(col)
                column_mapping[col] = col
            elif col == 'last_place_name' and 'place' in ticks_df.columns:
                available_columns.append('place')
                column_mapping[col] = 'place'
        
        if len(available_columns) < 3:  # Need at least X, Y, and place
            print(f"  Warning: Missing required columns. Available: {list(ticks_df.columns)}")
            return pd.DataFrame()
        
        # Select and rename columns
        position_df = ticks_df[available_columns].copy()
        if 'place' in position_df.columns and 'last_place_name' not in position_df.columns:
            position_df = position_df.rename(columns={'place': 'last_place_name'})
        
        # Clean the data
        position_df = position_df.dropna(subset=['X', 'Y', 'last_place_name'])
        position_df = position_df[position_df['last_place_name'] != '']
        position_df['map_name'] = map_name
        
        return position_df
    
    def _analyze_positions(self, position_df: pd.DataFrame) -> Dict[str, Dict]:
        """Analyze position data to extract coordinate ranges for each place."""
        results = {}
        
        # Group by map and place
        for map_name in position_df['map_name'].unique():
            map_data = position_df[position_df['map_name'] == map_name]
            results[map_name] = {}
            
            print(f"\nAnalyzing positions for {map_name}:")
            
            place_stats = []
            for place_name in sorted(map_data['last_place_name'].unique()):
                place_data = map_data[map_data['last_place_name'] == place_name]
                
                if len(place_data) < 10:  # Skip places with too few samples
                    continue
                
                # Calculate coordinate ranges for X, Y, and Z
                x_min, x_max = place_data['X'].min(), place_data['X'].max()
                y_min, y_max = place_data['Y'].min(), place_data['Y'].max()
                z_min, z_max = place_data['Z'].min(), place_data['Z'].max()
                
                # Add some padding to ranges
                x_padding = (x_max - x_min) * 0.1 if x_max != x_min else 50
                y_padding = (y_max - y_min) * 0.1 if y_max != y_min else 50
                z_padding = (z_max - z_min) * 0.1 if z_max != z_min else 25
                
                x_range = [float(x_min - x_padding), float(x_max + x_padding)]
                y_range = [float(y_min - y_padding), float(y_max + y_padding)]
                z_range = [float(z_min - z_padding), float(z_max + z_padding)]
                
                # Calculate statistics
                sample_count = len(place_data)
                center_x = float(place_data['X'].mean())
                center_y = float(place_data['Y'].mean())
                center_z = float(place_data['Z'].mean())
                
                position_info = {
                    'x_range': x_range,
                    'y_range': y_range,
                    'z_range': z_range,
                    'center': [center_x, center_y, center_z],
                    'sample_count': sample_count,
                    'x_std': float(place_data['X'].std()),
                    'y_std': float(place_data['Y'].std()),
                    'z_std': float(place_data['Z'].std())
                }
                
                results[map_name][place_name] = position_info
                place_stats.append({
                    'place': place_name,
                    'samples': sample_count,
                    'x_range': f"({x_range[0]:.0f}, {x_range[1]:.0f})",
                    'y_range': f"({y_range[0]:.0f}, {y_range[1]:.0f})"
                })
                
                print(f"  {place_name}: {sample_count} samples, "
                      f"X: {x_range[0]:.0f} to {x_range[1]:.0f}, "
                      f"Y: {y_range[0]:.0f} to {y_range[1]:.0f}, "
                      f"Z: {z_range[0]:.0f} to {z_range[1]:.0f}")
            
            # Store for potential visualization
            self.position_data[map_name] = map_data
            
        return results
    
    def generate_config_code(self, results: Dict[str, Dict], map_name: str = None) -> str:
        """Generate Python config code for the extracted positions."""
        if map_name:
            maps_to_process = [map_name] if map_name in results else []
        else:
            maps_to_process = list(results.keys())
        
        config_code = "# Auto-generated position definitions\n\n"
        
        for map_name in maps_to_process:
            map_positions = results[map_name]
            
            # Clean map name for variable name
            clean_map_name = map_name.replace("de_", "").replace("cs_", "").upper()
            
            config_code += f"# {map_name} position definitions\n"
            config_code += f"{clean_map_name}_POSITIONS = {{\n"
            
            for place_name, position_info in sorted(map_positions.items()):
                # Clean place name for dictionary key
                clean_place = place_name.replace(" ", "_").replace("-", "_").lower()
                x_range = position_info['x_range']
                y_range = position_info['y_range']
                z_range = position_info['z_range']
                
                config_code += f"    '{clean_place}': {{\n"
                config_code += f"        'x_range': ({x_range[0]:.0f}, {x_range[1]:.0f}),\n"
                config_code += f"        'y_range': ({y_range[0]:.0f}, {y_range[1]:.0f}),\n"
                config_code += f"        'z_range': ({z_range[0]:.0f}, {z_range[1]:.0f})\n"
                config_code += f"    }},  # {position_info['sample_count']} samples\n"
            
            config_code += "}\n\n"
        
        return config_code
    
    def save_results(self, results: Dict[str, Dict], output_file: str = "extracted_positions.json"):
        """Save results to JSON file."""
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_path}")
    
    def create_position_visualization(self, map_name: str, save_plot: bool = True):
        """Create a visualization of the extracted positions."""
        if map_name not in self.position_data:
            print(f"No data available for {map_name}")
            return
        
        map_data = self.position_data[map_name]
        
        plt.figure(figsize=(15, 12))
        
        # Create scatter plot colored by place
        places = map_data['last_place_name'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(places)))
        
        for place, color in zip(places, colors):
            place_data = map_data[map_data['last_place_name'] == place]
            plt.scatter(place_data['X'], place_data['Y'], 
                       c=[color], label=place, alpha=0.6, s=1)
        
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        plt.title(f'Player Positions on {map_name}')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        
        # Invert Y axis to match typical map orientation
        plt.gca().invert_yaxis()
        
        plt.tight_layout()
        
        if save_plot:
            plot_path = f"{map_name}_positions.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            print(f"Position visualization saved to: {plot_path}")
        
        plt.show()
    
    def print_summary_statistics(self, results: Dict[str, Dict]):
        """Print summary statistics for extracted positions."""
        print("\n" + "="*60)
        print("POSITION EXTRACTION SUMMARY")
        print("="*60)
        
        for map_name, positions in results.items():
            print(f"\n{map_name.upper()}:")
            print(f"  Total places found: {len(positions)}")
            
            total_samples = sum(pos['sample_count'] for pos in positions.values())
            print(f"  Total position samples: {total_samples:,}")
            
            # Top places by sample count
            sorted_places = sorted(positions.items(), 
                                 key=lambda x: x[1]['sample_count'], reverse=True)
            
            print(f"  Top 5 most common places:")
            for place, info in sorted_places[:5]:
                print(f"    {place}: {info['sample_count']:,} samples")


def main():
    """Main function to run the position extractor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract position ranges from CS2 demo files")
    parser.add_argument("demo_directory", help="Directory containing demo files")
    parser.add_argument("--map", help="Specific map to analyze (e.g., de_mirage)")
    parser.add_argument("--output", default="extracted_positions.json", 
                       help="Output file for results")
    parser.add_argument("--config-output", help="Output file for Python config code")
    parser.add_argument("--visualize", action="store_true", 
                       help="Create position visualization")
    
    args = parser.parse_args()
    
    try:
        # Initialize extractor
        extractor = MapPositionExtractor(args.demo_directory, args.map)
        
        # Extract positions
        results = extractor.load_and_analyze_demos()
        
        # Print summary
        extractor.print_summary_statistics(results)
        
        # Save results
        extractor.save_results(results, args.output)
        
        # Generate config code
        config_code = extractor.generate_config_code(results, args.map)
        print("\n" + "="*60)
        print("GENERATED CONFIG CODE:")
        print("="*60)
        print(config_code)
        
        if args.config_output:
            with open(args.config_output, 'w') as f:
                f.write(config_code)
            print(f"Config code saved to: {args.config_output}")
        
        # Create visualization if requested
        if args.visualize:
            for map_name in results.keys():
                extractor.create_position_visualization(map_name)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())