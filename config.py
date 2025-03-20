import os


class Config:
    SECRET_KEY = "mysecretkey"
    SQLALCHEMY_DATABASE_URI = "sqlite:///financial_system.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
