from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

from apps.monolith.api import routes
from .utils import filters

if __name__ == "__main__":
    app.run(host='0.0.0.0')

def create_app():

    return app
