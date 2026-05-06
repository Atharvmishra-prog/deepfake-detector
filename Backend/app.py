from flask import Flask, send_from_directory
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import cv2
import io
import os
import base64
import webbrowser
import threading

# ─── FLASK SETUP ──────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='../Frontend', static_url_path='')
CORS(app)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
MODEL_PATH = os.environ.get('MODEL_PATH', 'model/deepfake_fixed_final.keras')
IMG_SIZE   = int(os.environ.get('IMG_SIZE',   299))
THRESHOLD  = float(os.environ.get('THRESHOLD', 0.45))
VIDEO_THRESHOLD = float(os.environ.get('VIDEO_THRESHOLD', 0.65))
FRAME_STEP = int(os.environ.get('FRAME_STEP', 5))   # analyse every Nth frame
MAX_FRAMES = int(os.environ.get('MAX_FRAMES', 60))    # max frames to analyse
TOP_FRAMES = int(os.environ.get('TOP_FRAMES', 6))     # most suspicious frames to return

# ─── MODEL ────────────────────────────────────────────────────────────────────
model = None

def load_deepfake_model():
    global model
    try:
        model = load_model(MODEL_PATH, compile=False)
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        print(f"[INFO] Model loaded from {MODEL_PATH}")
        print(f"[INFO] Input shape: {model.input_shape}")
    except Exception as e:
        print(f"[WARNING] Could not load model: {e}")
        model = None

def get_model():
    return model

# ─── PREDICT ──────────────────────────────────────────────────────────────────
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Resize and normalize image for Xception input (299x299, /255)."""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    if img.width > 1000 or img.height > 1000:
        img.thumbnail((1000, 1000), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        img = Image.open(buffer).convert('RGB')
    img = img.resize((IMG_SIZE, IMG_SIZE))
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)

def predict_image_bytes(image_bytes: bytes) -> float:
    """Returns fake_prob (0-1). raw score = real_prob since Class_0=Real."""
    tensor    = preprocess_image(image_bytes)
    raw       = model.predict(tensor, verbose=0)
    fake_prob = float(raw[0][0])
    real_prob = 1.0 - fake_prob
    return fake_prob

def frame_to_bytes(frame) -> bytes:
    """Convert OpenCV frame to JPEG bytes."""
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buf.tobytes()

def frame_to_base64(frame) -> str:
    """Convert OpenCV frame to base64 data URL."""
    jpg_bytes = frame_to_bytes(frame)
    return 'data:image/jpeg;base64,' + base64.b64encode(jpg_bytes).decode('utf-8')

# ─── SERVE FRONTEND ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('../Frontend', 'index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok', 'model_loaded': model is not None, 'threshold': THRESHOLD}

# ─── REGISTER ROUTES ──────────────────────────────────────────────────────────
from Backend.routes_image import image_bp
from Backend.routes_video import video_bp
app.register_blueprint(image_bp)
app.register_blueprint(video_bp)

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    load_deepfake_model()
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, host='0.0.0.0', port=5000)