from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import create_db
from app.routers import ingest, facts, links, showcase, documents
from app.config import DEMO_MODE, ALLOWED_ORIGINS, LLM_PROVIDER, OPENAI_COMPAT_MODEL

app = FastAPI(
    title='ClaimsMap — Fact Knowledge Layer',
    description='Extract, link, and verify claims across multiple PDF documents.',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
    return {
        'status': 'ok',
        'demo_mode': DEMO_MODE,
        'llm_provider': LLM_PROVIDER,
        'model': OPENAI_COMPAT_MODEL if LLM_PROVIDER == 'openai_compat' else 'gemini-1.5-pro',
    }
