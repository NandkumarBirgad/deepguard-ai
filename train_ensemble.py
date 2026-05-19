# train_ensemble.py — DeepGuard AI v2.0 Fine-Tuning Script
#
# Usage:
#   python train_ensemble.py --model xception --data_dir dataset/ --epochs 10
#   python train_ensemble.py --model efficientnet --data_dir dataset/ --epochs 10
#   python train_ensemble.py --model resnet --data_dir dataset/ --epochs 10
#
# Expected dataset directory structure:
#   dataset/
#     train/
#       real/   ← real video frames / images
#       fake/   ← AI-generated frames (Instagram reels, YouTube shorts, face-swaps, etc.)
#     val/
#       real/
#       fake/

import os
import argparse
import numpy as np

# --- Monkey-patch for Python 3.13 / h5py / platform.py WMI bug ---
import platform
_original_wmi_query = getattr(platform, '_wmi_query', None)
def _mock_wmi_query(table, *keys):
    if table == 'OS':
        data = {'Version': '10.0.19045', 'ProductType': '1', 'BuildType': 'Multiprocessor Free', 'ServicePackMajorVersion': '0', 'ServicePackMinorVersion': '0'}
    elif table == 'CPU':
        data = {'Manufacturer': 'AuthenticAMD', 'Caption': 'AMD64 Family 23'}
    else:
        data = {}
    
    if data:
        return tuple(data.get(k, '0') for k in keys)
    if _original_wmi_query:
        try:
            return _original_wmi_query(table, *keys)
        except OSError:
            pass
    raise OSError("not supported")
platform._wmi_query = _mock_wmi_query
# -----------------------------------------------------------------

import tensorflow as tf
from tensorflow.keras import layers, optimizers, callbacks
from tensorflow.keras.applications import Xception, EfficientNetB4, ResNet50
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.utils.class_weight import compute_class_weight

# ─── CONSTANTS ───────────────────────────────────────
XCEPTION_SIZE    = (299, 299)
EFFNET_SIZE      = (224, 224)
RESNET_SIZE      = (224, 224)

MODEL_SAVE_PATHS = {
    "xception":    "models/xception_image_model.keras",
    "efficientnet":"models/efficientnet_model.keras",
    "resnet":      "models/resnet50_model.keras",
}

# ─── AUGMENTATION (social-media-aware) ───────────────
def get_datagen(model_name):
    """
    Strong augmentations to improve robustness on:
    - Compressed / low-quality social media uploads
    - Resized / cropped Instagram / YouTube frames
    - Face-swap and lip-sync artefacts
    """
    return ImageDataGenerator(
        rescale=1./255,
        rotation_range=12,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.08,
        zoom_range=0.15,
        horizontal_flip=True,
        brightness_range=[0.75, 1.25],
        channel_shift_range=25.0,
        fill_mode='nearest',
        # JPEG-quality simulation via random noise
        preprocessing_function=lambda x: x + np.random.normal(0, 0.01, x.shape),
    )

def get_val_datagen():
    return ImageDataGenerator(rescale=1./255)

# ─── MODEL BUILDERS ──────────────────────────────────
def build_xception(num_classes=1):
    base = Xception(weights='imagenet', include_top=False,
                    input_shape=(*XCEPTION_SIZE, 3))
    # Unfreeze last 30 layers for fine-tuning
    for layer in base.layers[:-30]:
        layer.trainable = False
    for layer in base.layers[-30:]:
        layer.trainable = True

    x = base.output
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    out = layers.Dense(num_classes, activation='sigmoid')(x)
    return tf.keras.Model(base.input, out)

