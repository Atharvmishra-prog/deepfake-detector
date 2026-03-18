from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
import io
import os
import base64
import webbrowser
import threading

app = Flask(__name__, static_folder='Frontend')
CORS(app)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
MODEL_PATH = os.environ.get('MODEL_PATH', 'model/deepfake_detection.keras')
IMG_SIZE   = int(os.environ.get('IMG_SIZE', 299))
THRESHOLD  = float(os.environ.get('THRESHOLD', 0.50))
# ──────────────────────────────────────────────────────────────────────────────

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


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((IMG_SIZE, IMG_SIZE))
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def predict(image_bytes: bytes) -> dict:
    if model is None:
        import random
        score = random.uniform(0.0, 1.0)
        label = 'FAKE' if score > THRESHOLD else 'REAL'
        return {
            'label':      label,
            'confidence': round((score if label == 'FAKE' else 1 - score) * 100, 2),
            'fake_prob':  round(score * 100, 2),
            'real_prob':  round((1 - score) * 100, 2),
            'demo_mode':  True,
        }

    tensor    = preprocess_image(image_bytes)
    raw       = model.predict(tensor, verbose=0)
    fake_prob = float(raw[0][0])
    real_prob = 1.0 - fake_prob
    label     = 'FAKE' if fake_prob >= THRESHOLD else 'REAL'
    confidence = fake_prob if label == 'FAKE' else real_prob

    return {
        'label':      label,
        'confidence': round(confidence * 100, 2),
        'fake_prob':  round(fake_prob  * 100, 2),
        'real_prob':  round(real_prob  * 100, 2),
        'demo_mode':  False,
    }


@app.route('/')
def index():
    return send_from_directory('Frontend', 'index.html')


@app.route('/api/detect', methods=['POST'])
def detect():
    try:
        if 'image' in request.files:
            file = request.files['image']
            if not file.filename:
                return jsonify({'error': 'No file selected'}), 400
            image_bytes = file.read()
        elif request.is_json and 'image' in request.json:
            data_url = request.json['image']
            if ',' in data_url:
                data_url = data_url.split(',', 1)[1]
            image_bytes = base64.b64decode(data_url)
        else:
            return jsonify({'error': 'No image provided'}), 400

        try:
            Image.open(io.BytesIO(image_bytes)).verify()
        except Exception:
            return jsonify({'error': 'Invalid image file'}), 400

        result = predict(image_bytes)
        return jsonify(result), 200

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status':       'ok',
        'model_loaded': model is not None,
        'img_size':     IMG_SIZE,
        'threshold':    THRESHOLD,
    })


if __name__ == '__main__':
    load_deepfake_model()
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, host='0.0.0.0', port=5000)
