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

@app.route('/')
def index():
    return render_template('index.html')

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