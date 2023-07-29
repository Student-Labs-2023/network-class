from sqlalchemy import Column, VARCHAR, BIGINT, BOOLEAN
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Roles(Base):
    __tablename__ = "Roles"

    id = Column(BIGINT(), primary_key=True)
    name = Column(VARCHAR())
