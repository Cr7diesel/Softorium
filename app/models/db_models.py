from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.models.db_conf import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String(255))


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(255))
    amount = Column(Integer)
    user = relationship("User")
