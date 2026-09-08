# ClaimsMap — Cross-Document Fact Verification

> AI-Powered Fact Extraction, Evidence Grounding & Cross-Document Reconciliation

ClaimsMap extracts structured financial and policy claims from PDF documents, grounds every claim to an exact source quote, and reconciles claims across sources into corroborated facts, scope/methodology distinctions, or genuine contradictions.

Deployable standalone on **Vercel** with full pre-seeded data, or self-hosted with FastAPI.

---

## Setup and Run Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- A [Google Gemini API key](https://aistudio.google.com/) (free tier works)

### 1. Clone and configure
```bash
git clone <your-repo-url>
cd superjoin
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
```

### 2. Install dependencies
```bash
make install
```

### 3. Run (with Gemini API key)
```bash
make dev
# Backend → http://localhost:8000
# Frontend → http://localhost:3000
# API docs → http://localhost:8000/docs
```

### 4. Run in demo mode (no API key needed)
```bash
make seed     # Populate DB with pre-extracted showcase data
make demo     # Start servers in demo mode
```

### 5. Ingest the starter datasets
```bash
make ingest-starters   # Curl-uploads all 6 starter PDFs while servers are running
```

---

## Video Demo

**[📹 3-minute walkthrough — Link TBD]**

Covers:
1. Uploading a PDF and watching fact extraction
2. Browsing the fact table with filters
3. The 4 showcase cases with evidence and reasoning
4. Failure modes and their mitigations

---

## Approach

### Architecture

```
PDF Upload
  → Local text extraction (pdfplumber + PyMuPDF)   # Never sends raw PDF to LLM
  → 3-pass sanitization (negatives, footnotes, FY notation)
  → Section-aware chunking (512 tokens, 20% overlap)
  → Gemini 1.5 Pro extraction (text-only, structured JSON prompt)
  → Pydantic v2 validation + unit normalization
  → SQLite storage (SQLModel ORM)
  → Cross-document reconciliation (5-step deterministic rules)
  → Gemini Flash explanation generation
  → FastAPI REST API → Next.js frontend
```

### Key Decisions

**1. Local PDF parsing before any LLM call**
Raw PDF bytes are never sent to Gemini. `pdfplumber` provides coordinate-aware table extraction preserving column alignment. `PyMuPDF` serves as text fallback. This is architecturally correct and also avoids the `unsupported mime type application/pdf` error class.

**2. Deterministic reconciliation engine**
The classification of CORROBORATED / CONTRADICTION / RECONCILED is done by pure Python rules (5-step cascade), not by LLM. The LLM (Gemini Flash) only generates the human-readable explanation *after* the verdict is already determined. This makes the system auditable and reproducible.

**3. Zero hardcoded schemas**
`metric_name` is a free-form string derived entirely from document context by the LLM. No fixed enums, no regex rules specific to Delhivery or RBI. New document types produce new metric names automatically.

**4. Chunk-level caching**
Each text chunk is cached in SQLite by SHA256 hash. Re-uploading a document or re-running the pipeline never calls Gemini again for already-processed chunks.

**5. Incremental ingestion**
A new document is identified by SHA256(file bytes). If already in the DB, the API returns the cached result immediately. New facts from a new document are reconciled against all existing facts without rebuilding.

### The 5-Step Reconciliation Algorithm

```python
if value_delta <= 1.5% AND same_temporal AND same_scope:   → CORROBORATED
elif different temporal scopes:                             → RECONCILED_TEMPORAL
elif different accounting basis:                            → RECONCILED_SCOPE
elif different metric definitions:                          → RECONCILED_METHODOLOGY
elif value_delta > 5% with same T, S, M:                   → GENUINE_CONTRADICTION
```

### Sanitization Passes (Hardened against PDF quirks)

| Pass | Problem | Example | Fix |
| :--- | :--- | :--- | :--- |
| 1 | Parenthetical negatives | `(217)` → `217` (sign lost) | Regex: `\(N\)` → `-N` |
| 2 | Footnote contamination | `18,793(1)` → `187,931` | Strip trailing `(\d+)` from numbers |
| 3 | FY notation | `FY24 / FY2023-24 / FY2024/25` mixed | ISO interval mapper |

---

## Limitations and Next Steps

### Current Limitations
- **Table extraction quality**: `pdfplumber` table detection fails on some scanned PDFs or complex multi-column layouts. Fallback to PyMuPDF gives prose text only.
- **Gemini cost**: Processing 100-page PDFs costs ~$0.05-0.15 per document at current Gemini 1.5 Pro pricing. Demo mode avoids this.
- **Entity resolution**: `rapidfuzz` fuzzy matching works well but may miss highly abbreviated entity names not seen in training data.
- **No PDF rendering**: Verbatim quotes are text-only; no PDF page image viewer in the UI.
- **ChromaDB not integrated**: Semantic search over facts is scaffolded but not activated in this version.

### What I Would Build Next
1. **PDF page renderer**: Embed PDF.js to highlight the verbatim quote within the actual PDF page for maximum evaluator trust.
2. **Semantic search**: Activate ChromaDB embeddings so evaluators can query "all facts about GDP growth" across all documents.
3. **Streaming ingestion**: Use Server-Sent Events for real-time progress as each page is processed.
4. **Confidence calibration**: Train a lightweight classifier on (entity similarity, metric similarity, delta, scope match) → relation_type, replacing the hardcoded thresholds.

---

## Additional Notes

- `data/sample_facts.db` is committed to the repository. Running `make demo` immediately serves the 4 showcase cases without any API key.
- `brain.md` in the root is the full domain forensic knowledge base used to design and validate the system.
- The API has auto-generated docs at `http://localhost:8000/docs` (Swagger UI).
- All commits follow conventional commit format (`feat:`, `fix:`, `docs:`, etc.).

---

**Submit**: https://forms.gle/3fLdBQ2D6Zm2Gqtv7
