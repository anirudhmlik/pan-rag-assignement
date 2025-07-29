# app/purge_db.py

from app.db.database import SessionLocal
from app.db.models import Document, Chunk

def purge_all_data():
    session = SessionLocal()
    try:
        deleted_chunks = session.query(Chunk).delete()
        deleted_documents = session.query(Document).delete()
        session.commit()
        print(f"Deleted {deleted_chunks} chunks and {deleted_documents} documents from the database.")
    except Exception as e:
        session.rollback()
        print(f"Error during purge: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    purge_all_data()