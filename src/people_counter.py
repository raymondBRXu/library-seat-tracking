import time
import sys
from pathlib import Path

# Try to import ultralytics, handle if not installed
try:
    from ultralytics import YOLO
except ImportError:
    print("Error: 'ultralytics' package not found. Please install it using: pip install ultralytics")
    sys.exit(1)

def count_people_in_images(images_dir="data/images", model_path="models/yolo11n.pt", interval=5):
    """
    Count people in images using YOLO model.
    
    Args:
        images_dir: Directory containing images (relative to project root)
        model_path: Path to YOLO model file (relative to project root)
        interval: Time interval between processing images (seconds)
    """
    # Define base paths
    # This file is in src/, so project root is parent directory
    project_root = Path(__file__).parent.parent
    img_dir_path = project_root / images_dir
    model_file_path = project_root / model_path
    
    # Verify paths
    if not model_file_path.exists():
        print(f"Error: Model file not found at {model_file_path}")
        return
        
    if not img_dir_path.exists():
        print(f"Error: Image directory not found at {img_dir_path}")
        return
    
    # Load model
    print(f"Loading model from {model_file_path}...")
    try:
        model = YOLO(str(model_file_path))
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Get images
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.PNG']
    images = []
    for ext in extensions:
        images.extend(img_dir_path.glob(ext))
    
    # Sort images by name to ensure order
    images.sort(key=lambda x: x.name)
    
    if not images:
        print(f"No images found in {img_dir_path}")
        return

    print(f"Found {len(images)} images. Starting counting loop...")
    print("-" * 50)
    
    try:
        for i, img_path in enumerate(images):
            start_time = time.time()
            
            # Run inference
            # classes=[0] filters for person class in COCO dataset (class 0 is person)
            # verbose=False suppresses standard YOLO output
            results = model(str(img_path), verbose=False, classes=[0]) 
            
            # Count people
            # results is a list of Results objects
            result = results[0]
            people_count = len(result.boxes)
            
            print(f"[{i+1}/{len(images)}] Image: {img_path.name} | People Count: {people_count}")
            
            # Wait for the remaining time in the interval
            if i < len(images) - 1:  # Don't sleep after the last image
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    count_people_in_images()

