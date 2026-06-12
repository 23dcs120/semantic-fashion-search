# DESIGN.md — Technical Explanation

**Project:** Semantic Fashion Search Engine  
**Candidate:** Parth Shah  
**Assessment:** ARTIFICIA — Data Science & ML Engineering

---

## 1. Model Choice — Why CLIP (ViT-B/32)?

I chose OpenAI's CLIP (`openai/clip-vit-base-patch32`), loaded and run
entirely locally via HuggingFace Transformers — no API calls, no internet
connection required at inference time, and no API keys needed.

**Why CLIP?**  
CLIP (Contrastive Language-Image Pretraining) is a multimodal model trained
on 400 million image-text pairs. This means image embeddings and text
embeddings share the same vector space — so a query like "floral summer dress"
(text) and an actual photo of one (image) produce nearby vectors, enabling
true cross-modal search out of the box without any separate text or image pipeline.

| Alternative | Why not chosen |
|---|---|
| Sentence-BERT | Text-only — cannot embed images, no cross-modal search |
| ALIGN (Google) | Heavier model, harder to run locally on CPU |
| BLIP-2 | ~5 GB model, excessive for a proof-of-concept |
| ResNet + TF-IDF | Two completely separate systems with no shared embedding space |
| OpenAI Embeddings API | External API call — violates local-only requirement |

**Why ViT-B/32 specifically:**
- Compact (~350 MB) — runs comfortably on CPU without a GPU
- Produces 512-dimensional embeddings — fast and memory-efficient for FAISS
- Best speed vs. quality balance for a local proof-of-concept
- Widely benchmarked and well-documented in the open-source community

---

## 2. How Embeddings Are Computed and Stored

### Offline Build Phase — `backend/embed.py`

Run once when the catalog is set up (or whenever new items are added):

```
For each catalog item:
  1. Load item image → PIL Image (RGB)
  2. Pass through CLIP image encoder → 512-d float32 vector
  3. L2-normalise the vector
  4. Append to embeddings list

Save all vectors → embeddings/catalog_embeddings.npy
Build FAISS IndexFlatIP from vectors
Save index → embeddings/faiss_index.bin
```

**Why L2 normalisation?**  
Normalised vectors make inner-product search (IndexFlatIP) mathematically
equivalent to cosine similarity. This measures the angle between semantic
directions rather than raw magnitude — which is what we want when comparing
meaning, not scale.

### Online Query Phase — `backend/search.py`

Happens in real time on every search request:

```
User submits text query OR image query
  → CLIP encoder (text or image branch)
  → 512-d L2-normalised query vector
  → FAISS IndexFlatIP.search(query_vec, top_k)
  → Returns top-k (catalog_index, cosine_similarity) pairs
  → Metadata lookup from catalog DataFrame
  → Return ranked results with name, category, description, score
```

Both text and image queries go through the same FAISS index because CLIP
places all modalities in one shared embedding space — this is the core
strength of the architecture.

---

## 3. Observed Behaviour — Visual Similarity vs. Metadata

During testing, image search queries (e.g. uploading a photo of a person
wearing a light-colored shirt) returned results that matched visual features
like color, texture, and garment style — but occasionally returned items
across gender categories.

**Why this happens:**  
CLIP matches based on visual embeddings — it sees color, texture, cut, and
pattern — not metadata fields like gender or age group. A beige women's jacket
and a beige men's jacket are visually close in the embedding space.

**How this would be handled in production:**  
Combine vector similarity search with metadata filtering:

```
FAISS search (top-k visual matches)
  + SQL/NoSQL filter (gender = "Men", category = "Shirts")
  → Re-ranked final results
```

Vector databases like Qdrant and Weaviate support this natively as
"filtered vector search" — running the metadata filter and ANN search
simultaneously without a performance penalty.

---

## 4. Scaling to 100,000+ Items in Production

### 4a. Index Upgrade Path

| Catalog Size | FAISS Index | Reason |
|---|---|---|
| < 1,000 items | `IndexFlatIP` *(current)* | Exact search, no setup needed |
| 10k – 500k items | `IndexIVFFlat` | Partitions space into Voronoi cells, ~30x speedup |
| 500k – 10M items | `IndexHNSWFlat` | Graph-based ANN, very high recall at low latency |
| 10M+ items | `IndexIVFPQ` | Product quantisation compresses vectors 8-16x, RAM-efficient |

### 4b. Production Architecture

| Challenge | Solution |
|---|---|
| Re-embedding new items blocks search | Async batch pipeline — Celery + Redis worker queue |
| Single machine bottleneck | Shard FAISS index across multiple nodes |
| Inference latency at scale | Deploy CLIP on GPU; export to ONNX for optimised CPU inference |
| Raw FAISS files hard to manage | Migrate to Qdrant, Weaviate, or Milvus vector database |
| Pure vector search misses exact names | Hybrid search — CLIP (dense) + BM25 (sparse) + Reciprocal Rank Fusion |
| Gender / category bleed in results | Add metadata filters alongside vector search |

### 4c. Async Embedding Pipeline (New Items)

```
New product uploaded to catalog
  → Celery task queued (Redis broker)
  → Worker: load image → CLIP inference → 512-d vector
  → Upsert vector into Qdrant with metadata
  → Catalog database updated
  → Search results updated in real time
```

### 4d. Hybrid Search (Recommended for Production)

Pure vector search can miss exact product name queries. Production systems
combine two retrieval strategies:

1. **Dense retrieval** — CLIP embeddings for semantic and visual similarity
2. **Sparse retrieval** — BM25 / Elasticsearch for keyword precision
3. **Reciprocal Rank Fusion** — merges both ranked lists into one final ranking

This is the standard approach used by large e-commerce platforms at scale.

---

## 5. Summary

| Layer | This PoC | Production |
|---|---|---|
| Model | CLIP ViT-B/32 (local, HuggingFace) | Same model, ONNX-optimised on GPU |
| Index | FAISS IndexFlatIP | FAISS IndexFlatIP → Qdrant / Milvus |
| Storage | `.npy` + `.bin` files | Qdrant with metadata filters |
| Ingestion | Script (`embed.py`) | Async Celery + Redis pipeline |
| Serving | FastAPI single process | FastAPI + Gunicorn + Nginx load balancer |
| Search type | Pure dense (CLIP only) | Hybrid dense + sparse + metadata filters |
| Gender/category filtering | Not implemented | Metadata filter alongside ANN search |
