from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import create_db
from app.routers import ingest, facts, links, showcase, documents
from app.config import DEMO_MODE

app = FastAPI(
    title='Superjoin — Fact Knowledge Layer',
    description='Extract, link, and explain facts across multiple PDF documents.',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def on_startup():
    create_db()


app.include_router(ingest.router)
app.include_router(facts.router)
app.include_router(links.router)
app.include_router(showcase.router)
app.include_router(documents.router)


@app.get('/api/health')
def health():
    return {'status': 'ok', 'demo_mode': DEMO_MODE}
