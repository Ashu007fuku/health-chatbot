import os
import json
from google.cloud import vision
from PIL import Image
from datetime import datetime
import io

# Paths
IMAGE_PATH = "trackreport5.jpg"
OUTPUT_DIR = "ocr_outputs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "newocr_table_google.json")
GOOGLE_CREDENTIALS = "obesity-bot-train-801a1cca327b.json"

# Create output dir if not exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS

def extract_text_with_google_vision(image_path, y_tolerance=25):
    client = vision.ImageAnnotatorClient()
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if not texts:
        return []
    # Get all detected words with bounding box coordinates
    words = []
    for t in texts[1:]:  # texts[0] is the full text, skip it
        if t.description.strip():
            # Use the top-left vertex for y/x
            v = t.bounding_poly.vertices[0]
            words.append({
                'text': t.description,
                'x': v.x if v.x is not None else 0,
                'y': v.y if v.y is not None else 0
            })
    # Sort and group by y-coordinate (like your previous logic)
    words.sort(key=lambda w: (w['y'], w['x']))
    rows = []
    current_row = []
    current_y = words[0]['y'] if words else 0
    for word in words:
        if abs(word['y'] - current_y) <= y_tolerance:
            current_row.append(word)
        else:
            rows.append([w['text'] for w in sorted(current_row, key=lambda w: w['x'])])
            current_row = [word]
            current_y = word['y']
    if current_row:
        rows.append([w['text'] for w in sorted(current_row, key=lambda w: w['x'])])
    return rows, words

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved OCR data to: {path}")

def main():
    print(f"📸 Running Google Vision OCR on: {IMAGE_PATH}")
    rows, words = extract_text_with_google_vision(IMAGE_PATH)
    print("\n📋 Structured Table Output:")
    for row in rows:
        print(" | ".join(row))
    print("\n📐 Word Coordinates:")
    for w in words:
        print(f"{w['text']}: (x={w['x']}, y={w['y']})")
    save_json(rows, OUTPUT_FILE)

if __name__ == "__main__":
    main()
