from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

GEMINI_API_KEY = "AIzaSyBrYM2z5U6k5-zSBuliFFmEdPkHQPC9MlY"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': 'Message vide'}), 400

    payload = {
        "contents": [
            {"parts": [{"text": user_message}]}
        ]
    }

    try:
        resp = requests.post(GEMINI_URL, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        bot_reply = result['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'response': bot_reply})
    except requests.exceptions.Timeout:
        return jsonify({'error': "L'IA met trop de temps à répondre."}), 504
    except Exception as e:
        return jsonify({'error': f"Erreur API Gemini : {str(e)}"}), 500

@app.route('/apropos')
def apropos():
    return render_template('apropos.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
