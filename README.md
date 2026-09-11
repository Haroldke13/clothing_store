# clothing_store

A Flask + MongoDB inventory and point-of-sale app for a clothing/uniform shop: stock management,
a shopping cart, sales and purchase tracking, staff salaries and trading licences.

Live demo (Render, may be asleep or offline): <https://clothing-store-j0ua.onrender.com/>

## What it does

All routes live in `app/routes.py` (one `main` blueprint, ~390 lines):

| Route | Purpose |
| --- | --- |
| `/` | Landing page |
| `/inventory_management` | List, add and edit stock items, including image upload |
| `/api/inventory` | JSON dump of all inventory items |
| `/add_to_cart`, `/view_cart`, `/remove_from_cart/<item_id>`, `/cancel_order` | Session cart |
| `/checkout` | Completes a purchase and decrements stock |
| `/sales_tracking`, `/buy_tracking` | History of sales and of purchases |
| `/salaries` | Record and list employee salaries |
| `/licenses`, `/add_license`, `/edit_license/<id>`, `/delete_license/<id>` | Trading-licence CRUD |
| `/login`, `/sign_up`, `/logout`, `/user_profile` | Accounts |
| `/about_us`, `/contact_us` | Static pages |

Authentication is hand-rolled on top of the Flask session (`session['user']`); passwords are hashed
with Werkzeug. There is no Flask-Login and no enforced role separation in the routes — the README
previously claimed an admin/user split, but nothing in `routes.py` checks a role.

## Tech stack

- Python 3, Flask 3.1 (application factory in `app/__init__.py`)
- MongoDB via PyMongo — see `app/db.py` for the collections
  (`users`, `inventory`, `sales_tracking`, `buy_tracking`, `salaries`, `licenses`, `cart`)
- Flask-Session (filesystem sessions, stored in `flask_session_data/`)
- Flask-WTF + WTForms for the login/signup forms, Werkzeug for password hashing
- Jinja2 templates in `app/templates/`, images in `app/static/images/`
- Gunicorn for deployment

## Setup

```bash
git clone https://github.com/Haroldke13/clothing_store.git
cd clothing_store
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Database configuration — read this before running

`config.py` reads `MONGO_URI` from the environment, **but `app/db.py` ignores it** and opens its own
`MongoClient` against a connection string hardcoded at the top of the file. To point the app at your
own database you must edit `app/db.py` (or refactor it to use `config.Config.MONGO_URI`).

Set a real secret key too — `app/__init__.py` overrides `Config.SECRET_KEY` with a hardcoded
`app.secret_key = '<set SECRET_KEY in .env - value intentionally not documented>'`.

### Run

```bash
python app.py            # or: flask --app app:app run --debug
```

Then open <http://127.0.0.1:5000>.

## Security

⚠️ `app/db.py` contains a **hardcoded MongoDB Atlas connection string with inline credentials** for a
real cluster. Rotate that database user and move the URI into an environment variable before doing
anything else with this repo. There is no `.gitignore`.

## Status

**Working prototype, feature-complete for its scope.** Last touched February 2025. Runs locally and
has been deployed to Render. Rough edges: no role enforcement, no tests, no input validation beyond
the two WTForms, and the DB connection string is not configurable without editing source.

## Licence

The `LICENSE` file in this repo is **GPL-3.0**, not MIT — an earlier version of this README said MIT.
Treat `LICENSE` as authoritative, or replace it if MIT was the intent.
