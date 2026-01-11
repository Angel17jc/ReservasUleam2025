from sqlalchemy import create_engine, URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Build connection URL using individual parameters to avoid encoding issues
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=settings.DB_USERNAME,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME
)

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    echo=False,
    connect_args={
        "client_encoding": "utf8"
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Auth database (read-only for user validation)
auth_db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=settings.AUTH_DB_USERNAME,
    password=settings.AUTH_DB_PASSWORD,
    host=settings.AUTH_DB_HOST,
    port=settings.AUTH_DB_PORT,
    database=settings.AUTH_DB_NAME,
)

auth_engine = create_engine(
    auth_db_url,
    pool_pre_ping=True,
    echo=False,
    connect_args={"client_encoding": "utf8"},
)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()
