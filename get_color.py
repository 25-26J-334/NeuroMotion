from PIL import Image
import numpy as np
from collections import Counter

def get_dominant_color(image_path):
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize((50, 50))
        pixels = np.array(img).reshape(-1, 3)
        # Filter out black/dark colors
        valid_pixels = [tuple(p) for p in pixels if sum(p) > 50]
        if not valid_pixels:
            valid_pixels = [tuple(p) for p in pixels]
            
        counter = Counter(valid_pixels)
        most_common = counter.most_common(5)
        
        # Pick the most vibrant/distinct color
        # Tangerine is orange-ish.
        for color, count in most_common:
            r, g, b = color
            # Simple check for orange/tangerine: High Red, Medium Green, Low Blue
            print(f"Candidate: RGB{color} Hex: #{r:02x}{g:02x}{b:02x}")
            
    except Exception as e:
        print(f"Error: {e}")

get_dominant_color("C:/Users/User/.gemini/antigravity/brain/67e3d052-f82e-4cdb-8647-bc60c934617c/uploaded_image_1767532364812.png")
