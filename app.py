import json
import os
from flask import Flask, render_template, request, session, jsonify

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this for production

class SesothoDatabase:
    def __init__(self):
        self.data_path = "data"
        self.load_all_data()
    
    def load_all_data(self):
        """Load all database files with fallback to old structure"""
        # Try new structure first
        try:
            self.phrases = self._load_json("phrases.json")
        except FileNotFoundError:
            # Fallback to old structure
            old_data = self._load_json("phrase_bank.json")
            # Convert old structure to new
            self.phrases = self._convert_old_structure(old_data)
        
        # Load other data files (create if don't exist)
        self.responses = self._load_or_create("responses.json", {"responses": []})
        self.categories = self._load_or_create("categories.json", {"categories": []})
        self.examples = self._load_or_create("usage_examples.json", {"examples": []})
        
        # Initialize users from session or create demo
        self.users = {"users": []}
    
    def _load_json(self, filename):
        """Load a JSON file from data folder"""
        path = os.path.join(self.data_path, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_or_create(self, filename, default_data):
        """Load or create a JSON file"""
        path = os.path.join(self.data_path, filename)
        try:
            return self._load_json(filename)
        except FileNotFoundError:
            # Save default data
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data
    
    def _convert_old_structure(self, old_data):
        """Convert old phrase_bank.json to new structure"""
        phrases = []
        for i, item in enumerate(old_data.get('phrases', []), 1):
            phrase = {
                'id': i,
                'sesotho_phrase': item.get('sesotho_phrase', ''),
                'english_translation': item.get('english_translation', ''),
                'category': 'uncategorized',  # Default category
                'difficulty': 'beginner'
            }
            phrases.append(phrase)
        
        return {'phrases': phrases}
    
    def get_all_phrases(self):
        """Get all phrases"""
        return self.phrases.get('phrases', [])
    
    def get_phrase_with_responses(self, phrase_id):
        """Get a phrase with all its responses and examples"""
        phrase = next((p for p in self.get_all_phrases() if p['id'] == phrase_id), None)
        if phrase:
            # Add responses
            phrase['response_options'] = [
                r for r in self.responses.get('responses', [])
                if r.get('phrase_id') == phrase_id
            ]
            # Add examples
            phrase['examples'] = [
                e for e in self.examples.get('examples', [])
                if e.get('phrase_id') == phrase_id
            ]
        return phrase
    
    def get_phrases_by_category(self, category):
        """Get phrases by category"""
        return [p for p in self.get_all_phrases() if p.get('category') == category]

# Initialize database
db = SesothoDatabase()

@app.route('/')
def index():
    """Main page"""
    # Get all categories
    categories = set(p.get('category', 'uncategorized') for p in db.get_all_phrases())
    
    return render_template('index.html', 
                         categories=categories,
                         phrases=db.get_all_phrases())

@app.route('/phrase/<int:phrase_id>')
def phrase_detail(phrase_id):
    """Get detailed phrase information"""
    phrase = db.get_phrase_with_responses(phrase_id)
    if phrase:
        return render_template('phrase_detail.html', phrase=phrase)
    return "Phrase not found", 404

@app.route('/category/<category_name>')
def category_phrases(category_name):
    """Get all phrases in a category"""
    phrases = db.get_phrases_by_category(category_name)
    return render_template('category.html', 
                         category=category_name,
                         phrases=phrases)

@app.route('/api/phrases')
def api_phrases():
    """API endpoint for phrases (for AJAX calls)"""
    return jsonify(db.get_all_phrases())

@app.route('/api/phrase/<int:phrase_id>')
def api_phrase_detail(phrase_id):
    """API endpoint for phrase details"""
    phrase = db.get_phrase_with_responses(phrase_id)
    if phrase:
        return jsonify(phrase)
    return jsonify({'error': 'Phrase not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)

# In your app.py
@app.route('/categories')
def all_categories():
    categories = load_json_data('categories.json')
    return render_template('categories.html', categories=categories['categories'])

@app.route('/category/<string:category_name>')
def category_detail(category_name):
    categories = load_json_data('categories.json')
    phrases = load_json_data('phrases.json')
    
    # Find the category
    category = next((c for c in categories['categories'] if c['name'] == category_name), None)
    
    if not category:
        return "Category not found", 404
    
    # Get phrases for this category
    category_phrases = [p for p in phrases['phrases'] if p['category'] == category_name]
    
    return render_template('category.html', 
                         category=category, 
                         phrases=category_phrases)

@app.route('/phrase/<int:phrase_id>')
def phrase_detail(phrase_id):
    phrases = load_json_data('phrases.json')
    responses = load_json_data('responses.json')
    examples = load_json_data('usage_examples.json')
    grammar_rules = load_json_data('grammar_rules.json')
    cultural_contexts = load_json_data('cultural_context.json')
    
    # Find the phrase
    phrase = next((p for p in phrases['phrases'] if p['id'] == phrase_id), None)
    
    if not phrase:
        return "Phrase not found", 404
    
    # Get related data
    phrase_responses = [r for r in responses['responses'] if r['phrase_id'] == phrase_id]
    phrase_examples = [e for e in examples['examples'] if e['phrase_id'] == phrase_id]
    related_grammar = [g for g in grammar_rules['grammar_rules'] 
                      if phrase.category in g['categories']]
    related_cultural = [c for c in cultural_contexts['cultural_contexts'] 
                       if phrase.category in c['categories']]
    
    return render_template('phrase_detail.html', 
                         phrase=phrase,
                         response_options=phrase_responses,
                         examples=phrase_examples,
                         grammar_rules=related_grammar,
                         cultural_contexts=related_cultural)
