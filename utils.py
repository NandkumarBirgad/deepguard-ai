# utils.py

import os
import numpy as np
import cv2
from PIL import Image
import tensorflow as tf
from keras.applications.xception import preprocess_input

IMAGE_SIZE = (299, 299)
DEFAULT_FRAME_SKIP = 10

# --------- LOAD MODEL ---------
def load_xception_model(model_path):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = tf.keras.models.load_model(model_path, compile=False)

    # FIXED CLASS ORDER (matches inference logic)
    classes = ["fake", "real"]
    return model, classes, "cpu"


# --------- IMAGE PREDICTION ---------
def preprocess_image_pil(image_pil):
    image = image_pil.resize(IMAGE_SIZE)
    image = np.array(image)
    image = preprocess_input(image)
    return np.expand_dims(image, 0)


def predict_image_xception(model, classes, image_pil):
    tensor = preprocess_image_pil(image_pil)
    prob = float(model.predict(tensor, verbose=0)[0][0])  # sigmoid output = REAL score

    real_prob = prob
    fake_prob = 1 - prob

    label = classes[1] if real_prob > fake_prob else classes[0]
    confidence = max(real_prob, fake_prob)

    return label, confidence, np.array([fake_prob, real_prob])


# --------- VIDEO PROCESSING ---------
def extract_frames(video_path, max_frames=50, frame_skip=10):
    """
    Extract frames from a video.
    - video_path: path to video
    - max_frames: max frames to extract
    - frame_skip: sample every `frame_skip` frames
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    count = 0

    while len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if count % frame_skip == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (299, 299))  # Xception input size
            frames.append(frame)

        count += 1

    cap.release()
    return np.array(frames)

def predict_video_xception(model, classes, video_path, max_frames=50, frame_skip=10):
    """
    Predict whether a video is 'real' or 'fake' using Xception model.
    Returns:
    - final_label: video-level label
    - confidence: video-level confidence
    - frame_results: list of dicts per frame with 'label' and 'confidence'
    """
    frames = extract_frames(video_path, max_frames, frame_skip)
    if len(frames) == 0:
        return None, None, []

    # Preprocess frames
    frames_preprocessed = preprocess_input(frames.astype(np.float32))

    # Predict frame probabilities
    preds = model.predict(frames_preprocessed, verbose=0).flatten()

    frame_results = []
    for p in preds:
        real_prob = float(p)           # probability of 'real'
        fake_prob = 1 - real_prob      # probability of 'fake'
        label = classes[1] if real_prob > fake_prob else classes[0]
        confidence = max(real_prob, fake_prob)

        frame_results.append({
            "label": label,
            "confidence": confidence
        })

    # Video-level prediction (average of frame probabilities)
    avg_prob = float(np.mean(preds))
    final_label = classes[1] if avg_prob > 0.5 else classes[0]
    confidence = max(avg_prob, 1 - avg_prob)

    return final_label, confidence, frame_results