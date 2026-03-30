import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from models import News, User, db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def ensure_legacy_schema_updates() -> None:
    inspector = inspect(db.engine)

    user_columns = [column["name"] for column in inspector.get_columns("user")]
    if "is_admin" not in user_columns:
        db.session.execute(
            text('ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0')
        )
        db.session.commit()


with app.app_context():
    db.create_all()
    ensure_legacy_schema_updates()


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])
    if current_user is None:
        session.clear()
        return redirect(url_for("login"))

    all_news = News.query.order_by(News.created_at.desc()).all()
    return render_template("index.html", user=current_user, news_list=all_news)


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

        is_first_user = User.query.count() == 0

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
            is_admin=is_first_user,
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


@app.route("/news", methods=["POST"])
def add_news():
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_user = db.session.get(User, session["user_id"])
    if current_user is None:
        session.clear()
        return redirect(url_for("login"))

    if not current_user.is_admin:
        flash("Seuls les admins peuvent ajouter des news.")
        return redirect(url_for("index"))

    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()

    if not title or not content:
        flash("Titre et contenu sont obligatoires pour une news.")
        return redirect(url_for("index"))

    news_item = News(title=title, content=content, author_id=current_user.id)
    db.session.add(news_item)
    db.session.commit()
    flash("News ajoutée avec succès.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
