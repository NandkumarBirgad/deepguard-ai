# app.py — DeepGuard AI v2.0

import os
import traceback
import requests as http_requests  # for Sightengine API calls
from flask import Flask, request, render_template, send_from_directory, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image

# Load environment variables from .env if present
if os.path.exists(".env"):
    with open(".env", "r") as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

import firebase_admin
from firebase_admin import credentials, auth


# ─────────────────── CONFIG ───────────────────
UPLOAD_FOLDER      = "uploads"
FALSE_PRED_DIR     = "false_predictions"
ALLOWED_IMAGE_EXT  = {"png", "jpg", "jpeg", "webp"}
ALLOWED_VIDEO_EXT  = {"mp4", "avi", "mov", "mkv", "webm"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXT | ALLOWED_VIDEO_EXT


app = Flask(__name__)
CORS(app)
app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024   # 500 MB
app.secret_key = os.environ.get("SECRET_KEY", "deepguard-secret-v2")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FALSE_PRED_DIR, exist_ok=True)

# ─────────────────── FIREBASE ───────────────────
try:
    firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS", "")
    if firebase_creds_json:
        # Cloud deployment: credentials passed as JSON string env var
        import json
        cred_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Local development: load from file
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    print("[INFO] Firebase initialised")
except Exception as e:
    print(f"[WARN] Firebase init failed: {e}")

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/project-graph")
def project_graph():
    return render_template("project_graph.html")


# ─────────────────── SIGHTENGINE AI-IMAGE DETECTION ───────────────────
# Sightengine API credentials
SIGHTENGINE_API_USER   = os.environ.get("SIGHTENGINE_API_USER", "")
SIGHTENGINE_API_SECRET = os.environ.get("SIGHTENGINE_API_SECRET", "")
SIGHTENGINE_API_URL    = "https://api.sightengine.com/1.0/check.json"

# Allowed image extensions for this feature
AI_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "bmp"}

# Static uploads folder (served via /static/uploads/)
STATIC_UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(STATIC_UPLOAD_FOLDER, exist_ok=True)


def call_sightengine(filepath):
    """
    Send the image at `filepath` to Sightengine's genai model.
    Returns the parsed JSON response dict, or raises on failure.
    """
    with open(filepath, "rb") as img_file:
        response = http_requests.post(
            SIGHTENGINE_API_URL,
            files={"media": img_file},
            data={
                "models":     "genai",          # AI-generated image model
                "api_user":   SIGHTENGINE_API_USER,
                "api_secret": SIGHTENGINE_API_SECRET,
            },
            timeout=30,  # seconds
        )
    response.raise_for_status()   # raises HTTPError for 4xx/5xx
    return response.json()


@app.route("/detect-ai", methods=["GET", "POST"])
def detect_ai_image():
    """
    Homepage + handler for the Sightengine AI-generated image detector.
    GET  → render upload form
    POST → validate file → call Sightengine API → show result
    """
    if request.method == "GET":
        return render_template("detect_ai.html")

    # ── Validate uploaded file ──
    if "image" not in request.files:
        return render_template(
            "detect_ai.html",
            error="No file received. Please choose an image to upload."
        )

    file = request.files["image"]

    if not file or file.filename == "":
        return render_template(
            "detect_ai.html",
            error="No file selected. Please choose an image file."
        )

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in AI_IMAGE_EXTENSIONS:
        return render_template(
            "detect_ai.html",
            error=f"Unsupported file type '.{ext}'. Please upload a PNG, JPG, JPEG, WEBP, GIF, or BMP image."
        )

    # ── Save to static/uploads so we can display it ──
    filename = secure_filename(file.filename)
    save_path = os.path.join(STATIC_UPLOAD_FOLDER, filename)
    file.save(save_path)

    # ── Call Sightengine API ──
    try:
        api_data = call_sightengine(save_path)
    except http_requests.exceptions.Timeout:
        return render_template(
            "detect_ai.html",
            error="The Sightengine API timed out. Please try again."
        )
    except http_requests.exceptions.HTTPError as exc:
        return render_template(
            "detect_ai.html",
            error=f"Sightengine API returned an error: {exc}"
        )
    except Exception as exc:
        return render_template(
            "detect_ai.html",
            error=f"Unexpected error while contacting the API: {exc}"
        )

    # ── Check for API-level errors ──
    if api_data.get("status") != "success":
        err_msg = api_data.get("error", {}).get("message", "Unknown API error")
        return render_template(
            "detect_ai.html",
            error=f"Sightengine API error: {err_msg}"
        )

    # ── Extract ai_generated score ──
    # Sightengine returns {"type": {"ai_generated": 0.xx}} under genai model
    type_info   = api_data.get("type", {})
    ai_score    = type_info.get("ai_generated", None)

    if ai_score is None:
        return render_template(
            "detect_ai.html",
            error="The API response did not contain an AI-generated probability score. "
                  "This may happen for unsupported image content."
        )

    # ── Classify result ──
    THRESHOLD     = 0.7
    score_pct     = round(ai_score * 100, 2)         # e.g. 85.3
    is_ai         = ai_score > THRESHOLD
    verdict       = "AI Generated Image" if is_ai else "Real Image"
    confidence    = score_pct if is_ai else round((1 - ai_score) * 100, 2)

    return render_template(
        "detect_ai.html",
        # uploaded image URL (served from /static/uploads/)
        image_url  = f"/static/uploads/{filename}",
        filename   = filename,
        # result fields
        verdict    = verdict,
        is_ai      = is_ai,
        ai_score   = score_pct,          # raw AI probability %
        confidence = confidence,          # confidence in the verdict %
        threshold  = int(THRESHOLD * 100),
        # raw API payload for debugging (hidden in UI)
        raw_api    = api_data,
    )


