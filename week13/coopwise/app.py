from __future__ import annotations

from pathlib import Path
import json
import shutil
import sqlite3
import re

# Hugging Face injects `spaces`; import it before CUDA-enabled ML packages
# so Gradio's reload watcher does not initialize CUDA in the wrong order.
try:
    import spaces  # noqa: F401
except ImportError:
    pass

import chromadb
import gradio as gr
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


PROJECT_DIR = Path(__file__).resolve().parent
CHROMADB_DIR = PROJECT_DIR / "chromadb"
COLLECTION_NAME = "coopwise_sources"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_search_resources():
    if not CHROMADB_DIR.exists():
        return None, None, "Index missing"
    try:
        sqlite_file = CHROMADB_DIR / "chroma.sqlite3"
        if sqlite_file.exists():
            with sqlite3.connect(sqlite_file) as probe:
                integrity = probe.execute("PRAGMA integrity_check").fetchone()
            print(
                f"CoopWise SQLite diagnostic: size={sqlite_file.stat().st_size} "
                f"integrity={integrity}",
                flush=True,
            )
        client = chromadb.PersistentClient(
            path=str(CHROMADB_DIR),
            settings=Settings(anonymized_telemetry=False, allow_reset=False),
        )
        collection = client.get_collection(COLLECTION_NAME)
        model = SentenceTransformer(MODEL_NAME)
        return model, collection, None
    except Exception as exc:
        print(
            f"CoopWise startup diagnostic: CHROMADB_DIR={CHROMADB_DIR} "
            f"exists={CHROMADB_DIR.exists()} exception={type(exc).__name__}: {exc}",
            flush=True,
        )
        try:
            if CHROMADB_DIR.exists():
                shutil.rmtree(CHROMADB_DIR)
            from build_index import main as rebuild_index

            rebuild_index()
            client = chromadb.PersistentClient(
                path=str(CHROMADB_DIR),
                settings=Settings(anonymized_telemetry=False, allow_reset=False),
            )
            collection = client.get_collection(COLLECTION_NAME)
            model = SentenceTransformer(MODEL_NAME)
            print("CoopWise rebuilt its saved index after an unusable database.", flush=True)
            return model, collection, None
        except Exception as rebuild_exc:
            print(
                f"CoopWise rebuild failed: {type(rebuild_exc).__name__}: {rebuild_exc}",
                flush=True,
            )
            return None, None, f"Could not load or rebuild CoopWise: {rebuild_exc}"


MODEL, COLLECTION, LOAD_ERROR = load_search_resources()


def get_topics() -> list[str]:
    source_file = PROJECT_DIR / "source_data" / "backyard_poultry_sources.json"
    static_topics: list[str] = []
    if source_file.exists():
        try:
            sources = json.loads(source_file.read_text(encoding="utf-8"))
            static_topics = sorted({source["topic"] for source in sources})
        except (OSError, json.JSONDecodeError, KeyError):
            static_topics = []

    if COLLECTION is None:
        return ["All topics", *static_topics]
    all_rows = COLLECTION.get(include=["metadatas"])
    topics = sorted(
        {
            row["topic"]
            for row in all_rows["metadatas"]
            if row and row.get("topic")
        }
    )
    return ["All topics", *topics] if topics else ["All topics", *static_topics]


TOPICS = get_topics()


def format_results(results: dict) -> str:
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    scores = results.get("scores", [[]])[0]
    if not scores:
        distances = results.get("distances", [[]])[0]
        scores = [max(0.0, 1.0 - float(distance)) for distance in distances]

    if not documents:
        return (
            "### No matching passages found\n"
            "Try a broader phrase or choose **All topics**."
        )

    cards: list[str] = []
    for rank, (document, metadata, score) in enumerate(
        zip(documents, metadatas, scores), start=1
    ):
        cards.append(
            f"### {rank}. {metadata['title']}\n"
            f"**Organization:** {metadata['organization']}  \n"
            f"**Topic:** {metadata['topic']}  \n"
            f"**Similarity:** {float(score):.3f}  \n"
            f"[Open original source]({metadata['url']})\n\n"
            f"{document}\n\n"
            f"*Source type: attributed {metadata.get('content_type', 'summary')}.*"
        )
    return "\n\n---\n\n".join(cards)


