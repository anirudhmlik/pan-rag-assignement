# app/init_db.py

from app.models.metadata import Base
from sqlalchemy import create_engine

# Use the same DB path as in your app config
DATABASE_URL = "sqlite:///./vector_db/chroma.sqlite3"
engine = create_engine(DATABASE_URL)

def create_tables():
    print("[Init] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[Init] Tables created.")

if __name__ == "__main__":
    create_tables()