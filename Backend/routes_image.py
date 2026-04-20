from flask import Blueprint, request, jsonify
from PIL import Image
import io
import base64

image_bp = Blueprint('image', __name__)


def extract_image_bytes(req):
    """Extract image bytes from multipart or JSON request."""
    if 'image' in req.files:
        file = req.files['image']
        if not file.filename:
            return None, 'No file selected'
        return file.read(), None
    elif req.is_json and 'image' in req.json:
        data_url = req.json['image']
        if ',' in data_url:
            data_url = data_url.split(',', 1)[1]
        return base64.b64decode(data_url), None
    return None, 'No image provided'


@image_bp.route('/api/detect', methods=['POST'])
def detect_image():
    try:
        # ── 1. Extract image ──────────────────────────────────────────────────
        image_bytes, err = extract_image_bytes(request)
        if err:
            return jsonify({'error': err}), 400

        # ── 2. Validate image ─────────────────────────────────────────────────
        try:
            Image.open(io.BytesIO(image_bytes)).verify()
        except Exception:
            return jsonify({'error': 'Invalid image file'}), 400

        # ── 3. Import shared utils from app ───────────────────────────────────
        from Backend.app import predict_image_bytes, model, THRESHOLD

        # ── 4. Demo mode ──────────────────────────────────────────────────────
        if model is None:
            import random
            score = random.uniform(0.0, 1.0)
            label = 'FAKE' if score > THRESHOLD else 'REAL'
            return jsonify({
                'label':      label,
                'confidence': round((score if label == 'FAKE' else 1 - score) * 100, 2),
                'fake_prob':  round(score * 100, 2),
                'real_prob':  round((1 - score) * 100, 2),
                'demo_mode':  True,
            })

        # ── 5. Predict ────────────────────────────────────────────────────────
        fake_prob  = predict_image_bytes(image_bytes)
        real_prob  = 1.0 - fake_prob
        label      = 'FAKE' if fake_prob >= THRESHOLD else 'REAL'
        confidence = fake_prob if label == 'FAKE' else real_prob

        return jsonify({
            'label':      label,
            'confidence': round(confidence * 100, 2),
            'fake_prob':  round(fake_prob  * 100, 2),
            'real_prob':  round(real_prob  * 100, 2),
            'demo_mode':  False,
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500
