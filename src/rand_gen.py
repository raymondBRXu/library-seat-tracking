import random
import csv
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Import LIBRARIES from lib_configs
# Handle both relative import (when used as module) and absolute import (when run as script)
try:
    from .lib_configs import LIBRARIES
except ImportError:
    # If relative import fails, try absolute import (for script execution)
    # Add project root to path if not already there
    project_root = Path(__file__).parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    from src.lib_configs import LIBRARIES

def generate_realistic_occupancy(capacity: int, base_occupancy_rate: float = None) -> int:
    """
    Generate realistic occupancy that doesn't exceed capacity.
    Uses a normal distribution centered around 40-60% occupancy for realism.
    
    Args:
        capacity: Maximum capacity of the floor
        base_occupancy_rate: Optional base rate (0-1) to add correlation between floors
    
    Returns:
        Occupied count (0 to capacity)
    """
    # If no base rate provided, generate one centered around 45-55% (realistic library usage)
    if base_occupancy_rate is None:
        base_occupancy_rate = random.uniform(0.35, 0.65)
    
    # Add some variance (±15%) to make it more dynamic
    variance = random.uniform(-0.15, 0.15)
    target_rate = base_occupancy_rate + variance
    
    # Clamp to reasonable bounds (20% to 90% for realism - libraries rarely 100% full or empty)
    target_rate = max(0.20, min(0.90, target_rate))
    
    # Calculate target occupancy
    target_occupancy = int(capacity * target_rate)
    
    # Add small random noise (±5% of capacity) for more natural variation
    noise = random.randint(-max(1, int(capacity * 0.05)), max(1, int(capacity * 0.05)))
    occupied = target_occupancy + noise
    
    # Ensure it's within valid bounds
    occupied = max(0, min(capacity, occupied))
    
    return occupied


def get_column_names():
    """
    Generate column names for CSV based on all library-floor combinations.
    Returns list of column names: ['timestamp', 'Olin Library Floor 1', ...]
    """
    columns = ["timestamp"]
    for lib in LIBRARIES:
        for floor_data in lib["floors"]:
            col_name = f"{lib['name']} Floor {floor_data['floor']}"
            columns.append(col_name)
    return columns


def update_occupancy_csv(output_path: str = "data/library_occupancy.csv"):
    """
    Generate new occupancy data for all libraries and floors, and save to CSV.
    Each row represents a complete snapshot of all libraries at a single timestamp.
    
    Args:
        output_path: Path to the CSV file (relative to project root)
    """
    # Ensure the data directory exists
    output_file = Path(__file__).parent.parent / output_path
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate column names
    fieldnames = get_column_names()
    
    # Generate occupancy data for all libraries/floors at this timestamp
    timestamp = datetime.now().isoformat()
    row_data = {"timestamp": timestamp}
    
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
    
    # Check if file exists to determine if we need headers
    file_exists = output_file.exists()
    
    with open(output_file, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file is new
        if not file_exists:
            writer.writeheader()
        
        # Write single row representing complete snapshot
        writer.writerow(row_data)
    
    print(f"Updated occupancy snapshot saved to {output_file}")
    print(f"Generated snapshot at {timestamp} with {len(fieldnames) - 1} library-floor combinations")
    
    return row_data


def generate_batch_occupancy_csv(
    num_rows: int = 100,
    start_time: str = "2025-11-21 9:00:00",
    interval_seconds: int = 5,
    output_path: str = "data/library_occupancy.csv"
):
    """
    Generate multiple occupancy snapshots with specified timestamps.
    
    Args:
        num_rows: Number of rows to generate
        start_time: Start time in format "YYYY-MM-DD HH:MM:SS"
        interval_seconds: Time interval between rows in seconds
        output_path: Path to the CSV file (relative to project root)
    """
    # Ensure the data directory exists
    output_file = Path(__file__).parent.parent / output_path
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Parse start time
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    
    # Generate column names
    fieldnames = get_column_names()
    
    # Generate all rows
    all_rows = []
    current_time = start_dt
    
    for i in range(num_rows):
        row_data = {"timestamp": current_time.isoformat()}
        
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
        
        all_rows.append(row_data)
        
        # Increment time by interval
        current_time += timedelta(seconds=interval_seconds)
    
    # Write all rows to CSV (overwrite existing file)
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"Generated {num_rows} occupancy snapshots saved to {output_file}")
    print(f"Time range: {start_dt.isoformat()} to {current_time.isoformat()}")
    print(f"Interval: {interval_seconds} seconds between snapshots")
    
    return all_rows


if __name__ == "__main__":
    # Generate 100 rows starting from 2025-11-21 9:00:00 with 5-second intervals
    generate_batch_occupancy_csv(
        num_rows=100,
        start_time="2025-11-21 9:00:00",
        interval_seconds=5
    )

