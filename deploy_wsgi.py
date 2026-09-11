"""Deployment entrypoint for clothing_store.

Additive only — app.py, config.py and app/__init__.py are untouched. It:

  * builds the app through the existing factory,
  * re-applies SECRET_KEY from the environment (create_app() overwrites
    Config.SECRET_KEY with a literal *after* loading the config object, so
    setting the env var alone has no effect),
  * registers a /healthz probe.

It cannot fix the MongoDB connection: app/db.py opens a MongoClient at import
time against a hardcoded URI. See DEPLOY.md section 1.

Run with:  gunicorn deploy_wsgi:app
"""

import os

from app import create_app  # noqa: E402  (the package factory)

app = create_app()

# app/__init__.py no longer hardcodes a secret key; Config supplies SECRET_KEY
# from the environment. Re-applied here so the WSGI entrypoint is explicit.
_secret = os.environ.get("SECRET_KEY")
if _secret:
    app.secret_key = _secret
    app.config["SECRET_KEY"] = _secret

if "healthz" not in app.view_functions:

    @app.route("/healthz")
    def healthz():
        """Liveness probe. Does not touch MongoDB on purpose: this answers
        'is the worker alive', not 'is the database reachable'."""
        return {"status": "ok"}, 200


if __name__ == "__main__":  # pragma: no cover - local smoke test only
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5758)))
