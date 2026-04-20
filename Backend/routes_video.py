from flask import Blueprint, request, jsonify
import numpy as np
import cv2
import os
import tempfile

video_bp = Blueprint('video', __name__)


@video_bp.route('/api/detect/video', methods=['POST'])
def detect_video():
    try:
        # ── 1. Validate file ──────────────────────────────────────────────────
        if 'video' not in request.files:
            return jsonify({'error': 'No video provided'}), 400
        file = request.files['video']
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400

        # ── 2. Import shared utils from app ───────────────────────────────────
        from Backend.app import predict_image_bytes, frame_to_bytes, frame_to_base64, model, VIDEO_THRESHOLD, FRAME_STEP, MAX_FRAMES

        # ── 3. Save to temp file ──────────────────────────────────────────────
        suffix = os.path.splitext(file.filename)[1] or '.mp4'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                return jsonify({'error': 'Could not open video file'}), 400

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps          = cap.get(cv2.CAP_PROP_FPS) or 30
            duration_sec = round(total_frames / fps, 1)

            frame_results = []
            frame_idx     = 0
            analysed      = 0

            # ── 4. Extract and analyse frames ─────────────────────────────────
            while cap.isOpened() and analysed < MAX_FRAMES:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % FRAME_STEP == 0:
                    if model is not None:
                        # video prediction is inverted vs image
                        fake_prob = 1.0-predict_image_bytes(frame_to_bytes(frame))
                    else:
                        import random
                        fake_prob = random.uniform(0.0, 1.0)

                    frame_results.append({
                        'frame_idx': frame_idx,
                        'timestamp': round(frame_idx / fps, 2),
                        'fake_prob': fake_prob,
                        'frame':     frame,
                    })
                    analysed += 1

                frame_idx += 1

            cap.release()

        finally:
            os.unlink(tmp_path)

        if not frame_results:
            return jsonify({'error': 'No frames could be extracted'}), 400

        # ── 5. Overall verdict ────────────────────────────────────────────────
        avg_fake_prob = float(np.mean([r['fake_prob'] for r in frame_results]))
        avg_real_prob = 1.0 - avg_fake_prob
        label         = 'FAKE' if avg_fake_prob >= VIDEO_THRESHOLD else 'REAL'
        confidence    = avg_fake_prob if label == 'FAKE' else avg_real_prob

        return jsonify({
            'label':           label,
            'confidence':      round(confidence    * 100, 2),
            'fake_prob':       round(avg_fake_prob * 100, 2),
            'real_prob':       round(avg_real_prob * 100, 2),
            'frames_analysed': analysed,
            'duration_sec':    duration_sec,
            'demo_mode':       model is None,
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'error': str(e)}), 500
