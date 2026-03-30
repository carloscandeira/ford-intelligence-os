"""Database connection management for Ford Intelligence OS."""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/ford_intelligence")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
SessionLocal = sessionmaker(bind=engine)


@contextmanager
def get_db():
    """Yield a database session, auto-closing on exit."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Run schema.sql to create all tables and indexes."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        schema_sql = f.read()

    with engine.connect() as conn:
        conn.execute(text(schema_sql))
        conn.commit()
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_db()
