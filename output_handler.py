# output_handler.py
"""Handles output to both console and file."""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import config

class OutputHandler:
    """Manages output to console and/or file."""
    
    def __init__(self, map_name: str = "analysis"):
        self.map_name = map_name
        self.file_handle: Optional[object] = None
        self.original_stdout = sys.stdout
        
        # Create output directory if needed
        if config.OUTPUT_TO_FILE:
            config.OUTPUT_DIR.mkdir(exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{map_name}_{timestamp}.txt"
            self.filepath = config.OUTPUT_DIR / filename
            
            # Open file for writing
            self.file_handle = open(self.filepath, 'w', encoding='utf-8')
    
    def write(self, text: str):
        """Write text to configured outputs."""
        # Write to console
        if config.OUTPUT_TO_CONSOLE:
            self.original_stdout.write(text)
            self.original_stdout.flush()
        
        # Write to file
        if config.OUTPUT_TO_FILE and self.file_handle:
            self.file_handle.write(text)
            self.file_handle.flush()
    
    def flush(self):
        """Flush both outputs."""
        if config.OUTPUT_TO_CONSOLE:
            self.original_stdout.flush()
        if self.file_handle:
            self.file_handle.flush()
    
    def close(self):
        """Close file handle and restore stdout."""
        if self.file_handle:
            self.file_handle.close()
            if config.OUTPUT_TO_FILE:
                print(f"\nResults saved to: {self.filepath}", file=self.original_stdout)
    
    def __enter__(self):
        """Context manager entry."""
        sys.stdout = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        sys.stdout = self.original_stdout
        self.close()