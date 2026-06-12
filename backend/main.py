import os
import sys
import shutil
import tempfile

# Fix path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Semantic Fashion Search Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(BASE_DIR, "catalog", "images")
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# import search AFTER app is created
from search import search_by_text, search_by_image, _catalog_df

@app.get("/")
def root():
    return {"status": "running", "message": "Semantic Fashion Search API"}

@app.get("/catalog")
def get_catalog():
    return {"items": _catalog_df.to_dict(orient="records")}

@app.get("/search/text")
def text_search(query: str, top_k: int = 5):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    results = search_by_text(query.strip(), top_k=top_k)
    return {"query": query, "results": results}

@app.post("/search/image")
async def image_search(
    file: UploadFile = File(...),
    top_k: int = Form(5),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    suffix = os.path.splitext(file.filename)[-1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        results = search_by_image(tmp_path, top_k=top_k)
    finally:
        os.remove(tmp_path)
    return {"filename": file.filename, "results": results}