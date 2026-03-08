import numpy as np
import base64
import json
from io import BytesIO
from pathlib import Path
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications import VGG16
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Dropout


BASE_DIR = Path(__file__).resolve().parent

# Rebuild model architecture
base_model = VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
base_model.trainable = False
model = Sequential([
    base_model,
    Flatten(),
    Dense(512, activation='relu'),
    Dropout(0.5),
    Dense(42, activation='softmax')
])

# Load trained weights
model.load_weights(str(BASE_DIR / "cropdoctor_weights.weights.h5"))

# Load config
with open(BASE_DIR / "model_config.json", "r") as f:
    config = json.load(f)
class_labels = config["class_labels"]
region_map = config["region_map"]


def image_file_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def predict(image_base64):
    payload = image_base64.strip()
    if payload.startswith("data:") and "," in payload:
        payload = payload.split(",", 1)[1]
    payload = "".join(payload.split())
    padding = (-len(payload)) % 4
    if padding:
        payload += "=" * padding
    img_data = base64.b64decode(payload)
    img = Image.open(BytesIO(img_data)).convert("RGB").resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prediction = model.predict(img_array, verbose=0)
    idx = int(np.argmax(prediction))
    confidence = float(np.max(prediction))
    disease = class_labels[idx]
    region = region_map.get(disease, "Unknown")
    return {
        "disease": disease,
        "confidence": round(confidence, 4),
        "confidence_pct": f"{confidence * 100:.2f}%",
        "region": region
    }

if __name__ == "__main__":
    image_path = "/Users/aditya/Documents/John Deere Hackathon/Backend/image_data/maize_earrot.jpg"
    image_base64 = image_file_to_base64(image_path)
    result = predict(image_base64)

    print("=" * 50)
    print("CROP DISEASE DETECTION REPORT")
    print("=" * 50)
    print(f"  Image path : {image_path}")
    print(f"  Disease    : {result['disease']}")
    print(f"  Confidence : {result['confidence_pct']}")
    print(f"  Region     : {result['region']}")
    print("=" * 50)

