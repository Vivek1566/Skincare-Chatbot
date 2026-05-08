"""
engine.py --- Enhanced Content-based product recommendation engine
Supports "Oily" condition and removed rates (prices/ratings) from output.
"""

import os
import zipfile
import csv
import io
import json
from collections import defaultdict

# --- Paths ---
ZIP_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', 'archive_7.zip'
)

# --- Expanded Ingredient -> Condition mapping ---
INGREDIENT_CONDITION_MAP = {
    'Salicylic_Acid': ['Acne', 'Oily', 'Sensitivity'],
    'Hyaluronic_Acid': ['Dryness', 'Normal', 'Sensitive', 'Aging', 'Bags'],
    'Retinol': ['Aging', 'Pigmentation', 'Normal', 'Acne'],
    'Vitamin_C': ['Pigmentation', 'Aging', 'Normal', 'Redness'],
    'Ceramides': ['Dryness', 'Sensitivity', 'Sensitive', 'Dry', 'Redness'],
    'Caffeine': ['Bags'],
    'Peptides': ['Bags', 'Aging'],
    'Niacinamide': ['Redness', 'Acne', 'Normal', 'Pigmentation', 'Oily'],
    'Aloe_Vera': ['Redness', 'Sensitivity', 'Sensitive'],
    'Centella_Asiatica': ['Redness', 'Sensitivity', 'Sensitive'],
    'Azelaic_Acid': ['Acne', 'Redness', 'Pigmentation'],
    'Alpha_Arbutin': ['Pigmentation'],
    'Kojic_Acid': ['Pigmentation'],
    'Glycolic_Acid': ['Aging', 'Pigmentation', 'Acne', 'Oily'],
    'Squalane': ['Dryness', 'Normal', 'Sensitivity'],
    'Tea_Tree_Oil': ['Acne', 'Oily'],
    'Clay': ['Oily', 'Acne'],
    'Witch_Hazel': ['Oily', 'Acne'],
}

# --- Data loading ---
_products = []          
_avg_ratings = {}       

def _load_data():
    global _products, _avg_ratings
    zip_candidates = [
        ZIP_PATH,
        os.path.join(os.path.dirname(__file__), '..', 'archive_7.zip'),
        r"d:\Skincare Detection chatbot\archive_7.zip",
    ]

    zip_path = None
    for p in zip_candidates:
        norm = os.path.normpath(p)
        if os.path.exists(norm):
            zip_path = norm
            break

    if zip_path is None:
        _products = _fallback_products()
        return

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            with z.open('products.csv') as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
                for row in reader:
                    _products.append({
                        'id': int(row['Product_ID']),
                        'brand': row['Brand'],
                        'price': float(row['Price']),
                        'ingredients': [i.strip() for i in row['Ingredients'].split('|')],
                    })
    except:
        _products = _fallback_products()

def _fallback_products():
    return [
        {'id': 0, 'brand': 'DermaCare Acne Relief', 'price': 25, 'ingredients': ['Salicylic_Acid', 'Niacinamide']},
        {'id': 1, 'brand': 'HydraGlow Serum', 'price': 45, 'ingredients': ['Hyaluronic_Acid', 'Ceramides']},
        {'id': 2, 'brand': 'AgeDefy Night Cream', 'price': 85, 'ingredients': ['Retinol', 'Peptides']},
        {'id': 3, 'brand': 'BrightenUp Essence', 'price': 55, 'ingredients': ['Vitamin_C', 'Alpha_Arbutin']},
        {'id': 4, 'brand': 'CalmDown Cica Gel', 'price': 30, 'ingredients': ['Centella_Asiatica', 'Aloe_Vera']},
        {'id': 5, 'brand': 'WakeUp Eye Cream', 'price': 35, 'ingredients': ['Caffeine', 'Hyaluronic_Acid']},
        {'id': 6, 'brand': 'Oil-Control Matte Clay Mask', 'price': 22, 'ingredients': ['Clay', 'Witch_Hazel', 'Niacinamide']},
        {'id': 7, 'brand': 'Pore-Refining Gel', 'price': 32, 'ingredients': ['Salicylic_Acid', 'Tea_Tree_Oil']},
    ]

# Load on import
_load_data()

def _condition_to_targets(condition: str, skin_type: str = '') -> list:
    targets = [condition, skin_type]
    condition_map = {
        'Acne': ['Acne', 'Oily'],
        'Oily': ['Oily', 'Acne'],
        'Dryness': ['Dryness', 'Dry'],
        'Aging': ['Aging'],
        'Pigmentation': ['Pigmentation'],
        'Sensitivity': ['Sensitivity', 'Sensitive'],
        'Normal': ['Normal'],
        'Bags': ['Bags'],
        'Redness': ['Redness'],
    }
    extras = condition_map.get(condition, [condition])
    targets.extend(extras)
    return list(set(t for t in targets if t))

def recommend_products(condition: str = 'Normal', skin_type: str = 'auto', budget: str = 'auto', top_n: int = 5) -> list:
    targets = _condition_to_targets(condition, skin_type)

    scored = []
    for prod in _products:
        match_score = 0
        matched_ingredients = []
        for ing in prod['ingredients']:
            helps = INGREDIENT_CONDITION_MAP.get(ing, [])
            overlap = [t for t in targets if t in helps]
            if overlap:
                match_score += len(overlap)
                matched_ingredients.append(ing)

        if match_score > 0:
            scored.append((match_score, prod, matched_ingredients))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_n]

    results = []
    for match_score, prod, matched_ings in top:
        if matched_ings:
            reason = f"Ideal match: contains {', '.join(i.replace('_', ' ') for i in matched_ings)} to target {condition}."
        else:
            reason = f"Recommended for maintaining healthy {condition} skin."

        results.append({
            'brand': prod['brand'],
            'ingredients': [i.replace('_', ' ') for i in prod['ingredients']],
            'match_score': round(match_score, 2),
            'recommendation_reason': reason,
        })

    return results
