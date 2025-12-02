import time
import csv
import signal
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Import functions from rand_gen.py
# Handle both relative import (when used as module) and absolute import (when run as script)
try:
    from .rand_gen import (
        LIBRARIES,
        generate_realistic_occupancy,
        get_column_names
    )
except ImportError:
    # If relative import fails, try absolute import (for script execution)
    # Add project root to path if not already there
    project_root = Path(__file__).parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    from src.rand_gen import (
        LIBRARIES,
        generate_realistic_occupancy,
        get_column_names
    )

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\nStopping real-time generator...")
    running = False
    sys.exit(0)

# Only register signal handler if running as main script or in main thread
try:
    if __name__ == "__main__":
        signal.signal(signal.SIGINT, signal_handler)
except ValueError:
    # Ignored if not in main thread
    pass


def get_last_timestamp(csv_file: Path) -> datetime:
    """
    Get the last timestamp from the CSV file.
    If file doesn't exist or is empty, return None.
    """
    if not csv_file.exists():
        return None
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                return None
            # Get the last row's timestamp
            last_timestamp_str = rows[-1]['timestamp']
            return datetime.fromisoformat(last_timestamp_str)
    except (KeyError, ValueError, IndexError):
        return None


def generate_snapshot_row(timestamp: datetime) -> dict:
    """
    Generate a single occupancy snapshot row for the given timestamp.
    
    Args:
        timestamp: The timestamp for this snapshot
    
    Returns:
        Dictionary with timestamp and all library-floor occupancy data
    """
    row_data = {"timestamp": timestamp.isoformat()}
    
    for lib in LIBRARIES:
        # Use a base occupancy rate per library to add correlation between floors
        # (if one floor is busy, others in the same library might be too)
        library_base_rate = random.uniform(0.35, 0.65)
        
        for floor_data in lib["floors"]:
            capacity = floor_data["capacity"]
            
            # Generate realistic occupancy
            occupied = generate_realistic_occupancy(capacity, library_base_rate)
            
            # Store in row with column name format: "Library Name Floor N"
            col_name = f"{lib['name']} Floor {floor_data['floor']}"
            row_data[col_name] = occupied
    
    return row_data


def append_row_to_csv(csv_file: Path, row_data: dict, fieldnames: list):
    """
    Append a single row to the CSV file.
    Creates the file with headers if it doesn't exist.
    Maintains a maximum of 500 rows (plus header).
    
    Args:
        csv_file: Path to the CSV file
        row_data: Dictionary with row data
        fieldnames: List of column names
    """
    MAX_ROWS = 500
    rows = []
    
    # Read existing data
    if csv_file.exists():
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as e:
            print(f"Error reading CSV for append: {e}")
            # If error reading, we might overwrite corrupt file or start fresh
            # Let's try to append anyway by starting fresh if read failed significantly
            pass

    # Append new row
    rows.append(row_data)
    
    # Prune if needed
    if len(rows) > MAX_ROWS:
        rows = rows[-MAX_ROWS:]
    
    # Write back entire file (atomic-ish update)
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def real_time_generate(
    output_path: str = "data/library_occupancy.csv",
    interval_seconds: int = 5
):
    """
    Generate occupancy data in real-time and append to CSV every interval_seconds.
    Continues until stopped (Ctrl+C).
    
    Args:
        output_path: Path to the CSV file (relative to project root)
        interval_seconds: Time interval between rows in seconds
    """
    # Ensure the data directory exists
    output_file = Path(__file__).parent.parent / output_path
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get column names
    fieldnames = get_column_names()
    
    # Check if CSV exists and get last timestamp for info
    last_timestamp = get_last_timestamp(output_file)
    if last_timestamp:
        print(f"Found existing CSV with last entry at: {last_timestamp.isoformat()}")
    else:
        print("Starting new CSV file.")
    
    print(f"Generating occupancy data every {interval_seconds} seconds...")
    print("Press Ctrl+C to stop.\n")
    
    row_count = 0
    
    try:
        # Generate first snapshot immediately
        first_run = True
        
        while running:
            if first_run:
                # Generate immediately on first run
                snapshot_time = datetime.now().replace(microsecond=0)
                first_run = False
            else:
                # Wait for the interval
                time.sleep(interval_seconds)
                snapshot_time = datetime.now().replace(microsecond=0)
            
            # Generate the snapshot
            row_data = generate_snapshot_row(snapshot_time)
            
            # Append to CSV
            append_row_to_csv(output_file, row_data, fieldnames)
            
            row_count += 1
            print(f"[{snapshot_time.strftime('%H:%M:%S')}] Generated snapshot #{row_count}")
    
    except KeyboardInterrupt:
        pass
    
    print(f"\nStopped. Generated {row_count} snapshots total.")


if __name__ == "__main__":
    # Generate occupancy data in real-time every 5 seconds
    real_time_generate(
        output_path="data/library_occupancy.csv",
        interval_seconds=5
    )

