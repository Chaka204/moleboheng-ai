from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
import difflib
import random

app = Flask(__name__)
CORS(app)

# ── helpers ──────────────────────────────────────────────────────────────────

def load_json(filename):
    path = os.path.join('data', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_best_match(user_input, phrases):
    user_lower = user_input.lower().strip()
    best_score = 0
    best_phrase = None
    match_type = "none"

    for phrase in phrases:
        sesotho = phrase['sesotho_phrase'].lower()
        keywords = [k.lower() for k in phrase.get('keywords', []) if k]

        # 1. Exact match
        if user_lower == sesotho:
            return phrase, 1.0, "exact"

        # 2. Keyword match
        for kw in keywords:
            if kw and kw in user_lower:
                if 0.8 > best_score:
                    best_score = 0.8
                    best_phrase = phrase
                    match_type = "keyword"

        # 3. Fuzzy match
        score = difflib.SequenceMatcher(None, user_lower, sesotho).ratio()
        if score > best_score and score > 0.45:
            best_score = score
            best_phrase = phrase
            match_type = "fuzzy"

    return best_phrase, best_score, match_type

def get_response_for_phrase(phrase_id, responses):
    """Pick a random response that matches the phrase_id."""
    matches = [r for r in responses if r['phrase_id'] == phrase_id]
    if matches:
        chosen = random.choice(matches)
        return chosen['response_sesotho']
    return None

# ── page routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/category/<category_name>')
def category(category_name):
    return render_template('category.html', category=category_name)

@app.route('/phrase/<int:phrase_id>')
def phrase_detail(phrase_id):
    return render_template('phrase_detail.html', phrase_id=phrase_id)

@app.route('/voice')
def voice():
    return render_template('voice.html')

# ── api routes ────────────────────────────────────────────────────────────────

@app.route('/api/phrases')
def get_phrases():
    category = request.args.get('category')
    data = load_json('phrases.json')
    phrases = data['phrases']
    if category:
        phrases = [p for p in phrases if p['category'] == category]
    return jsonify(phrases)

@app.route('/api/categories')
def get_categories():
    return jsonify(load_json('categories.json'))

@app.route('/api/chat', methods=['POST'])
def chat():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"response": "Ka kopo, rome molaetsa.", 
                        "metadata": {"match_type": "none", "intent": "empty", "confidence": 0}}), 400

    user_message = body.get('message', '').strip()

    if not user_message:
        return jsonify({
            "response": "Ha ke utloisise. Ka kopo, leka hape.",
            "metadata": {"match_type": "none", "intent": "empty", "confidence": 0}
        })

    phrases = load_json('phrases.json')['phrases']
    responses = load_json('responses.json')['responses']

    match, score, match_type = find_best_match(user_message, phrases)

    if match:
        # Try responses.json first, fall back to a generic reply
        response_text = get_response_for_phrase(match['id'], responses)
        if not response_text:
            response_text = f"O itse: \"{match['sesotho_phrase']}\" — {match['english_translation']}"
        intent = match['sesotho_phrase']
    else:
        response_text = "Ha ke utloisise hantle. Ka kopo, leka hape."
        intent = "unknown"

    return jsonify({
        "response": response_text,
        "metadata": {
            "match_type": match_type,
            "intent": intent,
            "confidence": round(score, 2)
        }
    })

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    return jsonify({
        "transcribed_text": "Lumela, u phela joang?",
        "ai_response": "Ke phela hantle, kea leboha!"
    })

# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
