from flask import Flask, request, jsonify, render_template, session
import json
import random
import os
from difflib import get_close_matches

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-123')

# Load phrase bank
def load_phrases():
    try:
        with open("data/phrase_bank.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("phrases", [])
    except:
        # Default phrases if file doesn't exist
        return [
            {
                "sesotho_phrase": "Lumela",
                "english_translation": "Hello",
                "response_options": ["Lumela! O kae?", "Lumela, kea leboha!"]
            },
            {
                "sesotho_phrase": "Kea leboha", 
                "english_translation": "Thank you",
                "response_options": ["Kea leboha le 'na!", "U amohelehile."]
            }
        ]

phrases = load_phrases()

def get_intent(user_input):
    user_input = user_input.lower().strip()
    
    # 1. Exact match
    for phrase in phrases:
        if phrase["sesotho_phrase"].lower() == user_input:
            return phrase, "exact"
    
    # 2. Partial match
    for phrase in phrases:
        if phrase["sesotho_phrase"].lower() in user_input:
            return phrase, "partial"
    
    # 3. Fuzzy match
    phrase_list = [p["sesotho_phrase"].lower() for p in phrases]
    matches = get_close_matches(user_input, phrase_list, n=1, cutoff=0.6)
    if matches:
        for phrase in phrases:
            if phrase["sesotho_phrase"].lower() == matches[0]:
                return phrase, "fuzzy"
    
    return None, "no_match"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid request"}), 400
        
        user_input = request.json.get("message", "").strip()
        
        if not user_input:
            return jsonify({"response": "Ha ke utloile hantle. Ka kopo, buisa hape."})
        
        if len(user_input) > 500:
            return jsonify({"response": "Ho buuoa ha holimo. Ka kopo, buisa ka lentsoe le khutšoanyane."})
        
        # Get intent
        intent_data, match_type = get_intent(user_input)
        
        if intent_data:
            response = random.choice(intent_data["response_options"])
            metadata = {
                "intent": intent_data.get("english_translation", "unknown"),
                "match_type": match_type
            }
        else:
            suggestions = [p["sesotho_phrase"] for p in phrases[:3]]
            response = f"Ha ke utloisise. Na u bolela: {', '.join(suggestions)}?"
            metadata = {"match_type": "no_match"}
        
        return jsonify({
            "response": response,
            "metadata": metadata
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Ho na le bothata. Ka kopo, leka hape."}), 500

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "Moleboheng AI",
        "phrases_loaded": len(phrases)
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
