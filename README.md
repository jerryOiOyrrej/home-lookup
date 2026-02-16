# 🏠 Marseille Immo

Recherche d'appartement à Marseille — Jerry & JoC

## Stack

- **Backend** : FastAPI + SQLite (SQLModel)
- **Frontend** : Jinja2 + TailwindCSS + Alpine.js
- **Auth** : Pocket ID (OIDC) + API Key
- **Deploy** : Docker / Coolify

## Variables d'environnement

| Variable | Description | Requis |
|----------|-------------|--------|
| `DATABASE_URL` | URL SQLite | Non (défaut: `sqlite:///data/immo.db`) |
| `OIDC_ISSUER` | URL Pocket ID | Oui |
| `OIDC_CLIENT_ID` | Client ID OIDC | Oui |
| `OIDC_CLIENT_SECRET` | Client Secret OIDC | Oui |
| `APP_URL` | URL publique de l'app | Oui |
| `SESSION_SECRET` | Secret pour les sessions | Oui |
| `API_KEY` | Clé API pour accès programmatique | Oui |

## Dev local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## API

- `GET /api/annonces` — Liste avec filtres
- `POST /api/annonces` — Créer (auth requise)
- `PATCH /api/annonces/{id}` — Modifier (auth requise)
- `DELETE /api/annonces/{id}` — Supprimer (auth requise)
- `GET /api/stats` — Statistiques
- `GET /health` — Health check
