# 🎓 Ynov Social Network

Réseau social pour étudiants Ynov avec posts, actualités, messages privés et assistance IA Gemini.

---

## 📋 Résumé du projet

- **Type**: Application Web Flask
- **BD**: SQLite (`site.db`)
- **IA**: Google Gemini 
- **Principales fonctionnalités**:
  - Authentification (`@ynov.com` obligatoire)
  - Profil utilisateur (photo, bio, compétences)
  - Posts avec likes et commentaires
  - Actualités Ynov (News)
  - Messagerie privée
  - Support images/vidéos (max 30MB)

---

## 📁 Arborescence

```
Challenge-48h/
├── app.py                    # Routes et logique Flask
├── models.py                 # Modèles de données (User, Post, News, etc.)
├── .env                      # Variables d'environnement (À CRÉER)
│
├── ia/
│   ├── __init__.py
│   └── gemini_service.py     # Service API Gemini
│
├── templates/                # Pages HTML
│   ├── base.html             # Layout principal
│   ├── index.html, login.html, register.html
│   ├── profile.html, edit_profile.html
│   ├── messages.html, services.html
│   ├── contact.html, apropos.html
│
├── static/
│   ├── css/                  # Feuilles de style
│   │   ├── base.css, auth.css, dashboard.css
│   │   ├── profile.css, messages.css
│   └── uploads/              # Fichiers uploadés
│       ├── images/
│       └── profile_pictures/
│
└── instance/                 # Données (auto-créé)
```

---

## 🚀 Comment lancer le projet

### 1️⃣ Environnement virtuel

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2️⃣ Installer les dépendances

```powershell
pip install Flask Flask-SQLAlchemy SQLAlchemy python-dotenv google-generativeai
```

### 3️⃣ Créer `.env` à la racine

```env
GEMINI_API_KEY=votre_cle_api_ici
GEMINI_MODEL=gemini-2.5-flash
```

💡 Obtenez votre clé sur [Google AI Studio](https://aistudio.google.com)

### 4️⃣ Lancer l'app

```powershell
py app.py
```

Accédez à **http://localhost:5000**

---

## 📝 Notes importantes

- ✅ Premier utilisateur = Admin automatiquement
- ✅ Emails au format `@ynov.com`
- ✅ Mots de passe hashés
- ✅ DB créée automatiquement au premier lancement