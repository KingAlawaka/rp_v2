""" from flask import Flask
import os
from src.auth import auth

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY"),
        )
    else:
        app.config.from_mapping(test_config)
    
    app.register_blueprint(auth)
    return app
 """