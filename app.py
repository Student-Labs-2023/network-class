from flask import Flask
from flask_migrate import Migrate

from database.database import db

app = Flask(__name__)

app.config.from_pyfile('config.py')
db.init_app(app=app)

migrate = Migrate(app, db)

# from validation.validator import validation
from channels.routes import channels

app.register_blueprint(channels)
# app.register_blueprint(validation)
with app.app_context():
    print(db.get_engine().engine)

if __name__ == '__main__':
    app.run()