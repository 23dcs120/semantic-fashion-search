import streamlit as st
import requests
import os
from PIL import Image

API_BASE  = "http://localhost:8000"
IMAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "catalog", "images"
)
TOP_K = 5

st.set_page_config(page_title="LOOKR — Fashion Search", page_icon="🔍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #F7F5F2; color: #1a1a1a; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 3rem !important; max-width: 1200px; }

/* hide default streamlit top padding */
.stApp > header { display: none; }

/* ── hero ── */
.hero {
    background: #1a1a1a;
    color: #F7F5F2;
    padding: 2.5rem 3rem 2rem;
    margin: 0 -2rem 2.5rem;
}
.hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 700;
    letter-spacing: -1px;
    margin: 0 0 0.3rem;
    line-height: 1;
}
.hero p {
    font-size: 0.82rem;
    color: #777;
    margin: 0;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

/* ── search card ── */
.search-card {
    background: white;
    border-radius: 14px;
    padding: 1.6rem 2rem;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    margin-bottom: 2.5rem;
}
.search-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #999;
    margin-bottom: 0.8rem;
}

/* ── radio buttons ── */
div[data-testid="stRadio"] > div { gap: 0.5rem; }
div[data-testid="stRadio"] label {
    background: #F7F5F2 !important;
    border: 1.5px solid #e0ddd8 !important;
    border-radius: 6px !important;
    padding: 0.4rem 1.1rem !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    color: #666 !important;
    cursor: pointer !important;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #1a1a1a !important;
    border-color: #1a1a1a !important;
    color: white !important;
}

/* ── text input ── */
.stTextInput > div > div > input {
    background: #F7F5F2 !important;
    border: 1.5px solid #e0ddd8 !important;
    border-radius: 8px !important;
    color: #1a1a1a !important;
    font-size: 1rem !important;
    padding: 0.7rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #C8A96E !important;
    box-shadow: 0 0 0 3px rgba(200,169,110,0.15) !important;
}

/* hide input label gap */
.stTextInput label { display: none !important; }

/* ── search button ── */
.stButton > button {
    background: #1a1a1a !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    padding: 0.7rem 1.5rem !important;
    width: 100% !important;
    margin-top: 0 !important;
}
.stButton > button:hover { background: #C8A96E !important; }

/* ── results section ── */
.results-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0 0 0.3rem;
}
.results-sub {
    font-size: 0.82rem;
    color: #999;
    margin-bottom: 1.5rem;
    letter-spacing: 0.03em;
}

/* ── result card ── */
.rcard {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
}
.rcard:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 28px rgba(0,0,0,0.11);
}
.rcard-img {
    background: #f0ede8;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
}
.rcard-body { padding: 0.9rem 1rem 1.1rem; }
.rcard-cat {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #C8A96E;
    margin-bottom: 0.3rem;
}
.rcard-name {
    font-size: 0.88rem;
    font-weight: 600;
    color: #1a1a1a;
    line-height: 1.35;
    margin-bottom: 0.35rem;
}
.rcard-desc {
    font-size: 0.74rem;
    color: #999;
    line-height: 1.45;
    margin-bottom: 0.6rem;
}
.rcard-score {
    display: inline-block;
    background: #f7f5f2;
    border: 1px solid #e8e4df;
    color: #777;
    font-size: 0.67rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.04em;
}

/* ── empty state ── */
.empty {
    text-align: center;
    padding: 5rem 2rem;
    color: #bbb;
}
.empty-icon { font-size: 3.5rem; margin-bottom: 1rem; }
.empty-text { font-size: 0.95rem; color: #aaa; }

/* ── remove streamlit column gap ── */
[data-testid="column"] { padding: 0 0.4rem !important; }
</style>
""", unsafe_allow_html=True)

# ── HERO ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>LOOKR</h1>
    <p>Semantic Fashion Search &nbsp;·&nbsp; Powered by CLIP &nbsp;·&nbsp; Fully Local</p>
</div>
""", unsafe_allow_html=True)

# ── SEARCH CARD ────────────────────────────────────────────────────────────────
st.markdown('<div class="search-card">', unsafe_allow_html=True)
st.markdown('<div class="search-label">Search Mode</div>', unsafe_allow_html=True)

mode = st.radio("mode", ["📝 Text Query", "🖼️ Image Query"],
                horizontal=True, label_visibility="collapsed")

results    = []
query_used = ""

if mode == "📝 Text Query":
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("q",
            placeholder="Try: white sneakers · floral summer dress · black leather jacket",
            label_visibility="collapsed")
    with col2:
        search_btn = st.button("Search →")

    if search_btn and query.strip():
        with st.spinner("Finding matches..."):
            try:
                resp = requests.get(
                    f"{API_BASE}/search/text",
                    params={"query": query.strip(), "top_k": TOP_K},
                    timeout=60)
                resp.raise_for_status()
                results    = resp.json()["results"]
                query_used = query.strip()
            except requests.exceptions.ConnectionError:
                st.error("⚠️ Backend not running. Start: uvicorn backend.main:app --reload")
            except Exception as e:
                st.error(f"Error: {e}")

elif mode == "🖼️ Image Query":
    uploaded = st.file_uploader(
        "Upload a clothing photo to find similar items",
        type=["jpg", "jpeg", "png"])
    if uploaded:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(uploaded, width=160, caption="Query image")
        with col2:
            st.write("")
            st.write("")
            if st.button("Find Similar →"):
                with st.spinner("Analysing..."):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/search/image",
                            files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                            data={"top_k": TOP_K},
                            timeout=60)
                        resp.raise_for_status()
                        results    = resp.json()["results"]
                        query_used = uploaded.name
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Backend not running.")
                    except Exception as e:
                        st.error(f"Error: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# ── RESULTS ────────────────────────────────────────────────────────────────────
if results:
    st.markdown(f'<div class="results-title">Results</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="results-sub">Showing top {len(results)} matches for &ldquo;{query_used}&rdquo;</div>', unsafe_allow_html=True)

    cols = st.columns(5, gap="small")
    for i, item in enumerate(results):
        with cols[i % 5]:
            img_path = os.path.join(IMAGE_DIR, item["image_file"])
            if os.path.exists(img_path):
                img = Image.open(img_path)
                # pad image to square for uniform card height
                w, h   = img.size
                size   = max(w, h)
                square = Image.new("RGB", (size, size), (240, 237, 232))
                square.paste(img, ((size - w) // 2, (size - h) // 2))
                st.image(square, use_container_width=True)

            st.markdown(f"""
<div class="rcard-body">
  <div class="rcard-cat">{item['category']}</div>
  <div class="rcard-name">{item['name']}</div>
  <div class="rcard-desc">{item['description'][:75]}{'…' if len(item['description']) > 75 else ''}</div>
  <div class="rcard-score">match &nbsp;{item['score']:.3f}</div>
</div>""", unsafe_allow_html=True)

else:
    st.markdown("""
<div class="empty">
    <div class="empty-icon">👗</div>
    <div class="empty-text">Enter a text query or upload an image to search the catalog.</div>
</div>""", unsafe_allow_html=True)