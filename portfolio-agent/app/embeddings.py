import numpy as np
from pathlib import Path
import pickle

class EmbeddingStore:
    def __init__(self, model_name="all-MiniLM-L6-v2", index_path="data/faiss.index", meta_path="data/meta.pkl"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)
        self._ensure_data_dir()
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "rb") as f:
                self.meta = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.meta = []

    def _ensure_data_dir(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def upsert(self, id: str, text: str, meta: dict = {}):
        vec = self.model.encode([text], convert_to_numpy=True).astype("float32")
        self.index.add(vec)
        self.meta.append({"id": id, "meta": meta, "text": text})
        self._save()
        return {"ok": True, "total": self.index.ntotal}

    def search(self, q: str, k: int = 4):
        vec = self.model.encode([q], convert_to_numpy=True).astype("float32")
        D, I = self.index.search(vec, k)
        results = []
        for i, idx in enumerate(I[0]):
            if idx < len(self.meta):
                results.append({
                    "score": float(D[0][i]),
                    "item": self.meta[idx]
                })
        return results

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.meta, f)
