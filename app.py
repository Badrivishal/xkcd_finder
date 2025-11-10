from __future__ import annotations

import os
import pickle
import faiss
import gradio as gr
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient
from prometheus_helper import PrometheusHelper
# --- Credit ---
# Most of this code was generated using AI (ChatGPT, GitHub Copilot). 
# Please refer to the references of the report for concrete links to the respective AI interactions.

# --- Config ---
INDEX_FILE = "xkcd.index"
META_FILE = "meta.pkl"
CHAT_MODEL = os.getenv("CHAT_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
prometheus_helper = PrometheusHelper()

# --- Build / load index ---
def build_index():
    prometheus_helper.start_index_build_timer()
    print("Building FAISS index...")
    ds = load_dataset("olivierdehaene/xkcd", split="train")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = []
    for ex in ds:
        title = ex["title"] if ex["title"] else ""
        transcript = ex["transcript"] if ex["transcript"] else ""
        explanation = ex["explanation"] if "explanation" in ex and ex["explanation"] else ""
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

    prometheus_helper.stop_index_build_timer()
    return index, meta

def get_index():
    if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
        print("Loading cached index...")
        with open(META_FILE, "rb") as f:
            return faiss.read_index(INDEX_FILE), pickle.load(f)
    else:
        return build_index()
    
def get_id_from_string(str:str) -> str:
    id_start = str.index("[") +1
    id_end = str.index("]")
    return str[id_start:id_end]

# --- Chat handler ---
def respond(
    message: str,
    history: list[dict[str, str]],
    oauth: gr.OAuthToken | None = None,  # Gradio injects this when available
):
    token = None
    if oauth and getattr(oauth, "token", None):
        token = oauth.token
    elif os.getenv("HF_TOKEN"):
        token = os.getenv("HF_TOKEN")
    else:
        return "⚠️ Please sign in with your Hugging Face account (top of the page) or set the HF_TOKEN environment variable"

    prometheus_helper.start_request_timer()
    # Embed the query and search FAISS
    prometheus_helper.start_faiss_index_search_timer()
    query_vec = embedder.encode([message], convert_to_numpy=True)
    D, I = index.search(query_vec, 5)
    candidates = [meta[int(i)] for i in I[0]]

    prometheus_helper.stop_faiss_index_search_timer()
    prometheus_helper.start_chat_model_call_timer()

    context = "\n".join(
        f"[{c['id']}] {c['title']}\nTranscript: {c['transcript']}\nExplanation: {c['explanation']}"
        for c in candidates
    )
    prompt = f"""Situation: "{message}"
Here are candidate xkcd comics:
{context}

Which comic fits best and why?
Please answer with the comic ID, URL (https://xkcd.com/ID/) and a short explanation in the format:

[ID] URL

EXPLANATION
"""

    print("[PROMPT] " + prompt)
    client = InferenceClient(model=CHAT_MODEL, api_key=token)  # 'api_key' alias also works
    resp = client.chat_completion(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that selects the most suitable xkcd comic."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        temperature=0.0, # TODO
    )

    prometheus_helper.stop_chat_model_call_timer()

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

    out_text = out.strip() or "Sorry, I couldn't parse the model response."

    if out_text != "Sorry, I couldn't parse the model response.":
        try:
            id = get_id_from_string(out_text)
            print(f'Read ID: {id}')
            
            import urllib.request, json
            with urllib.request.urlopen(f'https://xkcd.com/{id}/info.0.json') as url:
                img_url = json.load(url)["img"]
                print(f'Got image url: {img_url}')
            
            prometheus_helper.record_frequency(int(id))
            return [out_text, gr.Image(value=img_url)]
        except ValueError:
            print("Couldn't parse xkcd ID or get image! That should not happen.")
    prometheus_helper.record_request(True)
    prometheus_helper.stop_request_timer()
    return out_text

if __name__ == "__main__":
    # --- UI ---
    prometheus_helper.setup_prometheus()
    with gr.Blocks(theme='gstaff/xkcd') as demo:
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
            type="messages",
        )
        global index
        global meta 
        index, meta = get_index()
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        demo.launch()
