from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Important for voice features

# Your existing routes
#@app.route('/simple-voice-test')
#def simple_voice_test():
#    return render_template('simple-voice-test.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/category/<category_name>')
def category(category_name):
    return render_template('category.html', category=category_name)

@app.route('/phrase/<phrase_id>')
def phrase_detail(phrase_id):
    return render_template('phrase_detail.html', phrase_id=phrase_id)

# NEW: Voice assistant page
@app.route('/voice')
def voice():
    return render_template('voice.html')

# NEW: Voice transcription endpoint (for when you deploy to Render)
@app.route('/transcribe', methods=['POST'])
def transcribe():
    """This will be used when deployed to Render"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400
        
        # For now, return mock response
        # Later, this will use Whisper for real transcription
        return jsonify({
            "transcribed_text": "Dumela, u phela joang?",
            "ai_response": "Ke phela hantle, kea leboha!"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Your existing JSON endpoints
@app.route('/api/phrases')
def get_phrases():
    with open('data/phrases.json', 'r') as f:
        return jsonify(json.load(f))

@app.route('/api/categories')
def get_categories():
    with open('data/categories.json', 'r') as f:
        return jsonify(json.load(f))

if __name__ == '__main__':
    app.run(debug=True)
