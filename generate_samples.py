#!/usr/bin/env python3
"""
Sample data generator for CBIR demo
Creates random colored rectangles as sample images
"""

import numpy as np
import cv2
from pathlib import Path
import random

def generate_sample_images(output_dir: str = "data/images", count: int = 50):
    """Generate sample colored images for testing"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    colors = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'purple': (128, 0, 128),
        'orange': (255, 165, 0),
        'pink': (255, 192, 203),
        'cyan': (0, 255, 255),
    }
    
    patterns = ['solid', 'gradient', 'stripes', 'circles']
    
    print(f"Generating {count} sample images...")
    
    for i in range(count):
        # Random size
        width = random.randint(200, 400)
        height = random.randint(200, 400)
        
        # Random color
        color_name = random.choice(list(colors.keys()))
        color = colors[color_name]
        
        # Random pattern
        pattern = random.choice(patterns)
        
        # Create image
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        if pattern == 'solid':
            img[:] = color
        elif pattern == 'gradient':
            for y in range(height):
                intensity = int((y / height) * 255)
                img[y, :] = (
                    int(color[0] * intensity / 255),
                    int(color[1] * intensity / 255),
                    int(color[2] * intensity / 255)
                )
        elif pattern == 'stripes':
            stripe_width = 20
            for x in range(0, width, stripe_width * 2):
                img[:, x:x+stripe_width] = color
        elif pattern == 'circles':
            img[:] = (200, 200, 200)  # Gray background
            num_circles = random.randint(3, 8)
            for _ in range(num_circles):
                center = (random.randint(0, width), random.randint(0, height))
                radius = random.randint(20, 60)
                cv2.circle(img, center, radius, color, -1)
        
        # Save image
        filename = f"{color_name}_{pattern}_{i:03d}.jpg"
        filepath = output_path / filename
        cv2.imwrite(str(filepath), img)
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{count} images...")
    
    print(f"✅ Successfully generated {count} images in {output_dir}")
    print("\nNext steps:")
    print("1. Start the application: docker-compose up")
    print("2. Build indexes: docker-compose exec backend python utils/build_index.py")
    print("3. Open http://localhost:3000 and start searching!")

if __name__ == "__main__":
    generate_sample_images(count=100)
