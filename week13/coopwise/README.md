---
title: Coopwise Search
emoji: 📈
colorFrom: gray
colorTo: indigo
sdk: gradio
sdk_version: 6.32.0
python_version: '3.12'
app_file: app.py
pinned: false
---

# CoopWise

CoopWise is a semantic search app for backyard chicken keepers. It retrieves relevant passages for everyday questions about flock health, biosecurity, coop care, weather, feeding, egg laying, and human safety.

## Data

The corpus contains 24 curated resource pages from USDA APHIS, CDC, university Extension services, and a veterinary education publisher. Source metadata includes:

- title
- organization
- topic
- original URL
- content type

The source file is [`source_data/backyard_poultry_sources.json`](source_data/backyard_poultry_sources.json). Entries are concise summaries written for this project rather than scraped page text. The original URL is provided for every source. Full text reuse terms were not assumed. Search results are retrieved passages from those summaries, not diagnoses or veterinary advice.

## How it works

1. `build_index.py` reads the source JSON.
2. It splits each source into paragraph-aware, sentence-balanced chunks. The target is 150-220 model tokens, with a 25-token sentence overlap. The target is a balance between enough context for meaning and enough chunks for precise retrieval.
3. `sentence-transformers/all-MiniLM-L6-v2` creates dense embeddings with `SentenceTransformer.encode`.
4. ChromaDB stores documents, embeddings, source metadata, and stable source/chunk IDs in `chromadb/`.
5. `app.py` loads the saved collection and model at startup. It does not rebuild the database.
6. A natural-language query is embedded and queried against the top five nearest passages. A topic filter narrows ChromaDB metadata results.

Cosine similarity is used for retrieval. The displayed similarity score is `1 - Chroma distance`.

## Build and run locally

From the repository root:

```bash
cd week13/coopwise
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python build_index.py
python app.py
```

Open the local URL printed by Gradio, usually `http://127.0.0.1:7860`.

The database is a repository artifact and should be included in the Hugging Face Space. If source data changes, rerun `python build_index.py` and commit the updated `chromadb/` folder.

## Tests

Run a focused startup and search check after building:

```bash
python -m unittest test_app.py
```

You can also rebuild from the project directory and confirm the collection count by running `python build_index.py`.

## Deploy to Hugging Face Spaces

1. Create a Hugging Face account and a new **Gradio** Space.
2. In the repository settings or user settings, create a write-enabled Hugging Face access token if command-line deployment is used.
3. Upload this project directory, including `app.py`, `build_index.py`, `requirements.txt`, `README.md`, `source_data/`, and `chromadb/`.
4. Set the Space SDK to **Gradio** and use Python 3.11 or newer.
5. Push the repository. Hugging Face will install `requirements.txt` and run `app.py`.

Example using the Hugging Face CLI:

```bash
pip install -U huggingface_hub
huggingface-cli login
git init
git add app.py build_index.py requirements.txt README.md source_data chromadb
git commit -m "Build CoopWise semantic search app"
git remote add origin https://huggingface.co/spaces/<username>/<space-name>
git push -u origin main
```

Do not commit or print Hugging Face tokens. The deployment URL will be:

`https://huggingface.co/spaces/<username>/<space-name>`

CoopWise is an information retrieval app, not a veterinary diagnostic tool. For urgent illness or suspected contagious disease, contact a veterinarian or appropriate animal-health authority.
