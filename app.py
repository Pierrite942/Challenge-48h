import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])
    if current_user is None:
        session.clear()
        return redirect(url_for("login"))

    return render_template("index.html", user=current_user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            flash("Le nom d'utilisateur et le mot de passe sont obligatoires.")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur existe déjà.")
            return render_template("register.html")

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Ce nom d'utilisateur existe déjà.")
            return render_template("register.html")

        # Connexion automatique après création de compte.
        session["user_id"] = new_user.id
        flash("Compte créé avec succès. Bienvenue !")
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash("Identifiants incorrects.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Tu as été déconnecté.")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
