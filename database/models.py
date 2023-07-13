from sqlalchemy import Column, VARCHAR, BIGINT, BOOLEAN
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'Users'

    id = Column(BIGINT, primary_key=True)
    full_name = Column(VARCHAR())
    photo_url = Column(VARCHAR())


class Channels(Base):
    __tablename__ = "Channels"

    id = Column(BIGINT, primary_key=True)
    name = Column(VARCHAR())
    url = Column(VARCHAR())
    public = Column(BOOLEAN())
    photo_url = Column(VARCHAR())


class UserChannels(Base):
    __tablename__ = "UserChannels"

    user_id = Column(BIGINT(), primary_key=True)
    channel_id = Column(BIGINT(), primary_key=True)
    role_id = Column(BIGINT())


class Roles(Base):
    __tablename__ = "Roles"

    id = Column(BIGINT(), primary_key=True)
    name = Column(VARCHAR())
