"""
Vision Simulator - Simulates dashboard camera input
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_dashboard_image(state: dict, warning_type: str = None) -> np.ndarray:
    """Create a simulated dashboard image"""
    # Create blank image
    img = np.zeros((300, 500, 3), dtype=np.uint8)
    img.fill(255)  # White background
    
    # Draw dashboard elements
    # Speed display
    cv2.putText(img, f"Speed: {state['speed']} km/h", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Fuel gauge
    cv2.rectangle(img, (50, 150), (250, 180), (0, 255, 0), -1)
    cv2.rectangle(img, (50, 150), (50 + int(200 * state['fuel_level'] / 100), 180), (0, 200, 0), -1)
    cv2.putText(img, f"Fuel: {state['fuel_level']}%", (260, 170), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Temperature
    cv2.putText(img, f"Temp: {state['cabin_temp']}°C", (50, 220), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Add warning lights
    if warning_type == "red":
        # Red warning circle
        cv2.circle(img, (400, 100), 30, (0, 0, 255), -1)
        cv2.putText(img, "!", (390, 108), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    elif warning_type == "yellow":
        # Yellow warning circle
        cv2.circle(img, (400, 100), 30, (0, 255, 255), -1)
        cv2.putText(img, "!", (390, 108), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    else:
        # Green status
        cv2.circle(img, (400, 100), 30, (0, 255, 0), -1)
        cv2.putText(img, "OK", (380, 108), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return img

if __name__ == "__main__":
    # Test
    state = {
        "speed": 60,
        "fuel_level": 75,
        "cabin_temp": 22
    }
    
    img = create_dashboard_image(state, warning_type="red")
    cv2.imwrite("dashboard_test.jpg", img)
    print("Dashboard image created: dashboard_test.jpg")
