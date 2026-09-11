# Deploying `clothing_store`

Flask + MongoDB shop: inventory, cart, sales/buy tracking, salaries, licences,
and an admin area gated on `session['user_email'] == 'admin@admin.com'`.

| Fact | Value |
|---|---|
| WSGI entrypoint | `deploy_wsgi:app` (calls `create_app()`, adds `/healthz`) |
| Listens on | `5758` inside the container |
| Suggested hostname | `shop.harolditdata.uk` |
| Persistent state | MongoDB (external) + two volumes, see below |
| Already deployed | yes — this repo also runs on Render |

---

## 1. BLOCKER — read this before pointing DNS at it

`app/db.py` opens the database connection at import time against a **hardcoded
URI**:

```python
connection_string = "mongodb+srv://test:test@chatroom.<cluster>.mongodb.net/"
client = MongoClient(connection_string)
```

Consequences:

1. `MONGO_URI` in `config.py` is dead code. Nothing reads it — `PyMongo` is
   imported in `app/__init__.py` but never instantiated, and every route imports
   its collections straight from `app/db.py`.
2. The credentials are `test:test` on a shared Atlas cluster, committed to a
   public repo. Anyone who has ever read this repo can read and write your
   inventory, users and cart collections.
3. A container built from this Dockerfile will connect to that cluster.

**This cannot be fixed from a new file** — the client is constructed at module
import, before any deployment shim can intervene. It needs a one-line source
change (the concurrent security pass may already have made it):

```python
import os
connection_string = os.environ["MONGO_URI"]   # fail loudly if unset
```

Then rotate the Atlas credentials, because the old ones are burned.

Until that lands: build and test locally, but do not add the DNS record.

## 2. Environment variables

| Variable | Required | Default | Read by | Notes |
|---|---|---|---|---|
| `MONGO_URI` | **Yes** (after the fix above) | `config.py` falls back to the literal string `'your_mongodb_atlas_connection_string'` | `config.py` — **currently unused**, see section 1 | Full `mongodb+srv://…` connection string. The app uses database `mydatabase` and collections `users`, `inventory`, `sales_tracking`, `buy_tracking`, `salaries`, `licenses`, `cart`. |
| `SECRET_KEY` | **Yes, in production** | `'<set SECRET_KEY in .env - value intentionally not documented>'` (hardcoded in `app/__init__.py`) | `config.py` and re-applied by `deploy_wsgi.py` | Signs session cookies **and** the Flask-Session signer. Setting the env var alone does nothing, because `create_app()` assigns the literal *after* `from_object(Config)`; `deploy_wsgi.py` re-applies it afterwards. Rotate it — the current value is public, and with it anyone can forge a session cookie for `admin@admin.com` and own the admin area. |
| `PORT` | No | `5758` | `Procfile` only | Dockerfile binds 5758 unconditionally. |

No payment, mail or third-party API keys are used anywhere in this codebase.

## 3. Build and run

```bash
docker build -t clothing-store:latest .

docker volume create clothing_store_sessions
docker volume create clothing_store_images

docker run -d --name clothing-store \
  --restart unless-stopped \
  -v clothing_store_sessions:/app/flask_session_data \
  -v clothing_store_images:/app/app/static/images \
  -p 127.0.0.1:5758:5758 \
  --env-file /etc/harold/clothing-store.env \
  --memory 400m --cpus 0.5 \
  clothing-store:latest
```

The image ships the repo's existing product images inside
`/app/app/static/images`; mounting a volume over that path **hides them**. If
you want both, either seed the volume once
(`docker cp` from a throwaway container) or drop the second `-v` and accept that
newly uploaded product images are lost on redeploy.

This container is **not** run `--read-only`: Flask-Session writes session files
and the admin image upload writes into the static tree.

## 4. Health check

`GET /healthz` → `{"status": "ok"}`. Added by `deploy_wsgi.py`; no existing file
was modified. It deliberately does not ping MongoDB, so a database outage
restarts nothing.

## 5. Other things found while reading the code

- Uploads **are** sanitised (`secure_filename` in `app/routes.py`) and the
  extension allow-list is `png/jpg/jpeg/gif`. Good.
- Passwords are stored with `werkzeug.security.generate_password_hash`. Good.
- Admin is identified by a hardcoded email string, not a role field. Anyone who
  registers with `admin@admin.com` becomes admin — check whether that account
  already exists in the cluster before exposing this.
- `Session(app)` is called twice in `create_app()`, and `SESSION_FILE_DIR` /
  `SESSION_USE_SIGNER` are set *after* the first call. Harmless in practice, but
  it means the first initialisation used the default session directory.
- Sessions are filesystem-backed, so you cannot scale this app to a second host
  without switching to a shared session backend.

## 6. Cloudflare tunnel

```yaml
  - hostname: shop.harolditdata.uk
    service: http://localhost:5758
```

Full config in `/home/onyango/Projects/DEPLOYMENT_PLAN.md`.

## 7. Files added by the deployment pass

`Dockerfile`, `.dockerignore`, `Procfile`, `deploy_wsgi.py`, `DEPLOY.md`.
No existing file was modified; `requirements.txt` already lists gunicorn and is
used as-is.
