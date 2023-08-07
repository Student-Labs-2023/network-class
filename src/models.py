from sqlalchemy import Column, BIGINT, VARCHAR, BOOLEAN
from src.database import Base


class Channels(Base):
    __tablename__ = "channels"

    id = Column(BIGINT, primary_key=True)
    title = Column(VARCHAR())
    url = Column(VARCHAR())
    photo_url = Column(VARCHAR())
    isActive = Column(BOOLEAN())
    isPublic = Column(BOOLEAN())

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class UserChannels(Base):
    __tablename__ = "user_channels"

    user_id = Column(BIGINT(), primary_key=True)
    channel_id = Column(BIGINT(), primary_key=True)
    role_id = Column(BIGINT())


class User(Base):
    __tablename__ = "users"

    id = Column(BIGINT(), primary_key=True)
    full_name = Column(VARCHAR(), nullable=False)
    email = Column(VARCHAR())
    photo_url = Column(VARCHAR())


class Role(Base):
    __tablename__ = "roles"

    id = Column(BIGINT(), primary_key=True)
    name = Column(VARCHAR())
