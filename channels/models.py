from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Channels(db.Model):
    id = db.Column(db.BIGINT, primary_key=True)
    name = db.Column(db.VARCHAR())
    url = db.Column(db.VARCHAR())
    public = db.Column(db.BOOLEAN())
    photo_url = db.Column(db.VARCHAR())
