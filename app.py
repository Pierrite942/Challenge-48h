<<<<<<< HEAD
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, template_folder='.') # Cherche index.html à la racine
CORS(app)

# Remplace par ta clé si tu n'utilises pas de fichier .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "ta_cle_ici"))
=======
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

# Configuration Flask avec le bon dossier de templates et static
app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

# Configuration de la clé API
API_KEY = "AIzaSyCuzEOE7JDRqczWZMNZt6iacP_lR1cbJu0"
genai.configure(api_key=API_KEY)
>>>>>>> 5db8cf0e6b0f1d5ba46ad792f745018f412f2079

@app.route('/')
def index():
    return render_template('index.html')

<<<<<<< HEAD
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message")
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": user_message}]
        )
        return jsonify({"reply": message.content[0].text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
=======
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Message vide'}), 400

        # Utiliser la bibliothèque Google Generative AI
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(user_message)
        
        if response and response.text:
            return jsonify({'response': response.text})
        else:
            return jsonify({'error': 'Pas de réponse de l\'IA'}), 500
            
    except Exception as e:
        print(f"Erreur dans /api/chat: {str(e)}")
        return jsonify({'error': f"Erreur: {str(e)}"}), 500

@app.route('/apropos')
def apropos():
    return render_template('html/apropos.html')

@app.route('/services')
def services():
    return render_template('html/services.html')

@app.route('/contact')
def contact():
    return render_template('html/contact.html')

if __name__ == '__main__':
    print("🚀 Démarrage du serveur Flask...")
    print("✅ API Gemini configurée")
    app.run(debug=True, host='127.0.0.1', port=5000)
>>>>>>> 5db8cf0e6b0f1d5ba46ad792f745018f412f2079
