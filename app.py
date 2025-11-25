# app.py

import os
from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import tensorflow as tf
from utils import load_xception_model, predict_image_xception, predict_video_xception
import firebase_admin
from firebase_admin import credentials, auth
from tensorflow.keras.metrics import AUC, Precision, Recall
import traceback

# -------------------- CONFIG -------------------- #
UPLOAD_FOLDER = "uploads"
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg"}
ALLOWED_VIDEO_EXT = {"mp4", "avi", "mov", "mkv"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXT.union(ALLOWED_VIDEO_EXT)

IMAGE_MODEL_PATH = "models/xception_image_model.keras"
VIDEO_MODEL_PATH = "models/xception_video_model.keras"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------- FIREBASE -------------------- #
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# -------------------- LOAD MODELS -------------------- #
def safe_load_model(model_path):
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file does not exist: {model_path}")
        return None, ["fake", "real"]

    try:
        model = tf.keras.models.load_model(
            model_path,
            compile=False,
            custom_objects={"AUC": AUC, "Precision": Precision, "Recall": Recall}
        )
        classes = ["fake", "real"]
        print(f"[INFO] Model loaded successfully: {model_path}")
        return model, classes

    except Exception as e:
        print(f"[ERROR] Could not load model {model_path}:")
        print(traceback.format_exc())
        return None, ["fake", "real"]

image_model, image_classes = safe_load_model(IMAGE_MODEL_PATH)
video_model, video_classes = safe_load_model(VIDEO_MODEL_PATH)

# -------------------- HELPERS -------------------- #
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_token(id_token):
    try:
        return auth.verify_id_token(id_token)
    except Exception:
        return None

# -------------------- ROUTES -------------------- #
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "media" not in request.files:
            return render_template("index.html", error="No file uploaded")

        file = request.files["media"]
        if file.filename == "":
            return render_template("index.html", error="Empty file name")
        if not allowed_file(file.filename):
            return render_template("index.html", error="Unsupported file type")

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        ext = filename.rsplit(".", 1)[1].lower()

        # ---------------- IMAGE ---------------- #
        if ext in ALLOWED_IMAGE_EXT:
            if image_model is None:
                return render_template("index.html", error="Image model not loaded")

            pil_img = Image.open(filepath).convert("RGB")
            label, confidence, probs = predict_image_xception(image_model, image_classes, pil_img)
            class_probs = list(zip(image_classes, [float(p) for p in probs]))

            return render_template("result_image.html",
                                   filename=filename,
                                   label=label.upper(),
                                   confidence=round(confidence * 100, 2),
                                   class_probs=class_probs)

        # ---------------- VIDEO ---------------- #
        elif ext in ALLOWED_VIDEO_EXT:
            if video_model is None:
                return render_template("index.html", error="Video model not loaded")

            final_label, confidence, frame_results = predict_video_xception(
                video_model, video_classes, video_path=filepath, max_frames=50, frame_skip=10
            )
            if final_label is None:
                return render_template("index.html", error="Cannot process video")

            # Convert to consistent dict format
            frame_results_dicts = []
            for res in frame_results:
                # res may already be tuple or dict depending on your utils
                if isinstance(res, dict):
                    frame_results_dicts.append({
                        "label": res.get("label", "UNKNOWN"),
                        "confidence": float(res.get("confidence", 0))
                    })
                elif isinstance(res, (list, tuple)) and len(res) == 2:
                    frame_results_dicts.append({
                        "label": res[0],
                        "confidence": float(res[1])
                    })

            indexed_frames = [(i, res) for i, res in enumerate(frame_results_dicts)]

            return render_template("result_video.html",
                                   filename=filename,
                                   label=final_label.upper(),
                                   confidence=round(confidence * 100, 2),
                                   frame_results=indexed_frames)

    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    print("[INFO] Received upload request")

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        return jsonify({"message": "Unauthorized - Invalid or missing token"}), 401

    if "image" not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"message": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"message": "Unsupported file type"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    ext = filename.rsplit(".", 1)[1].lower()

    # ---------------- IMAGE MODEL ---------------- #
    if ext in ALLOWED_IMAGE_EXT:
        if image_model is None:
            return jsonify({"message": "Image model not loaded"}), 500

        pil_img = Image.open(filepath).convert("RGB")
        label, confidence, probs = predict_image_xception(image_model, image_classes, pil_img)

        response = {
            "prediction": "REAL" if label.lower() == "real" else "FAKE",
            "confidence": float(confidence),
            "frame_results": [{"label": label.upper(), "confidence": float(confidence)}],
            "face_count": 1,
            "suspicion_score": round(1 - confidence, 3),
            "risk_level": "low" if confidence > 0.8 else "medium" if confidence > 0.5 else "high",
            "risk_factors": ["Blur", "Lighting Issues"] if confidence < 0.5 else [],
            "quality_metrics": {
                "blur_score": 0.75,
                "brightness": 0.6,
                "contrast": 0.55,
                "edge_density": 0.42
            }
        }
        return jsonify(response), 200

    # ---------------- VIDEO MODEL ---------------- #
    elif ext in ALLOWED_VIDEO_EXT:
        if video_model is None:
            return jsonify({"message": "Video model not loaded"}), 500

        final_label, confidence, frame_results = predict_video_xception(
            video_model, video_classes, filepath, max_frames=50, frame_skip=10
        )

        # Convert frame_results to consistent dicts
        frame_results_dicts = []
        for res in frame_results:
            if isinstance(res, dict):
                frame_results_dicts.append({
                    "label": res.get("label", "UNKNOWN"),
                    "confidence": float(res.get("confidence", 0))
                })
            elif isinstance(res, (list, tuple)) and len(res) == 2:
                frame_results_dicts.append({
                    "label": res[0],
                    "confidence": float(res[1])
                })

        response = {
            "prediction": "REAL" if final_label.lower() == "real" else "FAKE",
            "confidence": float(confidence),
            "frame_results": frame_results_dicts,
            "face_count": len(frame_results_dicts),
            "suspicion_score": round(1 - confidence, 3),
            "risk_level": "low" if confidence > 0.8 else "medium" if confidence > 0.5 else "high",
            "risk_factors": ["Frame inconsistencies", "Blinking anomalies"] if confidence < 0.5 else [],
            "quality_metrics": {
                "blur_score": 0.72,
                "brightness": 0.61,
                "contrast": 0.49,
                "edge_density": 0.38
            }
        }
        return jsonify(response), 200

    return jsonify({"message": "Unsupported extension"}), 400


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