def build_efficientnet(num_classes=1):
    base = EfficientNetB4(weights='imagenet', include_top=False,
                          input_shape=(*EFFNET_SIZE, 3))
    for layer in base.layers[:-40]:
        layer.trainable = False
    for layer in base.layers[-40:]:
        layer.trainable = True

    x = base.output
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.45)(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    out = layers.Dense(num_classes, activation='sigmoid')(x)
    return tf.keras.Model(base.input, out)

def build_resnet50(num_classes=1):
    base = ResNet50(weights='imagenet', include_top=False,
                    input_shape=(*RESNET_SIZE, 3))
    for layer in base.layers[:-25]:
        layer.trainable = False
    for layer in base.layers[-25:]:
        layer.trainable = True

    x = base.output
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    out = layers.Dense(num_classes, activation='sigmoid')(x)
    return tf.keras.Model(base.input, out)

MODEL_BUILDERS = {
    "xception":    (build_xception,    XCEPTION_SIZE),
    "efficientnet":(build_efficientnet, EFFNET_SIZE),
    "resnet":      (build_resnet50,    RESNET_SIZE),
}

# ─── TRAINING ────────────────────────────────────────
def train(args):
    model_name = args.model.lower()
    if model_name not in MODEL_BUILDERS:
        raise ValueError(f"Unknown model: {model_name}. Choose from {list(MODEL_BUILDERS)}")

    builder_fn, img_size = MODEL_BUILDERS[model_name]

    train_dir = os.path.join(args.data_dir, "train")
    val_dir   = os.path.join(args.data_dir, "val")

    print(f"\n[INFO] Building {model_name.upper()} model …")
    model = builder_fn()

    # ── Compute class weights to handle imbalanced datasets
    classes = np.array([0, 1])  # 0=fake, 1=real
    cw = compute_class_weight('balanced', classes=classes,
                              y=np.array([0]*500 + [1]*500))   # placeholder
    class_weight = {0: cw[0], 1: cw[1]}
    print(f"[INFO] Class weights: {class_weight}")

    # ── Data generators
    train_gen = get_datagen(model_name).flow_from_directory(
        train_dir, target_size=img_size,
        batch_size=args.batch_size, class_mode='binary', shuffle=True
    )
    val_gen = get_val_datagen().flow_from_directory(
        val_dir, target_size=img_size,
        batch_size=args.batch_size, class_mode='binary', shuffle=False
    )

    # ── Recalculate class weights from actual data
    labels = train_gen.classes
    cw = compute_class_weight('balanced', classes=np.unique(labels), y=labels)
    class_weight = dict(enumerate(cw))
    print(f"[INFO] Recalculated class weights: {class_weight}")

    # ── Callbacks
    save_path  = MODEL_SAVE_PATHS[model_name]
    cbs = [
        callbacks.ModelCheckpoint(
            save_path, monitor='val_accuracy', mode='max',
            save_best_only=True, verbose=1
        ),
        callbacks.EarlyStopping(
            monitor='val_loss', patience=5, restore_best_weights=True, verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.3, patience=3, min_lr=1e-7, verbose=1
        ),
        callbacks.TensorBoard(log_dir=f'logs/{model_name}'),
    ]

    # ── Phase 1: train top layers only (warm-up)
    print("\n[INFO] Phase 1: Warm-up (top layers only) …")
    for layer in model.layers:
        if hasattr(layer, 'layers'):   # is a base model
            for l in layer.layers:
                l.trainable = False
        else:
            layer.trainable = True

    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3),
        loss='binary_crossentropy',
        metrics=['accuracy',
                 tf.keras.metrics.AUC(name='auc'),
                 tf.keras.metrics.Precision(name='precision'),
                 tf.keras.metrics.Recall(name='recall')]
    )
    model.fit(train_gen, validation_data=val_gen, epochs=5,
              class_weight=class_weight, callbacks=cbs[:2])

    # ── Phase 2: fine-tune with unfrozen top layers
    print("\n[INFO] Phase 2: Fine-tuning …")
    for layer in model.layers:
        layer.trainable = True

    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-5),
        loss='binary_crossentropy',
        metrics=['accuracy',
                 tf.keras.metrics.AUC(name='auc'),
                 tf.keras.metrics.Precision(name='precision'),
                 tf.keras.metrics.Recall(name='recall')]
    )
    model.fit(train_gen, validation_data=val_gen,
              epochs=args.epochs, class_weight=class_weight, callbacks=cbs)

    print(f"\n[✓] Model saved to: {save_path}")

    # ── Evaluate
    print("\n[INFO] Final evaluation …")
    results = model.evaluate(val_gen, verbose=1)
    for metric, val in zip(model.metrics_names, results):
        print(f"  {metric}: {val:.4f}")

# ─── MAIN ────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeepGuard AI v2.0 — Train ensemble models")
    parser.add_argument("--model",      type=str, default="xception",
                        choices=["xception","efficientnet","resnet"],
                        help="Which model to train/fine-tune")
    parser.add_argument("--data_dir",   type=str, default="dataset",
                        help="Root dataset directory (must have train/ and val/ subdirs)")
    parser.add_argument("--epochs",     type=int, default=15,
                        help="Number of fine-tuning epochs")
    parser.add_argument("--batch_size", type=int, default=16,
                        help="Batch size for training")
    args = parser.parse_args()
    train(args)
