from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Roles(db.Model):
    id = db.Column(db.BIGINT(), primary_key=True)
    name = db.Column(db.VARCHAR())
