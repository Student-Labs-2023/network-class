from database.database import db


class Users(db.Model):

    id = db.Column(db.BIGINT(), primary_key=True)
    full_name = db.Column(db.VARCHAR())
    photo_url = db.Column(db.VARCHAR())
