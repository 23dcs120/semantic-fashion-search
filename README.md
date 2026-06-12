# 👗 Semantic Fashion Search Engine

Proof-of-concept semantic search engine that finds fashion items by
**natural language text** or **query image** — powered entirely by
local open-source models. No external APIs used.

---

## Demo Video
> 🎬 [Watch Demo Video](https://www.loom.com/share/84a2f24862b44635b51112237a58b9fa)

---

## How It Works

```
Query (text or image)
        ↓
   CLIP encoder          ← runs 100% locally via HuggingFace
        ↓
  512-d embedding
        ↓
 FAISS IndexFlatIP       ← cosine similarity search
        ↓
  Top-K ranked results   ← ordered by similarity score
```

Both text and image queries share the same FAISS index because CLIP maps
all modalities into one common vector space — so "blue jeans" (text) and
a photo of blue jeans (image) produce nearby vectors automatically.

---

## Project Structure

```
semantic-fashion-search/
├── catalog/
│   ├── images/            # 25 fashion item images
│   └── metadata.csv       # id, name, category, description, image_file
├── embeddings/
│   ├── catalog_embeddings.npy
│   └── faiss_index.bin
├── backend/
│   ├── embed.py           # builds FAISS index from catalog images
│   ├── search.py          # CLIP + FAISS search logic
│   └── main.py            # FastAPI REST API
├── frontend/
│   └── app.py             # Streamlit UI
├── setup_dataset.py       # downloads Kaggle dataset + builds catalog
├── demo.ipynb             # Jupyter notebook demo
├── requirements.txt       # all dependencies
├── DESIGN.md              # model choice + scaling strategy
└── README.md
```

---

## Setup & Run

### 1. Clone and install dependencies

```bash
git clone https://github.com/<your-username>/semantic-fashion-search.git
cd semantic-fashion-search
pip install -r requirements.txt
```

### 2. Download dataset from Kaggle

```bash
# a) Get your API token from kaggle.com → Settings → API → Create New Token
# b) Place kaggle.json at:
#    Windows: C:\Users\YourName\.kaggle\kaggle.json
#    Mac/Linux: ~/.kaggle/kaggle.json

python setup_dataset.py
```

This downloads the Fashion Product Images (Small) dataset, picks 25 items
across 7 categories, and writes catalog/images/ and catalog/metadata.csv.

### 3. Build the FAISS index

```bash
python test_embed.py
```

Downloads CLIP model (~350 MB on first run) and generates
embeddings/faiss_index.bin.

### 4. Start the FastAPI backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### 5. Start the Streamlit frontend

```bash
streamlit run frontend/app.py
```

Open: http://localhost:8501

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/catalog` | GET | List all catalog items |
| `/search/text?query=blue+jeans&top_k=5` | GET | Text semantic search |
| `/search/image` | POST | Image semantic search (multipart) |

---

## Tech Stack

| Component | Technology | Notes |
|---|---|---|
| Embeddings | CLIP ViT-B/32 (HuggingFace) | Runs 100% locally, no API key |
| Vector Search | FAISS IndexFlatIP | Cosine similarity search |
| Backend API | FastAPI + Uvicorn | REST endpoints |
| Frontend | Streamlit | Interactive search UI |
| Dataset | Kaggle Fashion Product Images Small | paramaggarwal/fashion-product-images-small |

---

## Technical Decisions & Scaling

See **[DESIGN.md](DESIGN.md)** for full details on:
- Why CLIP was chosen over alternatives (ALIGN, BLIP-2, Sentence-BERT)
- How embeddings are computed and stored step by step
- How to scale this pipeline to 100,000+ items in production
- Hybrid search strategy for production systems