def search(query: str, topic: str):
    query = query.strip()
    if not query:
        return "### Enter a question to begin\nTry an everyday question about your coop, flock, or eggs."
    if LOAD_ERROR:
        return (
            "### Search index unavailable\n"
            f"{LOAD_ERROR}. Run `python build_index.py` to build it."
        )
    if COLLECTION is None or MODEL is None:
        return "### Search index unavailable\nRun `python build_index.py` before launching the app."

    query_embedding = MODEL.encode([query], convert_to_numpy=True)
    where = None if topic == "All topics" else {"topic": topic}
    try:
        available = COLLECTION.count()
        if available == 0:
            return "### No passages are available\nThe saved collection is empty."
        rows = COLLECTION.get(include=["documents", "metadatas"])
        stop_words = {
            "a", "an", "and", "are", "do", "for", "how", "i", "in", "is",
            "my", "of", "the", "to", "what", "with", "should",
        }
        query_terms = {
            term for term in re.findall(r"[a-z0-9]+", query.lower())
            if len(term) > 2 and term not in stop_words
        }
        ranked = []
        for document, metadata in zip(rows["documents"], rows["metadatas"]):
            if where and metadata.get("topic") != topic:
                continue
            searchable = " ".join(
                [
                    document,
                    metadata.get("title", ""),
                    metadata.get("organization", ""),
                    metadata.get("topic", ""),
                ]
            ).lower()
            overlap = sum(
                1 for term in query_terms
                if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", searchable)
            )
            ranked.append((document, metadata, overlap))
        ranked.sort(key=lambda item: item[2], reverse=True)
        if not ranked:
            return "### No matching passages found\nTry a broader phrase or choose **All topics**."
        top = ranked[:5]
        return format_results(
            {
                "documents": [[item[0] for item in top]],
                "metadatas": [[item[1] for item in top]],
                "scores": [[float(item[2]) / max(1.0, len(query_terms)) for item in top]],
            }
        )
    except Exception as exc:
        return f"### Search could not be completed\n{exc}"


CSS = """
.coopwise-header {text-align: center; margin-bottom: 0.5rem;}
.source-warning {border-left: 4px solid #d97706; padding-left: 1rem;}
"""

with gr.Blocks(title="CoopWise") as demo:
    gr.Markdown(
        "# CoopWise",
        elem_classes=["coopwise-header"],
    )
    gr.Markdown(
        "Semantic search for backyard chicken keepers, with passages from "
        "USDA, CDC, university Extension, and veterinary education sources.",
        elem_classes=["coopwise-header"],
    )

    with gr.Row():
        query_box = gr.Textbox(
            label="Ask a flock-care question",
            placeholder="How do I keep the coop dry in winter?",
            lines=2,
            scale=4,
        )
        topic_box = gr.Dropdown(
            choices=TOPICS,
            value="All topics",
            label="Topic",
            scale=1,
            allow_custom_value=True,
        )

    search_button = gr.Button("Search CoopWise", variant="primary")
    examples = gr.Examples(
        examples=[
            ["How do I keep the coop dry in winter?", "Winter weather"],
            ["What should I do before adding new birds?", "Adding birds"],
            ["How can I prevent Salmonella around my flock?", "Human safety"],
            ["Why has egg production dropped?", "Egg laying"],
            ["How do I provide clean water and balanced feed?", "Feeding"],
            ["What are signs that my chicken is sick?", "Flock health"],
        ],
        inputs=[query_box, topic_box],
        label="Example questions",
    )
    output = gr.Markdown(label="Relevant passages")

    search_button.click(search, inputs=[query_box, topic_box], outputs=output)
    query_box.submit(search, inputs=[query_box, topic_box], outputs=output)

    gr.Markdown(
        "CoopWise retrieves information from curated sources; it does not diagnose "
        "disease or replace professional care. Contact a veterinarian or your State "
        "veterinarian/appropriate animal-health authority for urgent illness or "
        "suspected contagious disease.",
        elem_classes=["source-warning"],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Soft(),
        css=CSS,
    )
