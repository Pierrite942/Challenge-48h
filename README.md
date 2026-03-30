## Installation

```powershell
python -m pip install -r requirements.txt
```

## PostgreSQL

Crée une base PostgreSQL, puis définis la variable d'environnement `DATABASE_URL` avant de lancer l'application.

Exemple:

```powershell
$env:DATABASE_URL="postgresql://postgres:motdepasse@localhost:5432/challenge_48h"
python app.py
```

## Utilisation

- Ouvre le site.
- Va sur la page Contact.
- Envoie un message pour l'enregistrer dans PostgreSQL.