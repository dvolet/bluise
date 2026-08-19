import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    DATABASE_PATH = os.path.join(
        os.path.dirname(__file__),
        "database",
        "portfolio.db"
    )