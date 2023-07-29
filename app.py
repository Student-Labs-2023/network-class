from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# from validation.validator import validation
from channels.routes import channels

app.register_blueprint(channels)
# app.register_blueprint(validation)

if __name__ == '__main__':
    app.run()
