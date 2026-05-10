"""Script tao tat ca bang trong database.

Chay: python -m src.create_tables
"""
from sqlalchemy import text

from src.entities.base import Base

# Import tat ca entities de SQLAlchemy biet can tao bang nao
from src.entities.video import Video  # noqa: F401
from src.entities.frame import Frame  # noqa: F401

from src.repositories.conn import engine


def create_tables():
    print("Creating tables...")

    # Bat extension pgvector truoc khi tao bang
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    print("Done! Tables created:")
    for table_name in Base.metadata.tables:
        print(f"  - {table_name}")


if __name__ == "__main__":
    create_tables()
