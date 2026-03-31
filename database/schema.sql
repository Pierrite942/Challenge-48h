DROP TABLE IF EXISTS "news";
DROP TABLE IF EXISTS "post_comment";
DROP TABLE IF EXISTS "post_like";
DROP TABLE IF EXISTS "post";
DROP TABLE IF EXISTS "user";

CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "news" (
    id SERIAL PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    content TEXT NOT NULL,
    image_path VARCHAR(255),
    video_path VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    author_id INTEGER NOT NULL,
    CONSTRAINT fk_news_author FOREIGN KEY(author_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE "post" (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    image_path VARCHAR(255),
    video_path VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    author_id INTEGER NOT NULL,
    CONSTRAINT fk_post_author FOREIGN KEY(author_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE "post_like" (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post_like_post FOREIGN KEY(post_id) REFERENCES "post"(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_like_user FOREIGN KEY(user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    CONSTRAINT uq_post_like_post_user UNIQUE(post_id, user_id)
);

CREATE TABLE "post_comment" (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post_comment_post FOREIGN KEY(post_id) REFERENCES "post"(id) ON DELETE CASCADE,
    CONSTRAINT fk_post_comment_user FOREIGN KEY(user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_username ON "user" (username);
CREATE INDEX idx_news_created_at ON "news" (created_at DESC);
CREATE INDEX idx_post_created_at ON "post" (created_at DESC);
CREATE INDEX idx_post_comment_post_id ON "post_comment" (post_id);
