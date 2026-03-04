import json
import os
import re
import random
from difflib import SequenceMatcher
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'


# ── Database ──────────────────────────────────────────────────────────────────

class SesothoDatabase:
    def __init__(self):
        self.data_path = "data"
        self.load_all_data()

    def load_all_data(self):
        self.phrases = self._load_json("phrases.json")
        self.responses = self._load_or_create("responses.json", {"responses": []})
        self.categories = self._load_or_create("categories.json", {"categories": []})

    def _load_json(self, filename):
        path = os.path.join(self.data_path, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_or_create(self, filename, default_data):
        path = os.path.join(self.data_path, filename)
        try:
            return self._load_json(filename)
        except FileNotFoundError:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data

    def get_all_phrases(self):
        return self.phrases.get('phrases', [])

    def get_phrases_by_category(self, category):
        return [p for p in self.get_all_phrases() if p.get('category') == category]

    def get_phrase_by_id(self, phrase_id):
        phrase = next((p for p in self.get_all_phrases() if p['id'] == phrase_id), None)
        if phrase:
            phrase = dict(phrase)  # don't mutate original
            phrase['response_options'] = [
                r for r in self.responses.get('responses', [])
                if r.get('phrase_id') == phrase_id
            ]
        return phrase

    def get_all_categories(self):
        return self.categories.get('categories', [])

    def get_category_by_name(self, name):
        return next((c for c in self.get_all_categories() if c['name'] == name), None)


# ── AI ────────────────────────────────────────────────────────────────────────

class SesothoAI:
    def __init__(self, database):
        self.db = database

    def normalize_text(self, text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def similarity_score(self, text1, text2):
        return SequenceMatcher(None, text1, text2).ratio()

    def find_best_match(self, user_input):
        normalized_input = self.normalize_text(user_input)
        best_score = 0
        best_phrase = None

        for phrase in self.db.get_all_phrases():
            # Check sesotho phrase
            sesotho_score = self.similarity_score(
                normalized_input, self.normalize_text(phrase['sesotho_phrase'])
            )
            # Check english translation
            english_score = self.similarity_score(
                normalized_input, self.normalize_text(phrase['english_translation'])
            ) * 0.8

            # Check keywords
            keyword_score = 0
            for kw in phrase.get('keywords', []):
                if kw and kw.lower() in normalized_input:
                    keyword_score = 0.85
                    break

            current_score = max(sesotho_score, english_score, keyword_score)

            if current_score > best_score:
                best_score = current_score
                best_phrase = phrase

        return best_phrase, best_score

    def check_personal_questions(self, user_input):
        """Handle questions directed at Moleboheng personally"""
        text = user_input.lower().strip()
    
        personal_responses = {
            # Who are you / what's your name
            ('u mang', 'o mang', 'lebitso la hao', 'lebitso la hau', 'what is your name', 'who are you'):
                ('Ke Moleboheng! Ke motšehetsi oa puo ea Sesotho. Ke hano ho o thusa ho ithuta le ho bua Sesotho.',
                 'I am Moleboheng! I am a Sesotho language assistant. I am here to help you learn and speak Sesotho.'),
    
            # How are you
            ('o phela joang', 'u phela joang', 'how are you'):
                ('Ke phela hantle, kea leboha! Wena o phela joang?',
                 'I am doing well, thank you! How are you doing?'),
    
            # What can you do
            ('u etsa eng', 'o etsa eng', 'what can you do', 'what do you do'):
                ('Nka o thusa ho ithuta Sesotho! Nka ho bolella ka mantsoe, dipuisano le ngoloa tsa Sesotho.',
                 'I can help you learn Sesotho! I can tell you about words, conversations and Sesotho literature.'),
    
            # Where are you from
            ('u tsoa kae', 'o tsoa kae', 'where are you from'):
                ('Ke tsoa Lesotho — naha e potiloe ke Afrika Borwa. Ke naha ea Basotho!',
                 'I come from Lesotho — a country surrounded by South Africa. It is the home of the Basotho people!'),
    
            # Greetings
            ('lumela', 'hello', 'hi', 'sawubona'):
                ('Lumela! Kea thaba ho kopana le uena. Nka o thusa joang kajeno?',
                 'Hello! I am happy to meet you. How can I help you today?'),
    
            # Farewells — this was missing before
            ('sala hantle', 'sala hantle', 'goodbye', 'bye', 'tsamaea hantle', 'tsamaea'):
                ('Sala hantle! Kea leboha hore u ile u bua le nna. Re tla bua hape!',
                 'Goodbye! Thank you for speaking with me. We will speak again!'),
    
            # Thank you
            ('kea leboha', 'kea lebohisa', 'thank you', 'thanks'):
                ('O amohelehile! Ke thabo ea ka ho u thusa. Na ho na le ntho e nngwe eo nka o thusang ka eona?',
                 'You are welcome! It is my pleasure to help you. Is there anything else I can help you with?'),
    
            # I am fine responses
            ('kea phela', 'ke phela hantle', 'i am fine', "i'm fine"):
                ('Ke utloa! Ke thabile hore u phela hantle. A re tsoele pele ho ithuta Sesotho!',
                 'I hear you! I am glad you are doing well. Let us continue learning Sesotho!'),
    
            # Yes
            ('ee', 'yes', 'yeah', 'yep'):
                ('Ee! Tsoele pele, ke mamela.',
                 'Yes! Please continue, I am listening.'),
    
            # No
            ('che', 'no', 'nope', 'nah'):
                ('Ke utloa. Na nka o thusa ka tsela e nngwe?',
                 'I understand. Can I help you in another way?'),
    
            # Help request
            ('thusa', 'help', 'nthuse', 'i need help'):
                ('Ke hano! Nka o thusa ka Sesotho. U batla ho ithuta eng kajeno?',
                 'I am here! I can help you with Sesotho. What would you like to learn today?'),
        }
    
        for triggers, (sesotho_reply, english_reply) in personal_responses.items():
            for trigger in triggers:
                if trigger in text:
                    return {
                        'response': sesotho_reply,
                        'english': english_reply,
                        'match_type': 'personal',
                        'intent': 'personal_question',
                        'confidence': 1.0
                    }
        return None

    def check_translation_request(self, user_input):
        """Detect if user is explicitly asking for a translation"""
        text = user_input.lower().strip()
        translation_triggers = [
            'translate', 'fetola', 'what does', 'what is', 'meaning of',
            'ho bolela eng', 'bolela ka sekhooa', 'in english', 'ka sesotho'
        ]
        return any(trigger in text for trigger in translation_triggers)    


    
    def generate_response(self, user_input):
        """Generate a response based on user input"""
        
        # 1. Check if it's a personal question first
        personal = self.check_personal_questions(user_input)
        if personal:
            return personal
    
        # 2. Check if user is explicitly asking for a translation
        wants_translation = self.check_translation_request(user_input)
    
        # 3. Find best phrase match
        phrase, score = self.find_best_match(user_input)
    
        if phrase and score > 0.5:
            responses = [
                r for r in self.db.responses.get('responses', [])
                if r.get('phrase_id') == phrase['id']
            ]
    
            if wants_translation:
                # User asked for translation — give it
                return {
                    'response': f'"{phrase["sesotho_phrase"]}" e bolela "{phrase["english_translation"]}" ka Sekhooa.',
                    'english': phrase['english_translation'],
                    'match_type': 'translation',
                    'intent': phrase.get('category', 'general'),
                    'confidence': round(score, 2),
                }
            elif responses:
                # Normal conversation — respond naturally
                response = random.choice(responses)
                return {
                    'response': response.get('response_sesotho', 'Kea leboha.'),
                    'english': response.get('response_english', ''),
                    'match_type': 'direct_match' if score > 0.8 else 'close_match',
                    'intent': phrase.get('category', 'general'),
                    'confidence': round(score, 2),
                }
            else:
                # Match found but no response — converse naturally
                return {
                    'response': f'Ee, ke utloa! O bolela ka "{phrase["sesotho_phrase"]}". Nka o thusa joang?',
                    'english': '',
                    'match_type': 'phrase_only',
                    'intent': phrase.get('category', 'general'),
                    'confidence': round(score, 2),
                }
        else:
            return {
                'response': 'Ke kopa utloisise. Ka kopo, buisa hape, kapa u botse ka tsela e fapaneng.',
                'english': 'I did not understand. Please say it again, or ask in a different way.',
                'match_type': 'no_match',
                'intent': 'unknown',
                'confidence': 0,
            }


# ── Init ──────────────────────────────────────────────────────────────────────

db = SesothoDatabase()
ai = SesothoAI(db)


# ── Page Routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    categories = db.get_all_categories()
    return render_template('index.html', categories=categories)


@app.route('/categories')
def all_categories():
    categories = db.get_all_categories()
    return render_template('categories.html', categories=categories)


@app.route('/category/<string:category_name>')
def category_detail(category_name):
    category = db.get_category_by_name(category_name)
    if not category:
        return "Category not found", 404
    phrases = db.get_phrases_by_category(category_name)
    return render_template('category.html', category=category, phrases=phrases)


@app.route('/phrase/<int:phrase_id>')
def phrase_detail(phrase_id):
    phrase = db.get_phrase_by_id(phrase_id)
    if not phrase:
        return "Phrase not found", 404
    return render_template('phrase_detail.html', phrase=phrase)


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route('/api/phrases')
def api_phrases():
    category = request.args.get('category')
    phrases = db.get_all_phrases()
    if category:
        phrases = [p for p in phrases if p.get('category') == category]
    return jsonify(phrases)


@app.route('/api/categories')
def api_categories():
    return jsonify(db.get_all_categories())


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                'response': 'Ha ho mantsoe a fanoeng.',
                'metadata': {'match_type': 'error', 'intent': 'empty', 'confidence': 0}
            }), 400

        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({
                'response': 'Ha ke utloisise. Ka kopo, leka hape.',
                'metadata': {'match_type': 'none', 'intent': 'empty', 'confidence': 0}
            })

        ai_response = ai.generate_response(user_message)
        log_interaction(user_message, ai_response)

        return jsonify({
            'response': ai_response['response'],
            'metadata': {
                'match_type': ai_response['match_type'],
                'intent': ai_response['intent'],
                'confidence': ai_response['confidence'],
                'english': ai_response.get('english', '')
            }
        })

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            'response': 'Ho na le bothata. Ka kopo, leka hape.',
            'metadata': {'match_type': 'error', 'intent': 'error', 'confidence': 0}
        }), 500


# ── Logging ───────────────────────────────────────────────────────────────────

def log_interaction(user_input, ai_response):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_input': user_input,
        'ai_response': ai_response['response'],
        'match_type': ai_response['match_type'],
        'confidence': ai_response['confidence']
    }
    try:
        with open('interaction_log.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


if __name__ == '__main__':
    app.run(debug=True)
