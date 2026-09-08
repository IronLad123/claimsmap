from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
from app.config import SQLITE_DB_PATH

Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}", echo=False, connect_args={"check_same_thread": False})

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
