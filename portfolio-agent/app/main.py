from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import ValidationError
from pathlib import Path
import json
from string import Template
import tempfile
import zipfile

from .models import UpsertRequest, SearchRequest, GenRequest, GeneratedSite
from .embeddings import EmbeddingStore
from .llm import call_llama_cpp, extract_json
from .sanitize import sanitize_html

# Config
MODEL_PATH = "models/your-model.gguf"  # set to None to use fallback_generate in llm.py
PROMPT_PATH = Path("prompts/system_prompt.txt")

app = FastAPI(title="Portfolio AI Agent (Open Source)")

emb_store = EmbeddingStore()

def load_prompt_template() -> Template:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    return Template(text)

PROMPT_TEMPLATE = load_prompt_template()

@app.post("/upsert")
def upsert(req: UpsertRequest):
    return emb_store.upsert(req.id, req.text, req.meta)

@app.post("/search")
def search(req: SearchRequest):
    return {"results": emb_store.search(req.q, req.k)}

@app.post("/generate")
def generate(req: GenRequest):
    # build prompt
    sections_str = ", ".join(req.sections)
    prompt = PROMPT_TEMPLATE.substitute(
        name=req.name,
        role=req.role,
        color=req.color,
        sections=sections_str,
        style=req.style,
        extra=req.extra
    )
    # call LLM
    raw_out = call_llama_cpp(prompt, model_path=MODEL_PATH, max_tokens=req.max_tokens)
    if raw_out is None:
        raise HTTPException(status_code=500, detail="No output from LLM runtime")

    # If the runtime returned text that contains JSON, extract
    js_text = extract_json(raw_out) or raw_out

    try:
        parsed = json.loads(js_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse JSON from model output: {e}\nRaw output: {raw_out[:1000]}")

    # Validate shape with pydantic
    try:
        site = GeneratedSite(**parsed)
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=f"Schema validation error: {e}")

    # Sanitize HTML content
    for f in site.files:
        if f.path.endswith(".html"):
            f.content = sanitize_html(f.content)

    # Optionally, store generated site to a temp zip for download
    tmpdir = Path(tempfile.mkdtemp())
    for f in site.files:
        outp = tmpdir / f.path
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(f.content, encoding="utf-8")

    zip_path = tmpdir / "site.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in site.files:
            z.write(tmpdir / f.path, arcname=f.path)

    # Return metadata + download path (note: FileResponse needs an absolute path)
    return JSONResponse({"meta": site.meta, "accessibility_issues": site.accessibility_issues, "download": str(zip_path)})

@app.get("/download")
def download(path: str):
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(p), media_type="application/zip", filename=p.name)
