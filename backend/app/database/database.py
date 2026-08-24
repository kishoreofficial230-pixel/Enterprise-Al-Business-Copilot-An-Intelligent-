import ssl

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=settings.DATABASE_USER,
    password=settings.DATABASE_PASSWORD,
    host=settings.DATABASE_HOST,
    port=settings.DATABASE_PORT,
    database=settings.DATABASE_NAME,
)


connect_args = {}

if settings.DATABASE_HOST not in {
    "127.0.0.1",
    "localhost",
}:
    connect_args["ssl"] = ssl.create_default_context()


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()