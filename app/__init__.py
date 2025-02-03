from flask import Flask
from flask_pymongo import PyMongo
from config import Config
from flask_session import Session


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.secret_key = 'clothing_store_secret_key'
    app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions on the filesystem

    Session(app)  # Initialize session handling

    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_FILE_DIR'] = 'flask_session_data'  # Store sessions in a folder

    Session(app)  # Initialize session handling

    from app.routes import main
    app.register_blueprint(main)

    return app
