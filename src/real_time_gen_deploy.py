import threading
import time
import sys
from datetime import datetime
from pathlib import Path

# Import functions from real_time_gen.py (reusing existing logic)
try:
    from .real_time_gen import (
        generate_snapshot_row, 
        append_row_to_csv, 
        get_column_names
    )
except ImportError:
    # If relative import fails, add project root to path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.real_time_gen import (
        generate_snapshot_row, 
        append_row_to_csv, 
        get_column_names
    )

def start_background_generator():
    """
    Starts a background thread that generates occupancy data every 5 seconds.
    This function returns the thread object.
    """
    def run_loop():
        # Calculate output path relative to project root
        # Assumes this file is in src/
        # We need to be careful about where __file__ resolves if imported from app.py
        # But since this file exists physically at src/real_time_gen_deploy.py, it should work.
        
        current_file = Path(__file__).resolve()
        # If this file is in src/, parent is src, parent.parent is project root
        if current_file.parent.name == 'src':
             project_root = current_file.parent.parent
        else:
             # Fallback
             project_root = Path.cwd()

        output_file = project_root / "data/library_occupancy.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = get_column_names()
        
        print(f"🚀 Background data generator started! Writing to {output_file}")
        
        while True:
            try:
                # Logic similar to real_time_gen.py
                timestamp = datetime.now().replace(microsecond=0)
                row_data = generate_snapshot_row(timestamp)
                append_row_to_csv(output_file, row_data, fieldnames)
                
                time.sleep(5)
            except Exception as e:
                print(f"Error in background generator: {e}")
                time.sleep(5) # Wait before retrying

    # Start as daemon thread so it closes when the main program exits
    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    return t

