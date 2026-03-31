from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    training_year = db.Column(db.String(50), nullable=True)
    specialization = db.Column(db.String(255), nullable=True)
    skills = db.Column(db.Text, nullable=True)
    news_posts = db.relationship("News", backref="author", lazy=True)
    posts = db.relationship("Post", backref="author", lazy=True)
    post_likes = db.relationship("PostLike", backref="user", lazy=True)
    post_comments = db.relationship("PostComment", backref="user", lazy=True)
    sent_messages = db.relationship(
        "PrivateMessage",
        foreign_keys="PrivateMessage.sender_id",
        backref="sender",
        lazy=True,
        cascade="all, delete-orphan",
    )
    received_messages = db.relationship(
        "PrivateMessage",
        foreign_keys="PrivateMessage.recipient_id",
        backref="recipient",
        lazy=True,
        cascade="all, delete-orphan",
    )


class News(db.Model):
    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    video_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Post(db.Model):
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    video_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    likes = db.relationship("PostLike", backref="post", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship(
        "PostComment",
        backref="post",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="PostComment.created_at.asc()",
    )


class PostLike(db.Model):
    __tablename__ = "post_like"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_like_post_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class PostComment(db.Model):
    __tablename__ = "post_comment"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class PrivateMessage(db.Model):
    __tablename__ = "private_message"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)