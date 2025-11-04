# Quick run (local dev)

1. Create virtualenv and install deps:
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt

2. Place or build your llama.cpp model:
   - Option A (recommended): Convert a HF model to gguf and put at models/your-model.gguf and place llama.cpp 'main' binary alongside.
   - Option B: Set MODEL_PATH=None in app/main.py to use the fallback generator for testing.

3. Run FastAPI:
   uvicorn app.main:app --reload --port 8000

4. Example requests:
   - Upsert:
     curl -X POST "http://localhost:8000/upsert" -H "Content-Type: application/json" -d '{"id":"template-1","text":"A minimal black-and-white modern layout","meta":{}}'

   - Generate:
     curl -X POST "http://localhost:8000/generate" -H "Content-Type: application/json" -d '{
       "name":"Alysha",
       "role":"Data visualisation student",
       "color":"Black and White",
       "sections":["About Me","Contact","Projects"],
       "style":"Modern",
       "extra":"Keep fonts system-ui; no external libraries",
       "max_tokens":512
     }'

   The /generate endpoint will return a JSON object containing "download": "<path-to-zip>".
   Then call:
     http://localhost:8000/download?path=<path-to-zip>
