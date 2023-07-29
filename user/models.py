from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UserChannels(db.Model):
    user_id = db.Column(db.BIGINT(), primary_key=True)
    channel_id = db.Column(db.BIGINT(), primary_key=True)
    role_id = db.Column(db.BIGINT())


class Users(db.Model):
    id = db.Column(db.BIGINT(), primary_key=True)
    full_name = db.Column(db.VARCHAR())
    photo_url = db.Column(db.VARCHAR())