# ─────────────────── HUGGING FACE AI-VIDEO DETECTION ───────────────────
# Allowed video extensions
AI_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "flv"}
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")
HF_VIDEO_MODEL = "umm-maybe/AI-image-detector"  # Best for detecting general AI-generated content (Midjourney, Sora, etc.)
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_VIDEO_MODEL}"


def call_huggingface_video(filepath):
    """
    Since Hugging Face free Inference API does not support raw video deepfake models directly,
    we extract 3 frames from the video (at 25%, 50%, and 75%) and send them to an AI image detector.
    """
    import cv2
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        raise Exception("Could not open video file to extract frame")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_indices = [
        max(0, int(total_frames * 0.25)),
        max(0, int(total_frames * 0.50)),
        max(0, int(total_frames * 0.75))
    ]
    
    extracted_frames = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            extracted_frames.append(frame)
    cap.release()
    
    if not extracted_frames:
        raise Exception("Failed to read frames from video")
        
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "image/jpeg"
    }
    
    all_responses = []
    # Send all 3 frames and collect responses
    for frame in extracted_frames:
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        data = buffer.tobytes()
        response = http_requests.post(
            HF_API_URL,
            headers=headers,
            data=data,
            timeout=60,
        )
        
        if response.status_code == 200:
            all_responses.append(response.json())
        else:
            # If rate limited or model loading on a frame, just ignore and continue
            pass
            
    if not all_responses:
        raise Exception("Hugging Face API failed on all extracted frames.")
        
    return all_responses


@app.route("/detect-ai-video", methods=["GET", "POST"])
def detect_ai_video():
    """
    Upload form + handler for the Hugging Face AI-generated video detector.
    GET  → render upload form
    POST → validate → call Hugging Face API → show result
    """
    if request.method == "GET":
        return render_template("detect_ai_video.html")

    # ── Validate uploaded file ──
    if "video" not in request.files:
        return render_template(
            "detect_ai_video.html",
            error="No file received. Please choose a video to upload."
        )

    file = request.files["video"]

    if not file or file.filename == "":
        return render_template(
            "detect_ai_video.html",
            error="No file selected. Please choose a video file."
        )

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in AI_VIDEO_EXTENSIONS:
        return render_template(
            "detect_ai_video.html",
            error=f"Unsupported file type '.{ext}'. Please upload an MP4, MOV, AVI, MKV, WEBM, or FLV video."
        )

    # ── Save to static/uploads ──
    filename  = secure_filename(file.filename)
    save_path = os.path.join(STATIC_UPLOAD_FOLDER, filename)
    file.save(save_path)

    # ── Call Hugging Face API ──
    try:
        api_data = call_huggingface_video(save_path)
    except http_requests.exceptions.Timeout:
        return render_template(
            "detect_ai_video.html",
            error="The Hugging Face API timed out. Try a shorter/smaller video."
        )
    except http_requests.exceptions.HTTPError as exc:
        return render_template(
            "detect_ai_video.html",
            error=f"Hugging Face API HTTP error: {exc}"
        )
    except Exception as exc:
        return render_template(
            "detect_ai_video.html",
            error=f"Unexpected error while contacting the API: {exc}"
        )

    # ── API-level error check ──
    if isinstance(api_data, dict) and "error" in api_data:
        err_msg = api_data.get("error", "Unknown API error")
        return render_template(
            "detect_ai_video.html",
            error=f"Hugging Face API error: {err_msg}. The model might be loading, please wait and try again."
        )

    # ── Extract ai_generated score ──
    ai_score = None
    if isinstance(api_data, list):
        # Flatten responses if multiple frames were analyzed: [[{"label":"artificial", "score":0.9}]]
        items_to_check = api_data
        if len(api_data) > 0 and isinstance(api_data[0], list):
            items_to_check = [item for sublist in api_data for item in sublist]
            
        fake_scores = []
        found_label = False
        for item in items_to_check:
            label = str(item.get("label", "")).upper()
            if "FAKE" in label or "LABEL_1" in label or "ARTIFICIAL" in label:
                fake_scores.append(item.get("score", 0.0))
                found_label = True
        
        if found_label and fake_scores:
            ai_score = max(fake_scores)  # Use the maximum AI score detected in any frame
        elif len(items_to_check) > 0:
            # Fallback
            ai_score = items_to_check[0].get("score", 0.5)

    if ai_score is None:
        return render_template(
            "detect_ai_video.html",
            error="The API response did not contain a recognizable probability score. "
                  "Try a different video format or check the model status."
        )

    # ── Classify result ──
    THRESHOLD  = 0.7
    score_pct  = round(ai_score * 100, 2)
    is_ai      = ai_score > THRESHOLD
    verdict    = "AI Generated Video" if is_ai else "Real Video"
    confidence = score_pct if is_ai else round((1 - ai_score) * 100, 2)

    return render_template(
        "detect_ai_video.html",
        video_url  = f"/static/uploads/{filename}",
        filename   = filename,
        verdict    = verdict,
        is_ai      = is_ai,
        ai_score   = score_pct,
        confidence = confidence,
        threshold  = int(THRESHOLD * 100),
        raw_api    = api_data,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

