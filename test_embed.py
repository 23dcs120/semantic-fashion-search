import os
print("Step 1 ok")
import numpy as np
print("Step 2 ok")
import pandas as pd
print("Step 3 ok")
import faiss
print("Step 4 ok")
import torch
print("Step 5 ok")
from PIL import Image
print("Step 6 ok")
from transformers import CLIPModel, CLIPProcessor
print("Step 7 ok")

BASE_DIR    = os.getcwd()
CATALOG_CSV = os.path.join(BASE_DIR, "catalog", "metadata.csv")
IMAGE_DIR   = os.path.join(BASE_DIR, "catalog", "images")
EMBED_DIR   = os.path.join(BASE_DIR, "embeddings")
os.makedirs(EMBED_DIR, exist_ok=True)

print("Step 8: Loading CLIP model...")
model     = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model.eval()
print("Step 9: Model loaded")

df = pd.read_csv(CATALOG_CSV)
print(f"Step 10: {len(df)} items in catalog")

embeddings = []
for _, row in df.iterrows():
    img_path = os.path.join(IMAGE_DIR, str(row["image_file"]))
    image    = Image.open(img_path).convert("RGB")
    inputs   = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    emb = emb / emb.norm(dim=-1, keepdim=True)
    embeddings.append(emb.squeeze().numpy().astype("float32"))
    print(f"  Done: {row['name']}")

embeddings_np = np.vstack(embeddings).astype("float32")
np.save(os.path.join(EMBED_DIR, "catalog_embeddings.npy"), embeddings_np)

index = faiss.IndexFlatIP(embeddings_np.shape[1])
index.add(embeddings_np)
faiss.write_index(index, os.path.join(EMBED_DIR, "faiss_index.bin"))
print("DONE! Index saved.")