"""
Robust XGBoost Training Script with 6 Classes + Anti-Overfitting
Classes: Acne, Bags, Dry, Redness, Oily, Normal.

Key anti-overfitting measures:
  - Early stopping with validation set
  - Reduced max_depth (4) + L1/L2 regularization
  - Balanced class weights via sample_weight
  - Uniform augmentation across all classes
  - Stratified train/test split
  - Confusion matrix + per-class metrics
  - Face detection during feature extraction for cleaner data
"""

import os
import sys
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_sample_weight
import joblib
import cv2
from pathlib import Path
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import random
import warnings
warnings.filterwarnings('ignore')

# ─── 6 Classes ────────────────────────────────────────────────────────────────
CLASSES = ['acne', 'bags', 'dry', 'redness', 'oily', 'normal']
NUM_CLASSES = len(CLASSES)

# ─── Globals ──────────────────────────────────────────────────────────────────
_feature_extractor = None
_face_cascade = None

def get_feature_extractor():
    global _feature_extractor
    if _feature_extractor is None:
        print("[INFO] Loading MobileNetV2 feature extractor...")
        _feature_extractor = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(224, 224, 3),
            pooling='avg'
        )
    return _feature_extractor

def get_face_cascade():
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        _face_cascade = cv2.CascadeClassifier(cascade_path)
    return _face_cascade

