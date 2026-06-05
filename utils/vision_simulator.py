"""
Dashboard image simulator for testing vision analysis
"""
import numpy as np

def create_dashboard_image(width=640, height=480, warning_type=None):
    """Create a simulated dashboard image with optional warning lights"""
    try:
        import cv2
    except ImportError:
        print("OpenCV not available")
        return None
    
    # Black background
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add dashboard layout
    cv2.rectangle(img, (50, 50), (width - 50, height - 50), (40, 40, 40), -1)
    
    # Add warning lights
    if warning_type == "red":
        cv2.circle(img, (width // 2, height // 2), 40, (0, 0, 255), -1)
    elif warning_type == "yellow":
        cv2.circle(img, (width // 2, height // 2), 40, (0, 255, 255), -1)
    
    return img


def save_dashboard_image(path, warning_type=None):
    """Save a simulated dashboard image to disk"""
    try:
        import cv2
        img = create_dashboard_image(warning_type=warning_type)
        if img is not None:
            cv2.imwrite(path, img)
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False
