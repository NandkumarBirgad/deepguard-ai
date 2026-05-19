# DeepGuard AI v2.0 — Deepfake Detection System

> **Upgraded to detect modern AI-generated Instagram Reels, YouTube Shorts, face-swap videos, lip-sync clips, and text-to-video content.**

---

## 🆕 What's New in v2.0

| Feature | v1.0 | v2.0 |
|---|---|---|
| Models | Xception only | **Xception + EfficientNet + ResNet50 Ensemble** |
| Labels | Real / Fake | **Real / Fake / Suspicious** |
| Video analysis | Frame average | **Frame-by-frame + Temporal Consistency** |
| Social media support | Basic | **Optimised for Instagram & YouTube compression** |
| Confidence display | Percentage | **Percentage + Risk Level + Progress Bar** |
| Suspicious frames | ❌ | **✅ Highlighted with bbox** |
| Analytics dashboard | ❌ | **✅ Frame distribution, variance, fake ratio** |
| False prediction logging | ❌ | **✅ Saved to false_predictions/false_predictions.jsonl** |
| Auto-threshold | Fixed 0.5 | **Tunable REAL=0.62 / FAKE=0.38** |
| Face detection | MTCNN | **MTCNN + social-media augmentation fallback** |

---

## 🏗️ Architecture

```
DeepGuard AI v2.0
├── app.py                    ← Flask backend (upgraded)
├── utils.py                  ← Ensemble engine, temporal analysis, social-media preprocessing
├── train_ensemble.py         ← Fine-tuning script (Xception, EfficientNet, ResNet50)
├── models/
│   ├── xception_image_model.keras     ← Primary model (existing)
│   ├── xception_video_model.keras     ← Video model (existing)
│   ├── efficientnet_model.keras       ← New (train with train_ensemble.py)
│   └── resnet50_model.keras           ← New (train with train_ensemble.py)
├── templates/
│   ├── index.html
│   ├── result_image.html     ← Upgraded with analytics card
│   ├── result_video.html     ← Upgraded with frame charts & suspicious highlights
│   ├── login.html
│   └── signup.html
├── false_predictions/
│   └── false_predictions.jsonl   ← Auto-logged for retraining
└── uploads/
```

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
# → Open http://localhost:5000
```

---

## 🧠 Training New Ensemble Models

### Step 1 — Prepare Your Dataset
```
dataset/
  train/
    real/    ← Real video frames (person talking, selfies, etc.)
    fake/    ← AI-generated frames from:
               - Instagram Reels AI filters
               - YouTube Shorts deepfakes
               - Face-swap (DeepFaceLab, Reface, etc.)
               - Lip-sync (wav2lip, etc.)
               - Text-to-video (Sora, Runway, Pika, etc.)
  val/
    real/
    fake/
```

### Step 2 — Fine-Tune Xception (primary)
```bash
python train_ensemble.py --model xception --data_dir dataset/ --epochs 15
```

### Step 3 — Train EfficientNet
```bash
python train_ensemble.py --model efficientnet --data_dir dataset/ --epochs 15
```

### Step 4 — Train ResNet50
```bash
python train_ensemble.py --model resnet --data_dir dataset/ --epochs 15
```

### Recommended Public Datasets
| Dataset | Content |
|---|---|
| [FaceForensics++](https://github.com/ondyari/FaceForensics) | Face-swap, face reenactment |
| [Celeb-DF v2](https://github.com/yuezunli/celeb-deepfakeforensics) | Celebrity deepfakes |
| [DFDC (Facebook)](https://ai.facebook.com/datasets/dfdc/) | Large-scale deepfakes |
| [WildDeepfake](https://github.com/deepfakeinthewild/deepfake-in-the-wild) | In-the-wild social media |
| [DGM4](https://github.com/CHELSEA234/M2TR) | Multi-modal generated media |

---

## ⚙️ Threshold Tuning

Edit `utils.py`:
```python
REAL_THRESHOLD  = 0.62   # above this → REAL
FAKE_THRESHOLD  = 0.38   # below this → FAKE
                          # between   → SUSPICIOUS
```

Tune based on your false-positive / false-negative tolerance.

---

## 🔖 Result Labels

| Label | Meaning | Risk |
|---|---|---|
| 🟢 **REAL** | Genuine content — confidence above threshold | Low |
| 🔴 **FAKE** | AI-generated — deepfake, face-swap, text-to-video | High / Medium |
| 🟡 **SUSPICIOUS** | Borderline — may be manipulated or heavily compressed | Medium |

---

## 🔁 False Prediction Feedback

Users can click **"Report Incorrect Prediction"** in the result page.  
Records are saved to `false_predictions/false_predictions.jsonl` for retraining.

```jsonl
{"id":"...", "timestamp":"...", "filepath":"...", "predicted_label":"REAL", "user_corrected_label":"fake", "confidence":61.4}
```

Use this file as additional hard-negative/positive samples during your next training run.

---

## 📊 API Endpoints

| Method | Route | Description |
|---|---|---|
| GET/POST | `/` | Main web UI |
| POST | `/upload` | API prediction (Firebase auth required) |
| POST | `/report-false` | Log a false prediction |
| GET | `/analytics` | Analytics summary JSON |
| GET | `/uploads/<filename>` | Serve uploaded files |
| GET | `/login` | Login page |
| GET | `/signup` | Signup page |