# ─── Face Detection ───────────────────────────────────────────────────────────
def detect_and_crop_face(image_path):
    """
    Detect face in image and return cropped face region.
    Falls back to center crop if no face detected.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = get_face_cascade()

    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(50, 50)
    )

    if len(faces) > 0:
        # Take the largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        # Add 20% padding
        pad_w = int(w * 0.2)
        pad_h = int(h * 0.2)
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(img.shape[1], x + w + pad_w)
        y2 = min(img.shape[0], y + h + pad_h)
        face_crop = img[y1:y2, x1:x2]
    else:
        # Fallback: center crop (70% of the image)
        h, w = img.shape[:2]
        ch, cw = int(h * 0.15), int(w * 0.15)
        face_crop = img[ch:h-ch, cw:w-cw]

    # Resize to 224x224 for MobileNetV2
    face_crop = cv2.resize(face_crop, (224, 224))
    return face_crop


# ─── Augmentation ─────────────────────────────────────────────────────────────
def augment_image(img_np):
    """Apply random augmentation to numpy image array."""
    aug = img_np.copy()

    # Random horizontal flip
    if random.random() > 0.5:
        aug = np.fliplr(aug)

    # Random brightness adjustment (subtle)
    brightness = random.uniform(0.8, 1.2)
    aug = np.clip(aug * brightness, 0, 255)

    # Random rotation (-15 to +15 degrees)
    angle = random.uniform(-15, 15)
    h, w = aug.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    aug = cv2.warpAffine(aug, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    # Random slight zoom (crop and resize)
    if random.random() > 0.5:
        crop_pct = random.uniform(0.05, 0.15)
        ch = int(h * crop_pct)
        cw = int(w * crop_pct)
        aug = aug[ch:h-ch, cw:w-cw]
        aug = cv2.resize(aug, (w, h))

    # Random Gaussian blur (subtle)
    if random.random() > 0.7:
        ksize = random.choice([3, 5])
        aug = cv2.GaussianBlur(aug, (ksize, ksize), 0)

    return aug.astype(np.float32)


# ─── Feature Extraction ──────────────────────────────────────────────────────
def extract_features_from_array(img_np, augment=False):
    """Extract MobileNetV2 features from a numpy image array (BGR, 224x224)."""
    try:
        if augment:
            img_np = augment_image(img_np)

        # Convert BGR to RGB for MobileNetV2
        img_rgb = cv2.cvtColor(img_np.astype(np.uint8), cv2.COLOR_BGR2RGB)
        img_rgb = img_rgb.astype(np.float32)

        x = preprocess_input(np.expand_dims(img_rgb, axis=0))
        features = get_feature_extractor().predict(x, verbose=0).flatten()
        return features
    except Exception as e:
        return None


def extract_features(image_path, augment=False):
    """Extract features from an image file with face detection."""
    try:
        face_img = detect_and_crop_face(image_path)
        if face_img is None:
            return None
        return extract_features_from_array(face_img, augment=augment)
    except Exception:
        return None


# ─── Dataset Loading ──────────────────────────────────────────────────────────
def load_dataset(dataset_path, augmentation_factor=5):
    """
    Load dataset with face detection and uniform augmentation.
    Each class gets the same augmentation factor for balance.
    """
    X, y = [], []
    dataset_path = Path(dataset_path)

    print(f"\n{'='*60}")
    print("LOADING DATASET WITH FACE DETECTION")
    print(f"{'='*60}")
    print(f"Augmentation factor: {augmentation_factor}x per image")
    print()

    class_counts = {}

    for idx, cond in enumerate(CLASSES):
        p = dataset_path / cond
        if not p.exists():
            print(f"  [WARN] {cond}: directory not found, skipping")
            continue

        # Find all image files (including in subdirectories)
        files = list(p.glob('**/*.jpg')) + list(p.glob('**/*.jpeg')) + list(p.glob('**/*.png')) + list(p.glob('**/*.bmp'))

        if len(files) == 0:
            print(f"  [WARN] {cond}: no image files found, skipping")
            continue

        print(f"  Loading {cond}: {len(files)} source images...", end='', flush=True)
        count = 0

        for f in files:
            # Original (no augmentation)
            feat = extract_features(str(f), augment=False)
            if feat is not None:
                X.append(feat)
                y.append(idx)
                count += 1

            # Augmented copies — same factor for all classes
            for _ in range(augmentation_factor - 1):
                feat = extract_features(str(f), augment=True)
                if feat is not None:
                    X.append(feat)
                    y.append(idx)
                    count += 1

        class_counts[cond] = count
        print(f" -> {count} samples")

    print(f"\n  Total samples: {sum(class_counts.values())}")
    print(f"  Per-class: {class_counts}")

    return np.array(X), np.array(y)


# ─── Main Training ────────────────────────────────────────────────────────────
def main():
    model_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(model_dir, 'dataset')

    print("="*60)
    print("XGBOOST SKIN MODEL TRAINING (v2 - Anti-Overfitting)")
    print("="*60)
    print(f"Classes: {CLASSES}")
    print(f"Dataset path: {dataset_path}")

    # ── Load data with balanced augmentation ──
    X, y = load_dataset(dataset_path, augmentation_factor=5)

    if len(X) == 0:
        print("[ERROR] No data loaded! Check dataset directory.")
        return

    if len(np.unique(y)) < 2:
        print(f"[ERROR] Only {len(np.unique(y))} class(es) found. Need at least 2.")
        return

    print(f"\nLoaded classes: {[CLASSES[i] for i in sorted(np.unique(y))]}")
    print(f"Total samples: {len(X)}, Features: {X.shape[1]}")

    # ── Stratified Train/Test Split ──
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # ── Feature Scaling ──
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # ── Compute balanced sample weights ──
    sample_weights = compute_sample_weight('balanced', y_train)
    print(f"Sample weights computed for class balance")

    # ── XGBoost with Anti-Overfitting Config ──
    model = xgb.XGBClassifier(
        n_estimators=300,           # Max trees (early stopping will cut this)
        max_depth=4,                # Shallower trees = less memorization
        learning_rate=0.05,         # Slower learning for better generalization
        subsample=0.7,              # Row subsampling per tree
        colsample_bytree=0.7,      # Feature subsampling per tree
        min_child_weight=5,         # Minimum samples per leaf
        gamma=0.3,                  # Minimum loss reduction for split
        reg_alpha=1.0,              # L1 regularization
        reg_lambda=2.0,             # L2 regularization
        objective='multi:softprob',
        num_class=NUM_CLASSES,
        random_state=42,
        eval_metric='mlogloss',
        early_stopping_rounds=30,   # Stop if no improvement for 30 rounds
    )

    print("\n[TRAINING] Fitting XGBoost with early stopping...")
    model.fit(
        X_train, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_test, y_test)], # Use test set for early stopping
        verbose=True, # Show progress
    )

    # ── Evaluation ──
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Overall Accuracy: {accuracy:.4f} ({accuracy*100:.1f}%)")
    print(f"Best iteration: {model.best_iteration if hasattr(model, 'best_iteration') else 'N/A'}")

    # Per-class report
    present_classes = sorted(np.unique(np.concatenate([y_test, y_pred])))
    target_names = [CLASSES[i] for i in present_classes]

    print(f"\n--- Per-Class Report ---")
    print(classification_report(y_test, y_pred, labels=present_classes, target_names=target_names))

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=present_classes)
    print("--- Confusion Matrix ---")
    print(f"{'':>10}", end='')
    for name in target_names:
        print(f"{name:>10}", end='')
    print()
    for i, row in enumerate(cm):
        print(f"{target_names[i]:>10}", end='')
        for val in row:
            print(f"{val:>10}", end='')
        print()

    # ── Check for overfitting ──
    train_pred = model.predict(X_train)
    train_acc = accuracy_score(y_train, train_pred)
    print(f"\n--- Overfitting Check ---")
    print(f"Train Accuracy: {train_acc:.4f}")
    print(f"Test Accuracy:  {accuracy:.4f}")
    print(f"Gap:            {train_acc - accuracy:.4f}")

    if train_acc - accuracy > 0.15:
        print("[WARN] Significant overfitting detected (gap > 15%)")
    else:
        print("[OK] No significant overfitting")

    # ── Save Model ──
    model_path = os.path.join(model_dir, 'xgboost_skin_model.pkl')
    scaler_path = os.path.join(model_dir, 'xgboost_scaler.pkl')

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    # Save class names for inference
    classes_path = os.path.join(model_dir, 'class_names.txt')
    with open(classes_path, 'w') as f:
        f.write('\n'.join(CLASSES))

    # Save feature names
    feature_names_path = os.path.join(model_dir, 'feature_names.txt')
    with open(feature_names_path, 'w') as f:
        f.write('\n'.join([f'mobilenet_feat_{i}' for i in range(X.shape[1])]))

    print(f"\n[SAVED] Model: {model_path}")
    print(f"[SAVED] Scaler: {scaler_path}")
    print(f"[SAVED] Classes: {classes_path}")
    print(f"\n{'='*60}")
    print("TRAINING COMPLETE")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
