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

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
