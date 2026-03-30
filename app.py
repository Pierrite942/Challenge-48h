import os
import uuid

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from models import News, Post, PostComment, PostLike, User, db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder or "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "ogg"}

db.init_app(app)


def _save_media_file(file_storage, allowed_extensions: set[str], subfolder: str):
    if file_storage is None or not file_storage.filename:
        return None

    safe_name = secure_filename(file_storage.filename)
    if "." not in safe_name:
        return None

    extension = safe_name.rsplit(".", 1)[1].lower()
    if extension not in allowed_extensions:
        return None

    unique_name = f"{uuid.uuid4().hex}.{extension}"
    relative_folder = os.path.join("uploads", subfolder)
    absolute_folder = os.path.join(app.static_folder or "static", relative_folder)
    os.makedirs(absolute_folder, exist_ok=True)

    absolute_path = os.path.join(absolute_folder, unique_name)
    file_storage.save(absolute_path)

    return f"{relative_folder}/{unique_name}".replace("\\", "/")


def _news_to_dict(item: News) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "author": item.author.username,
        "author_id": item.author_id,
        "created_at": item.created_at.strftime("%d/%m %H:%M"),
        "image_path": item.image_path,
        "video_path": item.video_path,
    }


def _post_to_dict(item: Post, current_user_id: int) -> dict:
    return {
        "id": item.id,
        "content": item.content,
        "author": item.author.username,
        "author_id": item.author_id,
        "created_at": item.created_at.strftime("%d/%m %H:%M"),
        "image_path": item.image_path,
        "video_path": item.video_path,
        "likes_count": len(item.likes),
        "comments_count": len(item.comments),
        "liked_by_current": any(like.user_id == current_user_id for like in item.likes),
    }


def _get_current_user():
    if "user_id" not in session:
        return None

    current_user = db.session.get(User, session["user_id"])
    if current_user is None:
        session.clear()
        return None
    return current_user


def ensure_legacy_schema_updates() -> None:
    inspector = inspect(db.engine)

    user_columns = [column["name"] for column in inspector.get_columns("user")]
    if "is_admin" not in user_columns:
        db.session.execute(
            text('ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0')
        )
        db.session.commit()

    news_columns = [column["name"] for column in inspector.get_columns("news")]
    if "image_path" not in news_columns:
        db.session.execute(text('ALTER TABLE "news" ADD COLUMN image_path VARCHAR(255)'))
        db.session.commit()

    if "video_path" not in news_columns:
        db.session.execute(text('ALTER TABLE "news" ADD COLUMN video_path VARCHAR(255)'))
        db.session.commit()

    post_columns = [column["name"] for column in inspector.get_columns("post")]
    if "image_path" not in post_columns:
        db.session.execute(text('ALTER TABLE "post" ADD COLUMN image_path VARCHAR(255)'))
        db.session.commit()

    if "video_path" not in post_columns:
        db.session.execute(text('ALTER TABLE "post" ADD COLUMN video_path VARCHAR(255)'))
        db.session.commit()


with app.app_context():
    db.create_all()
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    ensure_legacy_schema_updates()


@app.route("/")
def index():
    current_user = _get_current_user()
    if current_user is None:
        return redirect(url_for("login"))

    all_posts = Post.query.order_by(Post.created_at.desc()).all()
    all_news = News.query.order_by(News.created_at.desc()).limit(20).all()
    return render_template(
        "index.html",
        user=current_user,
        posts=all_posts,
        ynov_news_list=all_news,
        serialized_posts=[_post_to_dict(item, current_user.id) for item in all_posts],
    )


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
    current_user = _get_current_user()
    if current_user is None:
        return redirect(url_for("login"))

    if not current_user.is_admin:
        flash("Seuls les comptes admin peuvent publier des news Ynov.")
        return redirect(url_for("index"))

    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()

    if not title or not content:
        flash("Titre et contenu obligatoires pour une news Ynov.")
        return redirect(url_for("index"))

    news_item = News(title=title, content=content, author_id=current_user.id)
    db.session.add(news_item)
    db.session.commit()
    flash("News Ynov publiee.")
    return redirect(url_for("index"))


@app.route("/posts", methods=["POST"])
def add_post():
    current_user = _get_current_user()
    if current_user is None:
        return redirect(url_for("login"))

    content = (request.form.get("content") or "").strip()
    image_file = request.files.get("image")
    video_file = request.files.get("video")

    image_path = _save_media_file(image_file, ALLOWED_IMAGE_EXTENSIONS, "images")
    video_path = _save_media_file(video_file, ALLOWED_VIDEO_EXTENSIONS, "videos")

    if image_file and image_file.filename and image_path is None:
        flash("Format d'image non supporte.")
        return redirect(url_for("index"))

    if video_file and video_file.filename and video_path is None:
        flash("Format de video non supporte.")
        return redirect(url_for("index"))

    if not content and not image_path and not video_path:
        flash("Ajoute du texte, une image ou une video pour publier.")
        return redirect(url_for("index"))

    post_item = Post(
        content=content,
        image_path=image_path,
        video_path=video_path,
        author_id=current_user.id,
    )
    db.session.add(post_item)
    db.session.commit()
    flash("Post publie.")
    return redirect(url_for("index"))


@app.route("/posts/<int:post_id>/like", methods=["POST"])
def toggle_post_like(post_id: int):
    current_user = _get_current_user()
    if current_user is None:
        return redirect(url_for("login"))

    post_item = db.session.get(Post, post_id)
    if post_item is None:
        flash("Post introuvable.")
        return redirect(url_for("index"))

    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        db.session.add(PostLike(post_id=post_id, user_id=current_user.id))

    db.session.commit()
    return redirect(url_for("index"))


@app.route("/posts/<int:post_id>/comments", methods=["POST"])
def add_post_comment(post_id: int):
    current_user = _get_current_user()
    if current_user is None:
        return redirect(url_for("login"))

    post_item = db.session.get(Post, post_id)
    if post_item is None:
        flash("Post introuvable.")
        return redirect(url_for("index"))

    content = (request.form.get("comment") or "").strip()
    if not content:
        flash("Le commentaire ne peut pas etre vide.")
        return redirect(url_for("index"))

    db.session.add(PostComment(post_id=post_id, user_id=current_user.id, content=content))
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/api/feed")
def feed_updates():
    current_user = _get_current_user()
    if current_user is None:
        return jsonify({"items": []}), 401

    after_id_raw = request.args.get("after_id", "0")
    try:
        after_id = max(int(after_id_raw), 0)
    except ValueError:
        after_id = 0

    new_items = (
        Post.query.filter(Post.id > after_id)
        .order_by(Post.created_at.asc())
        .all()
    )
    return jsonify({"items": [_post_to_dict(item, current_user.id) for item in new_items]})


if __name__ == "__main__":
    app.run(debug=True)
