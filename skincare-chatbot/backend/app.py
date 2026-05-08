from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from model.utils import predict_skin_condition
from flask_cors import CORS
from recommender.engine import recommend_products
from recommender.chatbot_nlp import handle_chat

# Paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BACKEND_DIR, '..', 'frontend')

app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Private-Network', 'true')
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response

UPLOAD_FOLDER = os.path.join(BACKEND_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Serve Frontend ───────────────────────────────────────────────────────────
@app.route('/')
def serve_index():
    return send_from_directory(os.path.abspath(FRONTEND_DIR), 'index.html')

@app.route('/<path:filename>')
def serve_frontend_file(filename):
    # Don't intercept API routes
    if filename.startswith(('upload', 'recommend', 'chat')):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory(os.path.abspath(FRONTEND_DIR), filename)


# ─── API ──────────────────────────────────────────────────────────────────────

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        return '', 204
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Allowed: png, jpg, jpeg, gif, bmp'}), 400
    
    try:
        # Create uploads folder if it doesn't exist
        upload_dir = os.path.abspath(os.path.join(BACKEND_DIR, 'static', 'uploads'))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        import uuid
        original_ext = os.path.splitext(file.filename)[1]
        filename = str(uuid.uuid4()) + original_ext
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Process the image
        context_data = {}
        for key in ['skin_type', 'skin_tone', 'climate', 'diet', 'hormonal', 'budget']:
            if key in request.form and request.form[key] and request.form[key] != 'auto':
                try:
                    context_data[key] = int(request.form[key])
                except (ValueError, TypeError):
                    context_data[key] = request.form[key]
                
        result = predict_skin_condition(file_path, context_data)
        
        # Delete the uploaded file after processing
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify(result), 200
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/recommend', methods=['POST'])
def recommend():
    """Return product recommendations based on skin condition."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        condition = data.get('condition', 'Normal')
        skin_type = data.get('skin_type', 'auto')
        budget = data.get('budget', 'auto')
        top_n = int(data.get('top_n', 5))

        products = recommend_products(
            condition=condition,
            skin_type=skin_type,
            budget=budget,
            top_n=top_n,
        )
        return jsonify({'products': products, 'condition': condition}), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """NLP chatbot endpoint."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        message = data.get('message', '')
        context = data.get('context', {})

        if not message.strip():
            return jsonify({'error': 'Empty message'}), 400

        reply = handle_chat(message, context)
        return jsonify({'reply': reply}), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Pre-load the model to improve first-request efficiency
    print("[Server] Pre-loading XGBoost model...")
    from model.xgboost_predictor import get_xgboost_predictor
    try:
        get_xgboost_predictor()
    except Exception as e:
        print(f"[Server] Warning: Could not pre-load model: {e}")
    
    print(f"[Server] Upload folder: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
    print(f"[Server] Backend directory: {BACKEND_DIR}")
    print(f"[Server] Frontend directory: {FRONTEND_DIR}")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)