from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

# Configuration Flask avec le bon dossier de templates et static
app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

# Configuration de la clé API
API_KEY = "AIzaSyCuzEOE7JDRqczWZMNZt6iacP_lR1cbJu0"
genai.configure(api_key=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

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
