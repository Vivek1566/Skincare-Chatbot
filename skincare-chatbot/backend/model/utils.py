import os
import numpy as np
try:
    from model.xgboost_predictor import predict_with_xgboost
except ImportError:
    from xgboost_predictor import predict_with_xgboost

# All 6 skin condition classes
classes = ['Acne', 'Bags', 'Dry', 'Redness', 'Oily', 'Normal']

def predict_skin_condition(image_path, context_data=None):
    """
    Main entry point for skin condition prediction.
    Uses XGBoost model with face detection for accurate results.
    """
    try:
        result = predict_with_xgboost(image_path)

        if result is None:
            return {
                'error': 'Prediction failed — could not process image',
                'primary_condition': 'Unknown',
                'confidence': 0.0
            }

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'primary_condition': 'Unknown',
            'confidence': 0.0
        }

def preprocess_image_to_features(image_path, context_data=None):
    return np.zeros((1, 1280))  # Placeholder for legacy compatibility