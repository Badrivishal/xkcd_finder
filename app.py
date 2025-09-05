from __future__ import annotations

import os
import pickle
import faiss
import gradio as gr
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient

# --- Config ---
INDEX_FILE = "xkcd.index"
META_FILE = "meta.pkl"
CHAT_MODEL = os.getenv("CHAT_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")

# --- Build / load index ---
def build_index():
    print("Building FAISS index...")
    ds = load_dataset("olivierdehaene/xkcd", split="train")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = []
    for ex in ds:
        id_ = str(ex["id"]) if ex["id"] else ""
        title = ex["title"] if ex["title"] else ""
        transcript = ex["transcript"] if ex["transcript"] else ""
        explanation = ex["explanation"] if "explanation" in ex and ex["explanation"] else ""
        texts.append(f"{id_} {title} {transcript} {explanation}")

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

if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
    print("Loading cached index...")
    index = faiss.read_index(INDEX_FILE)
    with open(META_FILE, "rb") as f:
        meta = pickle.load(f)
else:
    index, meta = build_index()

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# --- Chat handler ---
def respond(
    message: str,
    history: list[dict[str, str]],
    oauth: gr.OAuthToken | None = None,  # Gradio injects this when available
):
    if not oauth:
        yield "⚠️ Please sign in with your Hugging Face account (top of the page)"
        return
    token = oauth.token

    # Embed the query and search FAISS
    query_vec = embedder.encode([message], convert_to_numpy=True)
    D, I = index.search(query_vec, 5)
    candidates = [meta[int(i)] for i in I[0]]

    context = "\n".join(
        f"[{c['id']}] {c['title']}\nTranscript: {c['transcript']}\nExplanation: {c['explanation']}"
        for c in candidates
    )
    prompt = f"""Situation: "{message}"
Here are candidate xkcd comics:
{context}

Which comic fits best and why?
Please answer with the comic ID, URL (https://xkcd.com/ID/) and a short explanation.
"""

    print("[PROMPT] " + prompt)
    client = InferenceClient(model=CHAT_MODEL, api_key=token)  # 'api_key' alias also works
    resp = client.chat_completion(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that selects the most suitable xkcd comic."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        temperature=0.0,
    )

    # Be tolerant to slight schema differences
    try:
        choice = resp.choices[0]
        msg = getattr(choice, "message", None)
        if isinstance(msg, dict):
            out = msg.get("content", "")
        else:
            out = getattr(msg, "content", "") or getattr(choice, "text", "")
    except Exception:
        out = str(resp)

    yield out.strip() or "Sorry, I couldn't parse the model response."

# --- UI ---
with gr.Blocks() as demo:
    gr.Markdown("# xkcd Comic Finder")
    gr.Markdown(
        "Sign in with your Hugging Face account so the app can call the model via the Inference API."
        "\n\n> If you deploy to a Space, add `hf_oauth: true` in your Space metadata and grant the `inference:api` scope."
    )
    gr.LoginButton()  # Shows “Sign in with Hugging Face”

    gr.ChatInterface(
        fn=respond,
        title="xkcd Comic Finder",
        description="Find the most suitable xkcd comic for your situation. Use the login button above.",
        examples=[
            "I need a comic about procrastination.",
            "A comic for programmers debugging code.",
            "Life advice in comic form.",
        ],
    )

if __name__ == "__main__":
    demo.launch()
