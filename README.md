# Setup du projet (Windows)

## 1) Créer et activer un environnement virtuel

```powershell
py -m venv .venv
```

## 2) Installer tous les packages nécessaires

```powershell
pip install Flask Flask-SQLAlchemy SQLAlchemy python-dotenv google-generativeai
```

Packages utilisés dans le projet :
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- python-dotenv
- google-generativeai

## 2.1) Configurer la clé API Gemini

Créer un fichier `.env` à la racine du projet avec :

```env
GEMINI_API_KEY=ta_cle_api_gemini
GEMINI_MODEL=gemini-2.5-flash
```

## 3) Lancer l'application web

```powershell
py app.py
```

Puis ouvrir le lien local affiché dans le terminal.
