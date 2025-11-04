import subprocess
import tempfile
import json
import re
from typing import Optional

def extract_json(text: str) -> Optional[str]:
    # Greedy extraction of the first {...} JSON block
    m = re.search(r"\{[\s\S]*\}", text)
    return m.group(0) if m else None

def call_llama_cpp(prompt: str, model_path: str = "models/your-model.gguf", max_tokens: int = 512, timeout: int = 120):
    """
    Calls llama.cpp main binary. Requires you to have compiled llama.cpp and have a GGUF model.
    Uses the --prompt-file option to avoid shell quoting issues.
    """
    # If you don't have llama.cpp, set model_path to None to use the fallback.
    if not model_path:
        return fallback_generate(prompt)

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
        f.write(prompt)
        f.flush()
        prompt_file = f.name

    cmd = [
        "./main",            # llama.cpp binary (adjust if different)
        "-m", model_path,
        "--prompt-file", prompt_file,
        "-n", str(max_tokens),
        "--temp", "0.1"      # low temperature for deterministic output
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"LLM runtime error: {proc.stderr}")
        out = proc.stdout
    finally:
        # don't remove prompt_file immediately if debugging; can unlink here if desired
        pass

    # try to extract JSON if model prepends explanation
    js = extract_json(out)
    return js or out

def fallback_generate(prompt: str):
    """
    Safe fallback for testing: returns a tiny example JSON rather than calling a real model.
    Use this when you don't have a local model yet.
    """
    example = {
        "meta": {"title": "Alysha | Data Visualisation", "desc": "Portfolio for Alysha"},
        "files": [
            {"path": "index.html", "content": "<!doctype html><html><head><meta charset='utf-8'><title>Alysha</title></head><body><main><h1>Alysha — Data Visualisation</h1><p>Projects...</p></main></body></html>"},
            {"path": "styles.css", "content": "body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #fff; color: #000 }"}
        ],
        "accessibility_issues": []
    }
    return json.dumps(example)
