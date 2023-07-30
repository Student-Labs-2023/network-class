from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS

from database.database import db

app = Flask(__name__)

cors = CORS(app, resources={r"/channels/*": {"origins": "*"}})

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
    app.run(host='0.0.0.0', port=5000)
