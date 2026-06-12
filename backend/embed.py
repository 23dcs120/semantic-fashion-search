import os
import sys

print("Step 1: Starting embed.py")

import numpy as np
print("Step 2: numpy ok")

import pandas as pd
print("Step 3: pandas ok")

import faiss
print("Step 4: faiss ok")

import torch
print("Step 5: torch ok")

from PIL import Image
print("Step 6: PIL ok")

from transformers import CLIPModel, CLIPProcessor
print("Step 7: transformers ok")

# paths
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_CSV = os.path.join(BASE_DIR, "catalog", "metadata.csv")
IMAGE_DIR   = os.path.join(BASE_DIR, "catalog", "images")
EMBED_DIR   = os.path.join(BASE_DIR, "embeddings")
EMB_PATH    = os.path.join(EMBED_DIR, "catalog_embeddings.npy")
INDEX_PATH  = os.path.join(EMBED_DIR, "faiss_index.bin")

print(f"Step 8: BASE_DIR = {BASE_DIR}")
print(f"Step 9: CATALOG_CSV exists = {os.path.exists(CATALOG_CSV)}")
print(f"Step 10: IMAGE_DIR exists = {os.path.exists(IMAGE_DIR)}")

os.makedirs(EMBED_DIR, exist_ok=True)

MODEL_NAME = "openai/clip-vit-base-patch32"
print("Step 11: Loading CLIP model (may take a few minutes on first run)...")

model     = CLIPModel.from_pretrained(MODEL_NAME)
processor = CLIPProcessor.from_pretrained(MODEL_NAME)
model.eval()

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
print(f"Step 12: Model loaded on {device}")

df = pd.read_csv(CATALOG_CSV)
print(f"Step 13: Catalog loaded with {len(df)} items")

embeddings = []
for _, row in df.iterrows():
    img_path = os.path.join(IMAGE_DIR, str(row["image_file"]))
    if not os.path.exists(img_path):
        print(f"  Skipping missing image: {img_path}")
        embeddings.append(np.zeros(512, dtype="float32"))
        continue
    image  = Image.open(img_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    emb = emb / emb.norm(dim=-1, keepdim=True)
    embeddings.append(emb.squeeze().cpu().numpy().astype("float32"))
    print(f"  Done: {row['name']}")

embeddings_np = np.vstack(embeddings).astype("float32")
np.save(EMB_PATH, embeddings_np)
print(f"Saved embeddings to {EMB_PATH}")

dim   = embeddings_np.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(embeddings_np)
faiss.write_index(index, INDEX_PATH)
print(f"Saved FAISS index to {INDEX_PATH}")
print(f"DONE! Index has {index.ntotal} vectors.")