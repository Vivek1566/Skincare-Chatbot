"""
xgboost_predictor.py -- Skin Condition Predictor v2
Uses MobileNetV2 + XGBoost with face detection.
NO hard-coded bias overrides. Model probabilities are the sole decision.

Classes: Acne, Bags, Dry, Redness, Oily, Normal
"""

import os
import joblib
import numpy as np
import cv2

# Lazy imports for TensorFlow (heavy)
_tf_loaded = False
_MobileNetV2 = None
_preprocess_input = None


def _ensure_tf():
    global _tf_loaded, _MobileNetV2, _preprocess_input
    if not _tf_loaded:
        from tensorflow.keras.applications import MobileNetV2 as _MNV2
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as _pi
        _MobileNetV2 = _MNV2
        _preprocess_input = _pi
        _tf_loaded = True


class XGBoostSkinPredictor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(XGBoostSkinPredictor, cls).__new__(cls)
            cls._instance.is_loaded = False
            cls._instance.model = None
            cls._instance.scaler = None
            cls._instance.feature_extractor = None
            cls._instance.face_cascade = None
            cls._instance.classes = ['Acne', 'Bags', 'Dry', 'Redness', 'Oily', 'Normal']
        return cls._instance

    def _load_model(self):
        if self.is_loaded:
            return True
        try:
            model_dir = os.path.dirname(os.path.abspath(__file__))
            self.model = joblib.load(os.path.join(model_dir, 'xgboost_skin_model.pkl'))
            self.scaler = joblib.load(os.path.join(model_dir, 'xgboost_scaler.pkl'))

            _ensure_tf()
            self.feature_extractor = _MobileNetV2(
                weights='imagenet',
                include_top=False,
                input_shape=(224, 224, 3),
                pooling='avg'
            )

            # Load face cascade for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)

            # Load class names if available
            classes_path = os.path.join(model_dir, 'class_names.txt')
            if os.path.exists(classes_path):
                with open(classes_path, 'r') as f:
                    loaded_classes = [line.strip().title() for line in f.readlines() if line.strip()]
                if len(loaded_classes) == self.model.n_classes_:
                    self.classes = loaded_classes
                    print(f"[OK] Loaded {len(self.classes)} classes: {self.classes}")

            self.is_loaded = True
            print("[OK] Skin predictor engine initialized (v2 — face detection)")
            return True
        except Exception as e:
            print(f"[ERROR] Engine load failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def detect_face(self, img):
        """
        Detect and crop the largest face in the image.
        Returns the cropped face (224x224, BGR) or center-cropped fallback.
        """
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Try multiple scale factors for robustness
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(50, 50)
        )

        if len(faces) == 0:
            # Try more aggressive detection
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,
                minNeighbors=3,
                minSize=(30, 30)
            )

        if len(faces) > 0:
            # Take the largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            # Add 20% padding for context
            pad_w = int(w * 0.2)
            pad_h = int(h * 0.2)
            x1 = max(0, x - pad_w)
            y1 = max(0, y - pad_h)
            x2 = min(img.shape[1], x + w + pad_w)
            y2 = min(img.shape[0], y + h + pad_h)
            face_crop = img[y1:y2, x1:x2]
            face_detected = True
        else:
            # Fallback: center crop 70% of image
            h, w = img.shape[:2]
            ch, cw = int(h * 0.15), int(w * 0.15)
            face_crop = img[ch:h - ch, cw:w - cw]
            face_detected = False

        face_crop = cv2.resize(face_crop, (224, 224))
        return face_crop, face_detected

    def extract_features(self, face_img_bgr):
        """Extract MobileNetV2 features from a BGR face image (224x224)."""
        _ensure_tf()
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(face_img_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
        x = _preprocess_input(np.expand_dims(img_rgb, axis=0))
        features = self.feature_extractor.predict(x, verbose=0)
        return features

    def predict(self, image_path):
        """
        Full prediction pipeline:
        1. Load image
        2. Detect and crop face
        3. Extract MobileNetV2 features
        4. XGBoost classification
        5. Return probabilities (NO hard-coded overrides)
        """
        if not self._load_model():
            return None

        try:
            # 1. Load raw image
            img = cv2.imread(image_path)
            if img is None:
                print(f"[ERROR] Could not load image: {image_path}")
                return None

            # 2. Face detection and cropping
            result = self.detect_face(img)
            if result is None:
                return None
            face_img, face_detected = result

            # 3. Feature extraction from face crop
            features = self.extract_features(face_img)

            # 4. Scale features and predict
            features_scaled = self.scaler.transform(features)
            probs = self.model.predict_proba(features_scaled)[0]

            # 5. Pure model-based decision — NO MANUAL OVERRIDES
            max_idx = np.argmax(probs)
            primary = self.classes[max_idx]
            confidence = float(probs[max_idx])

            # Build probability dict
            prob_dict = {}
            for i, cls in enumerate(self.classes):
                if i < len(probs):
                    prob_dict[cls] = round(float(probs[i]), 4)
                else:
                    prob_dict[cls] = 0.0

            # Get top 4 conditions sorted by probability
            sorted_conditions = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
            top_conditions = [
                {'condition': name, 'confidence': round(confidence, 4), 'percentage': round(confidence * 100, 2)}
                for name, confidence in sorted_conditions[:4]
                if confidence > 0.05  # Only include conditions with >5% confidence
            ]
            
            # Ensure we have at least one condition
            if not top_conditions:
                top_conditions = [{'condition': sorted_conditions[0][0], 'confidence': round(sorted_conditions[0][1], 4), 'percentage': round(sorted_conditions[0][1] * 100, 2)}]

            # Skin Type detection (higher probability among Oily, Normal, Dry)
            skin_type_classes = ['Oily', 'Normal', 'Dry']
            skin_type_probs = {cls: prob_dict.get(cls, 0.0) for cls in skin_type_classes}
            top_skin_type = max(skin_type_probs, key=skin_type_probs.get)
            skin_type_confidence = skin_type_probs[top_skin_type]

            # Detect skin issues (Acne, Bags, Redness) separately from skin type
            issue_classes = ['Acne', 'Bags', 'Redness']
            issue_probs = {cls: prob_dict.get(cls, 0.0) for cls in issue_classes}
            detected_issues = [
                {'issue': cls, 'confidence': round(prob, 4), 'percentage': round(prob * 100, 2)}
                for cls, prob in sorted(issue_probs.items(), key=lambda x: x[1], reverse=True)
                if prob > 0.1
            ]

            return {
                'primary_condition': primary,
                'confidence': round(confidence, 4),
                'all_conditions': top_conditions,  # Top 4 conditions
                'detected_issues': detected_issues,  # Issues like Acne, Bags, Redness
                'skin_type': top_skin_type,
                'skin_type_confidence': round(skin_type_confidence, 4),
                'probabilities': prob_dict,
                'face_detected': face_detected,
                'model_version': 'v3_multi_condition'
            }

        except Exception as e:
            print(f"[ERROR] Prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return None


def predict_with_xgboost(image_path):
    return XGBoostSkinPredictor().predict(image_path)


def get_xgboost_predictor():
    predictor = XGBoostSkinPredictor()
    predictor._load_model()
    return predictor
