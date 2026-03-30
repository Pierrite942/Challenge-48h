import os
from contextlib import closing

import psycopg2  # type: ignore[import-not-found]
from psycopg2 import OperationalError  # type: ignore[import-not-found]
from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/challenge_48h",
)


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS contact_messages (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(120) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        subject VARCHAR(160) NOT NULL,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )
            conn.commit()
    except Exception:
        print("Base PostgreSQL indisponible")


def fetch_recent_messages(limit=5):
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT name, email, subject, message, created_at
                    FROM contact_messages
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
        return [
            {
                "name": row[0],
                "email": row[1],
                "subject": row[2],
                "message": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]
    except Exception:
        return []


def save_contact_message(name, email, subject, message):
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO contact_messages (name, email, subject, message)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (name, email, subject, message),
                )
            conn.commit()
    except Exception as exc:
        raise OperationalError("Impossible d'enregistrer le message") from exc


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/apropos")
def apropos():
    return render_template('apropos.html')


@app.route("/services")
def services():
    return render_template('services.html')


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not subject or not message:
            flash("Tous les champs du formulaire sont obligatoires.", "error")
        else:
            try:
                save_contact_message(name, email, subject, message)
                flash("Message enregistré dans PostgreSQL.", "success")
                return redirect(url_for("contact"))
            except Exception as exc:
                flash(f"Impossible d'enregistrer le message: {exc}", "error")

    recent_messages = fetch_recent_messages()
    return render_template("contact.html", recent_messages=recent_messages)


try:
    init_db()
except Exception:
    print("Initialisation PostgreSQL ignorée")


if __name__ == "__main__":
    app.run(debug=True)