.PHONY: dev backend frontend seed test install

install:
	pip3 install -r backend/requirements.txt
	cd frontend && npm install

backend:
	cd backend && PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend on :8000 and frontend on :3000..."
	@trap 'kill 0' SIGINT; \
	(cd backend && PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

seed:
	cd backend && PYTHONPATH=. python3 scripts/seed_showcase.py

demo:
	@echo "Starting in DEMO MODE (no API key required)..."
	@trap 'kill 0' SIGINT; \
	(cd backend && DEMO_MODE=true PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

test:
	cd backend && PYTHONPATH=. python3 -m pytest tests/ -v --tb=short

ingest-starters:
	@echo "Ingesting all 6 starter PDFs..."
	for f in starter-datasets/delhivery/*.pdf starter-datasets/india-macroeconomy/*.pdf; do \
		curl -s -X POST http://localhost:8000/api/ingest \
			-F "file=@$$f" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['filename'], '->', d['fact_count'], 'facts')"; \
	done
