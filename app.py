from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import google.generativeai as genai
import os
import time
import re
import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Charger la cle API depuis le fichier .env
load_dotenv()

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ynook-dev-secret-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Limiteur local anti-spam pour proteger le quota (1 requete / 3 secondes / IP)
RATE_LIMIT_SECONDS = 3.0
last_request_by_ip = {}

# Configuration MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ynook_db")


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


def get_mysql_connection(use_database=True):
    config = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
    }
    if use_database:
        config["database"] = MYSQL_DATABASE
    return mysql.connector.connect(**config)


def init_mysql():
    """Cree la base et les tables necessaires si elles n'existent pas."""
    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=False)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()

        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                prenom VARCHAR(100) NOT NULL,
                nom VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                from_user_id INT NOT NULL,
                to_user_id INT NOT NULL,
                status ENUM('pending', 'accepted', 'rejected') NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_request (from_user_id, to_user_id),
                CONSTRAINT fk_fr_from_user FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_fr_to_user FOREIGN KEY (to_user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS friends (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user1_id INT NOT NULL,
                user2_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_friend_pair (user1_id, user2_id),
                CONSTRAINT fk_f_user1 FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_f_user2 FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                content TEXT NOT NULL,
                is_read TINYINT(1) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_msg_sender FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_msg_receiver FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_msg_pair_time (sender_id, receiver_id, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )

        # Migration douce pour les anciennes bases deja creees sans la colonne is_read
        cursor.execute("SHOW COLUMNS FROM messages LIKE 'is_read'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE messages ADD COLUMN is_read TINYINT(1) NOT NULL DEFAULT 0")
        conn.commit()
        print("MySQL: base et table users prêtes")
    except mysql.connector.Error as err:
        print(f"MySQL init error: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


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


def require_auth_user():
    user = session.get('user')
    if not user:
        return None, (jsonify({'error': 'Authentification requise.'}), 401)
    return user, None


def normalize_friend_pair(user_a, user_b):
    return (min(user_a, user_b), max(user_a, user_b))


def get_relationship_status(conn, current_user_id, target_user_id):
    cursor = conn.cursor(dictionary=True)
    try:
        u1, u2 = normalize_friend_pair(current_user_id, target_user_id)
        cursor.execute(
            "SELECT id FROM friends WHERE user1_id = %s AND user2_id = %s LIMIT 1",
            (u1, u2)
        )
        if cursor.fetchone() is not None:
            return 'friends'

        cursor.execute(
            """
            SELECT from_user_id, to_user_id
            FROM friend_requests
            WHERE status = 'pending'
              AND ((from_user_id = %s AND to_user_id = %s) OR (from_user_id = %s AND to_user_id = %s))
            LIMIT 1
            """,
            (current_user_id, target_user_id, target_user_id, current_user_id)
        )
        req = cursor.fetchone()
        if req is None:
            return 'none'
        if req['from_user_id'] == current_user_id:
            return 'request_sent'
        return 'request_received'
    finally:
        cursor.close()


def are_friends(conn, user_a, user_b):
    u1, u2 = normalize_friend_pair(user_a, user_b)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM friends WHERE user1_id = %s AND user2_id = %s LIMIT 1",
            (u1, u2)
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/inscription')
def inscription_page():
    return render_template('html/inscription.html')


@app.route('/login')
def login_page():
    return render_template('html/login.html')


@app.route('/message')
def message_page():
    return render_template('html/message.html')

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


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or request.form

    prenom = (data.get('prenom') or '').strip()
    nom = (data.get('nom') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or data.get('confirm-password') or ''

    if not prenom or not nom or not email or not password or not confirm_password:
        return jsonify({'error': 'Tous les champs sont obligatoires.'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Les mots de passe ne correspondent pas.'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Le mot de passe doit contenir au moins 8 caracteres.'}), 400

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({'error': 'Format email invalide.'}), 400

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users (prenom, nom, email, password_hash) VALUES (%s, %s, %s, %s)",
            (prenom, nom, email, password_hash)
        )
        conn.commit()
        return jsonify({'message': 'Inscription reussie.'}), 201
    except mysql.connector.IntegrityError as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return jsonify({'error': 'Cet email est deja utilise.'}), 409
        return jsonify({'error': f'Erreur base de donnees: {err}'}), 500
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or request.form
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email et mot de passe obligatoires.'}), 400

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, prenom, nom, email, password_hash FROM users WHERE email = %s LIMIT 1",
            (email,)
        )
        user = cursor.fetchone()

        if user is None:
            return jsonify({'error': 'Compte introuvable.'}), 404

        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Mot de passe incorrect.'}), 401

        session['user'] = {
            'id': user['id'],
            'prenom': user['prenom'],
            'nom': user['nom'],
            'email': user['email']
        }

        return jsonify({
            'message': f"Connexion reussie. Bienvenue {user['prenom']}.",
            'user': session['user']
        }), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/me', methods=['GET'])
def me():
    user = session.get('user')
    if not user:
        return jsonify({'authenticated': False}), 200
    return jsonify({'authenticated': True, 'user': user}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'message': 'Deconnexion reussie.'}), 200


@app.route('/api/users/search', methods=['GET'])
def search_users():
    auth_user, error_response = require_auth_user()
    if error_response:
        return error_response

    query = (request.args.get('q') or '').strip()
    if len(query) < 2:
        return jsonify({'users': []}), 200

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        like_term = f"%{query}%"
        cursor.execute(
            """
            SELECT id, prenom, nom, email
            FROM users
            WHERE id != %s
              AND (prenom LIKE %s OR nom LIKE %s OR email LIKE %s)
            ORDER BY prenom ASC, nom ASC
            LIMIT 15
            """,
            (auth_user['id'], like_term, like_term, like_term)
        )
        users = cursor.fetchall()

        result = []
        for user in users:
            result.append({
                'id': user['id'],
                'prenom': user['prenom'],
                'nom': user['nom'],
                'email': user['email'],
                'relation_status': get_relationship_status(conn, auth_user['id'], user['id'])
            })

        return jsonify({'users': result}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/friends/request', methods=['POST'])
def send_friend_request():
    auth_user, error_response = require_auth_user()
    if error_response:
        return error_response

    data = request.get_json(silent=True) or request.form
    to_user_id = data.get('to_user_id')
    if to_user_id is None:
        return jsonify({'error': 'to_user_id est obligatoire.'}), 400

    try:
        to_user_id = int(to_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'to_user_id invalide.'}), 400

    if to_user_id == auth_user['id']:
        return jsonify({'error': 'Vous ne pouvez pas vous ajouter vous-meme.'}), 400

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM users WHERE id = %s LIMIT 1", (to_user_id,))
        if cursor.fetchone() is None:
            return jsonify({'error': 'Utilisateur introuvable.'}), 404

        u1, u2 = normalize_friend_pair(auth_user['id'], to_user_id)
        cursor.execute(
            "SELECT id FROM friends WHERE user1_id = %s AND user2_id = %s LIMIT 1",
            (u1, u2)
        )
        if cursor.fetchone() is not None:
            return jsonify({'error': 'Vous etes deja amis.'}), 409

        cursor.execute(
            "SELECT id, from_user_id, status FROM friend_requests WHERE from_user_id = %s AND to_user_id = %s LIMIT 1",
            (to_user_id, auth_user['id'])
        )
        incoming = cursor.fetchone()
        if incoming is not None and incoming['status'] == 'pending':
            return jsonify({'error': 'Cet utilisateur vous a deja envoye une demande. Consultez vos demandes.'}), 409

        cursor.execute(
            """
            INSERT INTO friend_requests (from_user_id, to_user_id, status)
            VALUES (%s, %s, 'pending')
            ON DUPLICATE KEY UPDATE status = 'pending'
            """,
            (auth_user['id'], to_user_id)
        )
        conn.commit()
        return jsonify({'message': 'Demande d\'ami envoyee.'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/friends/requests', methods=['GET'])
def incoming_friend_requests():
    auth_user, error_response = require_auth_user()
    if error_response:
        return error_response

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT fr.id, fr.created_at, u.id AS from_user_id, u.prenom, u.nom, u.email
            FROM friend_requests fr
            JOIN users u ON u.id = fr.from_user_id
            WHERE fr.to_user_id = %s AND fr.status = 'pending'
            ORDER BY fr.created_at DESC
            """,
            (auth_user['id'],)
        )
        return jsonify({'requests': cursor.fetchall()}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/friends/requests/<int:request_id>/respond', methods=['POST'])
def respond_friend_request(request_id):
    auth_user, error_response = require_auth_user()
    if error_response:
        return error_response

    data = request.get_json(silent=True) or request.form
    action = (data.get('action') or '').strip().lower()
    if action not in ('accept', 'reject'):
        return jsonify({'error': "action doit etre 'accept' ou 'reject'."}), 400

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, from_user_id, to_user_id, status
            FROM friend_requests
            WHERE id = %s
            LIMIT 1
            """,
            (request_id,)
        )
        req = cursor.fetchone()
        if req is None:
            return jsonify({'error': 'Demande introuvable.'}), 404

        if req['to_user_id'] != auth_user['id']:
            return jsonify({'error': 'Action non autorisee.'}), 403

        if req['status'] != 'pending':
            return jsonify({'error': 'Cette demande est deja traitee.'}), 409

        if action == 'accept':
            cursor.execute("UPDATE friend_requests SET status = 'accepted' WHERE id = %s", (request_id,))
            u1, u2 = normalize_friend_pair(req['from_user_id'], req['to_user_id'])
            cursor.execute(
                "INSERT IGNORE INTO friends (user1_id, user2_id) VALUES (%s, %s)",
                (u1, u2)
            )
            conn.commit()
            return jsonify({'message': 'Demande acceptee.'}), 200

        cursor.execute("UPDATE friend_requests SET status = 'rejected' WHERE id = %s", (request_id,))
        conn.commit()
        return jsonify({'message': 'Demande refusee.'}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/friends/list', methods=['GET'])
def list_friends():
    auth_user, error_response = require_auth_user()
    if error_response:
        return error_response

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                CASE
                    WHEN f.user1_id = %s THEN u2.id
                    ELSE u1.id
                END AS id,
                CASE
                    WHEN f.user1_id = %s THEN u2.prenom
                    ELSE u1.prenom
                END AS prenom,
                CASE
                    WHEN f.user1_id = %s THEN u2.nom
                    ELSE u1.nom
                END AS nom,
                CASE
                    WHEN f.user1_id = %s THEN u2.email
                    ELSE u1.email
                END AS email,
                f.created_at
            FROM friends f
            JOIN users u1 ON u1.id = f.user1_id
            JOIN users u2 ON u2.id = f.user2_id
            WHERE f.user1_id = %s OR f.user2_id = %s
            ORDER BY f.created_at DESC
            """,
            (
                auth_user['id'], auth_user['id'], auth_user['id'], auth_user['id'],
                auth_user['id'], auth_user['id']
            )
        )
        return jsonify({'friends': cursor.fetchall()}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/messages/send', methods=['POST'])
def send_message_to_friend():
    auth_user, error_response = require_auth_user()
    if error_response:
        return error_response

    data = request.get_json(silent=True) or request.form
    receiver_id = data.get('receiver_id')
    content = (data.get('content') or '').strip()

    if receiver_id is None:
        return jsonify({'error': 'receiver_id est obligatoire.'}), 400

    try:
        receiver_id = int(receiver_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'receiver_id invalide.'}), 400

    if receiver_id == auth_user['id']:
        return jsonify({'error': 'Vous ne pouvez pas vous envoyer un message a vous-meme.'}), 400

    if not content:
        return jsonify({'error': 'Le message est vide.'}), 400

    if len(content) > 2000:
        return jsonify({'error': 'Le message est trop long (max 2000 caracteres).'}), 400

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        if not are_friends(conn, auth_user['id'], receiver_id):
            return jsonify({'error': 'Vous devez etre amis pour vous envoyer des messages.'}), 403

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)",
            (auth_user['id'], receiver_id, content)
        )
        conn.commit()
        return jsonify({'message': 'Message envoye.'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/messages/conversation/<int:friend_id>', methods=['GET'])
def get_conversation(friend_id):
    auth_user, error_response = require_auth_user()
    if error_response:
        return error_response

    if friend_id == auth_user['id']:
        return jsonify({'messages': []}), 200

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        if not are_friends(conn, auth_user['id'], friend_id):
            return jsonify({'error': 'Acces refuse: vous n\'etes pas amis.'}), 403

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            UPDATE messages
            SET is_read = 1
            WHERE sender_id = %s
              AND receiver_id = %s
              AND is_read = 0
            """,
            (friend_id, auth_user['id'])
        )

        cursor.execute(
            """
            SELECT id, sender_id, receiver_id, content, is_read, created_at
            FROM messages
            WHERE (sender_id = %s AND receiver_id = %s)
               OR (sender_id = %s AND receiver_id = %s)
            ORDER BY created_at ASC, id ASC
            LIMIT 300
            """,
            (auth_user['id'], friend_id, friend_id, auth_user['id'])
        )
        conn.commit()
        return jsonify({'messages': cursor.fetchall()}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route('/api/notifications', methods=['GET'])
def notifications():
    auth_user, error_response = require_auth_user()
    if error_response:
        return error_response

    conn = None
    cursor = None
    try:
        conn = get_mysql_connection(use_database=True)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT COUNT(*) AS pending_count
            FROM friend_requests
            WHERE to_user_id = %s AND status = 'pending'
            """,
            (auth_user['id'],)
        )
        pending_count = cursor.fetchone()['pending_count']

        cursor.execute(
            """
            SELECT m.content, m.created_at, u.prenom, u.nom
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.receiver_id = %s
              AND m.is_read = 0
            ORDER BY m.created_at DESC, m.id DESC
            LIMIT 5
            """,
            (auth_user['id'],)
        )
        recent_messages = cursor.fetchall()

        return jsonify({
            'pending_friend_requests': pending_count,
            'recent_messages': recent_messages
        }), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'MySQL indisponible: {err}'}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    init_mysql()
    print("Serveur Ynook lance sur http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
