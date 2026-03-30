from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

# Charger la cle API depuis le fichier .env
load_dotenv()

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
CORS(app)

# Limiteur local anti-spam pour proteger le quota (1 requete / 3 secondes / IP)
RATE_LIMIT_SECONDS = 3.0
last_request_by_ip = {}


def local_fallback_response(user_message):
    """Reponse de secours quand l'API Gemini est indisponible (quota, etc.)."""
    text = user_message.strip().lower()

    if any(word in text for word in ["bonjour", "salut", "coucou", "hello"]):
        return "Mode secours actif: Bonjour. Je suis temporairement en mode local car le quota Gemini est depasse."

    if "nom" in text:
        return "Mode secours actif: Je suis l'assistant Ynook (mode local temporaire)."

    if any(word in text for word in ["aide", "help", "comment", "quoi faire"]):
        return (
            "Mode secours actif: je peux vous aider a reformuler un texte, proposer un plan d'action, "
            "ou repondre simplement a des questions courtes."
        )

    return (
        "Mode secours actif: le quota Gemini est depasse pour le moment. "
        "Reessayez plus tard ou ajoutez une nouvelle cle API, et je repasserai en mode IA automatiquement."
    )

def get_api_key():
    # Recharge .env pour prendre en compte une nouvelle cle sans redemarrer le serveur
    load_dotenv(override=True)
    return os.getenv("GEMINI_API_KEY", "").strip()


def check_rate_limit(client_ip):
    now = time.monotonic()
    last_time = last_request_by_ip.get(client_ip)
    if last_time is None:
        last_request_by_ip[client_ip] = now
        return 0.0

    elapsed = now - last_time
    if elapsed < RATE_LIMIT_SECONDS:
        return RATE_LIMIT_SECONDS - elapsed

    last_request_by_ip[client_ip] = now
    return 0.0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        client_ip = request.remote_addr or "unknown"
        wait_seconds = check_rate_limit(client_ip)
        if wait_seconds > 0:
            return jsonify({
                'error': f"Trop de messages. Reessayez dans {wait_seconds:.1f} seconde(s)."
            }), 429

        api_key = get_api_key()
        if api_key:
            genai.configure(api_key=api_key)
        else:
            return jsonify({'error': 'Cle API manquante dans le fichier .env'}), 500

        data = request.json
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Message vide'}), 400

        # Fallback de modeles: Gemini d'abord, puis Gemma si quota Gemini depasse
        model_names = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemma-3-1b-it",
            "gemma-3-4b-it",
        ]
        response = None
        last_err = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(user_message)
                break
            except Exception as model_err:
                last_err = model_err
                err_text = str(model_err).lower()
                # Si quota depasse pour un modele, on tente le modele suivant
                if "429" in err_text or "quota" in err_text or "resource_exhausted" in err_text:
                    continue
                if "not found" in err_text or "not supported" in err_text or "404" in err_text:
                    continue
                raise

        if response is None and last_err is not None:
            raise last_err

        if response and response.text:
            return jsonify({'response': response.text})
        else:
            return jsonify({'error': "L'IA n'a pas pu generer de texte."}), 500

    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "API Key not found" in err_msg:
            return jsonify({'error': "Cle API Gemini invalide. Regenerer une cle sur ai.google.dev et mettez-la dans .env."}), 401
        if "429" in err_msg or "quota" in err_msg.lower():
            return jsonify({
                'response': local_fallback_response(user_message),
                'fallback': True,
                'warning': 'Quota Gemini depasse. Reponse locale de secours.'
            }), 200
        return jsonify({'error': f"Erreur serveur : {err_msg}"}), 500

if __name__ == '__main__':
    print("Serveur Ynook lance sur http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
