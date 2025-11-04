// embeddings/index.js
import fs from "fs";
import path from "path";
import { SentenceTransformer } from "sentence-transformers";
import faiss from "faiss-node";

const model = new SentenceTransformer("all-MiniLM-L6-v2");
const STORE_PATH = path.resolve("./embeddings/memoryStore.json");

let index = new faiss.IndexFlatL2(384); // 384 dims for all-MiniLM-L6-v2
let memory = [];

if (fs.existsSync(STORE_PATH)) {
  const data = JSON.parse(fs.readFileSync(STORE_PATH, "utf8"));
  if (data.vectors?.length) {
    const vectors = Float32Array.from(data.vectors.flat());
    index = new faiss.IndexFlatL2(384);
    index.add(vectors);
    memory = data.items;
  }
}

export async function addMemory(text, meta = {}) {
  const embedding = await model.encode([text]);
  index.add(embedding);
  memory.push({ text, meta });
  persist();
}

export async function searchMemory(query, k = 3) {
  const qEmbed = await model.encode([query]);
  const [distances, ids] = index.search(qEmbed, k);

  return ids[0]
    .map((id, i) => ({
      item: memory[id],
      score: distances[0][i]
    }))
    .filter(x => x.item);
}

function persist() {
  const vectors = [];
  for (let i = 0; i < index.ntotal; i++) {
    const v = new Float32Array(384);
    index.reconstruct(i, v);
    vectors.push(Array.from(v));
  }
  fs.writeFileSync(STORE_PATH, JSON.stringify({ items: memory, vectors }));
}
