from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
from app.config import SQLITE_DB_PATH

Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}", echo=False, connect_args={"check_same_thread": False})

def create_db():
    SQLModel.metadata.create_all(engine)
    # Lightweight SQLite column migration for existing tables
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(facts)")).fetchall()
            existing_cols = {row[1] for row in res}
            cols_to_add = [
                ("file_hash", "TEXT DEFAULT ''"),
                ("chunk_hash", "TEXT DEFAULT ''"),
                ("extractor_model", "TEXT DEFAULT 'gemini-1.5-pro'"),
                ("prompt_version", "TEXT DEFAULT 'v2.1'"),
                ("grounding_verified", "BOOLEAN DEFAULT 1"),
            ]
            for col_name, col_type in cols_to_add:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE facts ADD COLUMN {col_name} {col_type}"))
            conn.commit()
        except Exception:
            pass


def get_session():
    with Session(engine) as session:
        yield session
