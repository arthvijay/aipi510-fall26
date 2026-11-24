from __future__ import annotations

import json
import re
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_DIR / "source_data" / "backyard_poultry_sources.json"
CHROMADB_DIR = PROJECT_DIR / "chromadb"
COLLECTION_NAME = "coopwise_sources"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TARGET_TOKENS = 180
MIN_CHUNK_TOKENS = 150
MAX_CHUNK_TOKENS = 220
OVERLAP_TOKENS = 25


def load_sources() -> list[dict]:
    with SOURCE_FILE.open("r", encoding="utf-8") as handle:
        sources = json.load(handle)
    required = {"title", "organization", "topic", "url", "text", "content_type"}
    for source in sources:
        missing = required - source.keys()
        if missing:
            raise ValueError(f"Source {source.get('title', '<unnamed>')} missing fields: {sorted(missing)}")
        if source["content_type"] not in {"summary", "quotation"}:
            raise ValueError("content_type must be 'summary' or 'quotation'")
    return sources


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def token_count(tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def chunk_text(text: str, tokenizer) -> list[str]:
    """Paragraph-aware greedy chunking with a small sentence overlap."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[str] = []
    current_sentences: list[str] = []

    def flush() -> None:
        nonlocal current_sentences
        if current_sentences:
            chunks.append(" ".join(current_sentences).strip())

    for paragraph in paragraphs:
        sentences = split_sentences(paragraph)
        for sentence in sentences:
            candidate = " ".join(current_sentences + [sentence]).strip()
            if current_sentences and token_count(tokenizer, candidate) > MAX_CHUNK_TOKENS:
                flush()
                overlap: list[str] = []
                overlap_tokens = 0
                for previous in reversed(current_sentences):
                    previous_tokens = token_count(tokenizer, previous)
                    if overlap_tokens + previous_tokens > OVERLAP_TOKENS:
                        break
                    overlap.insert(0, previous)
                    overlap_tokens += previous_tokens
                current_sentences = overlap
            current_sentences.append(sentence)

            if token_count(tokenizer, " ".join(current_sentences)) >= TARGET_TOKENS:
                if token_count(tokenizer, " ".join(current_sentences)) >= MIN_CHUNK_TOKENS:
                    flush()
                    current_sentences = []

    flush()
    return [chunk for chunk in chunks if chunk]


def stable_id(source_index: int, chunk_number: int) -> str:
    return f"source-{source_index:03d}-chunk-{chunk_number:03d}"


def main() -> None:
    sources = load_sources()
    CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

    model = SentenceTransformer(MODEL_NAME)
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for source_index, source in enumerate(sources):
        chunks = chunk_text(source["text"], model.tokenizer)
        for chunk_number, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append(
                {
                    "title": source["title"],
                    "organization": source["organization"],
                    "topic": source["topic"],
                    "url": source["url"],
                    "chunk_number": chunk_number,
                    "content_type": source["content_type"],
                }
            )
            ids.append(stable_id(source_index, chunk_number))

    embeddings = model.encode(documents, convert_to_numpy=True, show_progress_bar=True)

    client = chromadb.PersistentClient(
        path=str(CHROMADB_DIR),
        settings=Settings(anonymized_telemetry=False, allow_reset=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    existing = collection.get(include=[])
    stale_ids = sorted(set(existing["ids"]) - set(ids))
    if stale_ids:
        collection.delete(ids=stale_ids)
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )

    print(f"Built {COLLECTION_NAME}: {len(documents)} chunks from {len(sources)} sources")


if __name__ == "__main__":
    main()
