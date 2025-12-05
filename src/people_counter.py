import threading
import time
import sys
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO
import csv

# Import LIBRARIES from lib_configs
try:
    from .lib_configs import LIBRARIES
except ImportError:
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.lib_configs import LIBRARIES

def get_column_names():
    """
    Generate the CSV column names based on the LIBRARIES configuration.
    """
    columns = ["timestamp"]
    for lib in LIBRARIES:
        for floor_data in lib["floors"]:
            columns.append(f"{lib['name']} Floor {floor_data['floor']}")
    return columns

def append_row_to_csv(csv_file: Path, row_data: dict, fieldnames: list):
    """
    Append a single row to the CSV file.
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
            pass

    # Append new row
    rows.append(row_data)
    
    # Prune if needed
    if len(rows) > MAX_ROWS:
        rows = rows[-MAX_ROWS:]
    
    # Write back entire file
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def count_people_in_images(model, image_index):
    """
    Batch process images for the i-th frame (image_index) across all library floors.
    Returns a dictionary mapping "Library Floor N" -> count.
    """
    
    project_root = Path(__file__).parent.parent
    images_base_path = project_root / "data/lib_images"
    
    image_paths = []
    keys = []
    
    # Collect all image paths for the current index
    for lib in LIBRARIES:
        lib_name = lib["name"]
        for floor_data in lib["floors"]:
            floor_num = floor_data["floor"]
            
            # Construct expected image path: data/lib_images/{LibName}/floor{N}/frame{i}.png
            # Note: frame index is 1-based (frame1..frame9)
            img_path = images_base_path / lib_name / f"floor{floor_num}" / f"frame{image_index}.png"
            
            if img_path.exists():
                image_paths.append(str(img_path))
                keys.append(f"{lib_name} Floor {floor_num}")
            else:
                # If image missing, we can't count. We'll handle this gracefully (e.g. 0 or previous value)
                # For batch inference, we skip it and handle the missing key later
                pass
    
    counts = {}
    
    if image_paths:
        # Batch inference
        # verbose=False reduces console noise
        results = model(image_paths, verbose=False)
        
        for key, result in zip(keys, results):
            # Count people (class 0 in COCO dataset is 'person')
            # result.boxes.cls contains class indices
            people_count = (result.boxes.cls == 0).sum().item()
            
            # Multiply by 8 as requested
            final_count = int(people_count * 8)
            
            # Check capacity for this floor and clamp if needed
            # We need to find the capacity for the library/floor corresponding to 'key'
            # key format is "{LibName} Floor {N}"
            for lib in LIBRARIES:
                if lib["name"] in key:
                    for floor_data in lib["floors"]:
                        if f"{lib['name']} Floor {floor_data['floor']}" == key:
                            capacity = floor_data["capacity"]
                            if final_count > capacity:
                                final_count = capacity
                            break
            
            counts[key] = final_count
            
    return counts

def start_background_generator():
    """
    Starts a background thread that generates occupancy data using YOLO.
    """
    def run_loop():
        project_root = Path(__file__).parent.parent
        output_file = project_root / "data/library_occupancy.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        model_path = project_root / "models/yolo11n.pt"
        
        print("🚀 Loading YOLO model...")
        # Load YOLO model
        try:
            model = YOLO(str(model_path))
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            return

        fieldnames = get_column_names()
        
        print(f"🚀 People counter started! Writing to {output_file}")
        
        # We cycle through frames 1 to 9
        frame_index = 1
        
        while True:
            try:
                start_time = time.time()
                timestamp = datetime.now().replace(microsecond=0)
                
                # Get counts for current frame index
                counts = count_people_in_images(model, frame_index)
                
                # Construct row data
                row_data = {"timestamp": timestamp.isoformat()}
                
                # Fill in counts, defaulting to 0 if image was missing
                # (Or could default to capacity/last value if preferred)
                for lib in LIBRARIES:
                    for floor_data in lib["floors"]:
                        key = f"{lib['name']} Floor {floor_data['floor']}"
                        row_data[key] = counts.get(key, 0)
                
                append_row_to_csv(output_file, row_data, fieldnames)
                
                print(f"[{timestamp.strftime('%H:%M:%S')}] Processed frame{frame_index} (Batch size: {len(counts)})")
                
                # Cycle frame index 1-9
                frame_index += 1
                if frame_index > 9:
                    frame_index = 1
                
                # Wait for remainder of 5 seconds
                elapsed = time.time() - start_time
                sleep_time = max(0, 5 - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error in people counter: {e}")
                time.sleep(5)

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    # Test run if executed directly
    t = start_background_generator()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")

