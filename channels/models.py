from database.database import db


class Channels(db.Model):
    id = db.Column(db.BIGINT, primary_key=True)
    name = db.Column(db.VARCHAR())
    url = db.Column(db.VARCHAR())
    public = db.Column(db.BOOLEAN())
    photo_url = db.Column(db.VARCHAR())

    def create(self):
        db.session.add(self)
        db.session.commit()


class UserChannels(db.Model):
    user_id = db.Column(db.BIGINT(), primary_key=True)
    channel_id = db.Column(db.BIGINT(), primary_key=True)
    role_id = db.Column(db.BIGINT())

    def create(self):
        db.session.add(self)
        db.session.commit()
