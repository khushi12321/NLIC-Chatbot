import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "nlic_chatbot"),
)

engine = create_engine(database_url, pool_pre_ping=True)


def test_connection():
    with engine.connect() as connection:
        return connection.execute(text("SELECT version()")).scalar()