from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import create_db
from app.routers import ingest, facts, links, showcase, documents
from app.config import DEMO_MODE, ALLOWED_ORIGINS, LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_BASE_URL, OPENAI_COMPAT_MODEL, OPENAI_COMPAT_BASE_URL

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
    import httpx
    ollama_online = False
    if LLM_PROVIDER == 'ollama':
        try:
            r = httpx.get(f'{OLLAMA_BASE_URL}/api/tags', timeout=1.5)
            ollama_online = r.status_code == 200
        except Exception:
            ollama_online = False
    return {
        'status': 'ok',
        'demo_mode': DEMO_MODE,
        'llm_provider': LLM_PROVIDER,
        'model': (
            OPENAI_COMPAT_MODEL if LLM_PROVIDER == 'openai_compat'
            else OLLAMA_MODEL if LLM_PROVIDER == 'ollama'
            else 'gemini-1.5-pro'
        ),
        'ollama_online': ollama_online if LLM_PROVIDER == 'ollama' else None,
    }
