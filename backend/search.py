import os
import numpy as np
import pandas as pd
import faiss
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_CSV = os.path.join(BASE_DIR, "catalog", "metadata.csv")
IMAGE_DIR   = os.path.join(BASE_DIR, "catalog", "images")
INDEX_PATH  = os.path.join(BASE_DIR, "embeddings", "faiss_index.bin")

MODEL_NAME = "openai/clip-vit-base-patch32"

print("Loading CLIP model...")
_model     = CLIPModel.from_pretrained(MODEL_NAME)
_processor = CLIPProcessor.from_pretrained(MODEL_NAME)
_model.eval()
_device = "cuda" if torch.cuda.is_available() else "cpu"
_model.to(_device)
print(f"CLIP ready on {_device.upper()}")

print(f"Loading FAISS index from {INDEX_PATH}...")
_index      = faiss.read_index(INDEX_PATH)
_catalog_df = pd.read_csv(CATALOG_CSV)
print(f"FAISS index loaded with {_index.ntotal} items")


def _text_to_vec(text):
    inputs = _processor(text=[text], return_tensors="pt",
                        padding=True, truncation=True).to(_device)
    with torch.no_grad():
        emb = _model.get_text_features(**inputs)
    emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.squeeze().cpu().numpy().astype("float32").reshape(1, -1)


def _image_to_vec(image_path):
    image  = Image.open(image_path).convert("RGB")
    inputs = _processor(images=image, return_tensors="pt").to(_device)
    with torch.no_grad():
        emb = _model.get_image_features(**inputs)
    emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.squeeze().cpu().numpy().astype("float32").reshape(1, -1)


def _format_results(indices, scores):
    results = []
    for idx, score in zip(indices, scores):
        if idx < 0 or idx >= len(_catalog_df):
            continue
        row = _catalog_df.iloc[int(idx)]
        results.append({
            "id":          int(row["id"]),
            "name":        str(row["name"]),
            "category":    str(row["category"]),
            "description": str(row["description"]),
            "image_file":  str(row["image_file"]),
            "score":       round(float(score), 4),
        })
    return results


def search_by_text(query, top_k=5):
    vec = _text_to_vec(query)
    scores, indices = _index.search(vec, top_k)
    return _format_results(indices[0], scores[0])


def search_by_image(image_path, top_k=5):
    vec = _image_to_vec(image_path)
    scores, indices = _index.search(vec, top_k)
    return _format_results(indices[0], scores[0])