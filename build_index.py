from __future__ import annotations

import pickle
import faiss
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

INDEX_FILE = "xkcd.index"
META_FILE = "meta.pkl"

# --- Build / load index ---
def build_index():
    print("Building FAISS index...")
    ds = load_dataset("olivierdehaene/xkcd", split="train")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = []
    for ex in ds:
        title = ex["title"] if ex["title"] else ""
        transcript = ex["transcript"] if ex["transcript"] else ""
        explanation = (
            ex["explanation"] if "explanation" in ex and ex["explanation"] else ""
        )
        texts.append(f"{title} {transcript} {explanation}")

    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, INDEX_FILE)

    # Store just the metadata we need (pickle-friendly)
    meta = [
        {
            "id": ex["id"],
            "title": ex["title"],
            "transcript": ex["transcript"],
            "explanation": ex["explanation"] if "explanation" in ex else "",
        }
        for ex in ds
    ]
    with open(META_FILE, "wb") as f:
        pickle.dump(meta, f)

    return index, meta

build_index()