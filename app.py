from textwrap import dedent
import streamlit as st
import sys
import os
import time
from dotenv import load_dotenv

sys.path.append("src")
from src.recommender import load_relevant_products
from src.utils import analyze_products_batch, is_positive_summary, get_dermatologist_tip_cached
from src.ai_chat import get_chat_response_streaming

# Load API Key
# load_dotenv()
# OPENROUTER_API_KEY = os.getenv("LLM_API_KEY")
OPENROUTER_API_KEY = st.secrets["LLM_API_KEY"]

# Init session state
for key in ["show_chat", "chat_history", "final_products", "skin_types", "concerns", "form_submitted"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "chat_history" in key else False if "show" in key or "submitted" in key else []

st.set_page_config(page_title="Skincare Match 💎", page_icon="💎", layout="wide")

# CSS Styling + Luxury Font
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
html, body, .stApp {
    background-color: #fff8f9;
    font-family: 'Inter', sans-serif;
    color: #333;
}
h1, h2, h3 {
    font-family: 'Playfair Display', serif;
    color: #bb2649;
}
.stForm {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #fff;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    margin-bottom: 30px;
}
.stButton > button {
    background-color: #bb2649;
    color: white;
    font-weight: bold;
    border: none;
    padding: 10px 24px;
    border-radius: 30px;
}
.stButton > button:hover {
    background-color: #e91e63;
}
.chat-bubble {
    background-color: #fff0f5;
    padding: 12px 16px;
    border-radius: 16px;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align:center;'>💎 Skincare Match Finder</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Temukan produk skincare yang cocok dengan kondisi kulit dan preferensimu, secara instan dan akurat</p>", unsafe_allow_html=True)

# Options
SKIN_TYPES = ["Kulit Kering", "kulit-berminyak", "kulit-kombinasi", "kulit-normal", "kulit-sensitif"]
CONCERNS = [
    "kulit-sensitif", "komedo", "aging", "kulit-kusam", "Kantung Mata", "Pori Besar",
    "Stretch Mark", "Cellulite", "Skin Tightening", "jerawat", "rambut-rontok", "Oily",
    "Dandruff", "Dullness", "Dark Spots", "Blackheads & Visible Pores", "acne & blemishes",
    "Dry Scalp", "Sore, Dry & Flaky Nipple", "Oiliness", "Normal", "Stretch Marks", "Dark Circles"
]
CATEGORY_GROUPS = {
    "Treatment": ["Acne / Pimple Patch", "Acne Treatment / Sealing Gel / Cream", "Toner", "Essence", "Face Serum"],
    "Cleanser": ["Face Wash", "Cleansing Oil", "Cleansing Balm", "Makeup Remover"],
    "Mask": ["Sheet Mask", "Clay Mask", "Sleeping Mask"],
    "Moisturizer": ["Face Gel", "Face Cream & Lotion", "Face Oil"],
    "Sun Care": ["Sunscreen", "Touch-Ups Sunscreen"],
    "Lip Care": ["Lip Balm", "Lip Scrub", "Lip Serum"],
    "Eye Care": ["Eye Cream", "Eye Mask", "Eye Serum"],
}
ALL_SUBCATEGORIES = [f"{cat} - {sub}" for cat, subs in CATEGORY_GROUPS.items() for sub in subs]

# Form Input
with st.form("form-premium"):
    col1, col2 = st.columns(2)
    with col1:
        skin = st.multiselect("🧬 Jenis Kulit", SKIN_TYPES)
        concern = st.multiselect("❗ Concern Kulit", CONCERNS)
    with col2:
        subcat_selected = st.multiselect("📂 Subkategori Produk", ALL_SUBCATEGORIES)
        budget_min = st.number_input("💰 Budget Minimum (Rp)", 0, value=100000)
        budget_max = st.number_input("💎 Budget Maksimum (Rp)", 0, value=2000000)
    form_btn = st.form_submit_button("🔍 Temukan Rekomendasi")

# Submit logic
if form_btn:
    st.session_state.form_submitted = True
    st.session_state.show_chat = False
    st.session_state.chat_history = []
    st.session_state.skin_types = skin
    st.session_state.concerns = concern

# Result
if st.session_state.form_submitted:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #fff0f5, #ffe4e1); border-radius: 20px; padding: 20px 30px; margin: 20px 0; box-shadow: 0 4px 14px rgba(255, 182, 193, 0.3);'>
        <h3 style='color:#bb2649;'>✨ Analisis Kulitmu</h3>
        <p><b>Jenis Kulit:</b> <span style="color:#e91e63;">{', '.join(skin)}</span></p>
        <p><b>Concern Kulit:</b> <span style="color:#e91e63;">{', '.join(concern)}</span></p>
    </div>
    """, unsafe_allow_html=True)

    products = load_relevant_products(subcat_list=subcat_selected, skin_types=skin, concerns=concern,
                                      budget_min=budget_min, budget_max=budget_max, data_dir="data")

    with st.spinner("💬 AI sedang menganalisis produk terbaik..."):
        summaries = analyze_products_batch(products[:6], skin, concern, OPENROUTER_API_KEY)

    final_products = []
    for p in products:
        if p["id"] in summaries and is_positive_summary(summaries[p["id"]]):
            p["ai_summary"] = summaries[p["id"]]
            final_products.append(p)

    st.session_state.final_products = final_products

    if not final_products:
        st.warning("Tidak ada produk yang cocok.")
    else:
        with st.spinner("🩺 Dermatologis AI sedang menulis tips..."):
            tip = get_dermatologist_tip_cached(final_products, skin, concern, api_key=OPENROUTER_API_KEY)

        st.markdown(f"""
        <div style='margin-top:20px;padding:15px;border-radius:12px;background:#fff6f9;border-left:6px solid #bb2649;'>
            <h4 style='color:#bb2649;'>🩺 Saran Skincare dari AI Dermatologis</h4>
            <p>{tip}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🧴 Rekomendasi Produk")
        cols = st.columns(3)
        for idx, p in enumerate(final_products):
            with cols[idx % 3]:
                st.markdown(f"""
                <div style='
                    background: #fff;
                    border-radius: 20px;
                    padding: 20px;
                    margin-bottom: 24px;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.06);
                    border: 1px solid #f4c6d0;
                '>
                    <img src="{p['img']}" style='width:100%;border-radius:12px;margin-bottom:12px;'/>
                    <h4 style='margin-bottom:4px;font-size:16px;'>{p['name']}</h4>
                    <div style='font-size:14px;color:#777;'>{p['brand']}</div>
                    <div style='font-size:16px;font-weight:bold;color:#bb2649;margin:8px 0;'>Rp{p['price']:,}</div>
                    <div>⭐ {p['rating']:.1f} / 5</div>
                    <details style='margin-top:8px;'>
                        <summary>💡 Alasan</summary>
                        <p>{p['why']}</p>
                    </details>
                    <details>
                        <summary>🧪 Ingredients</summary>
                        <p>{p['ingredients']}</p>
                    </details>
                    <details>
                        <summary>🧴 Cara Pakai</summary>
                        <p>{p['how_to_use']}</p>
                    </details>
                    <details>
                        <summary>🧠 AI Ringkasan Review</summary>
                        <p>{p.get("ai_summary", "_Belum tersedia_")}</p>
                    </details>
                    <a href="{p['url']}" target="_blank" style='display:inline-block;margin-top:10px;font-weight:bold;color:#bb2649;'>🌐 Lihat Produk</a>
                </div>
                """, unsafe_allow_html=True)

        if st.button("💬 Tanya AI tentang produk ini"):
            st.session_state.show_chat = True

# Chat session
if st.session_state.show_chat and st.session_state.final_products:
    st.markdown("### 🤖 Tanya AI Seputar Produk")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_msg = st.chat_input("Tanya sesuatu...")
    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        context = ""
        for p in st.session_state.final_products:
            context += f"Produk: {p['name']} ({p['brand']})\n- Ingredients: {p['ingredients']}\n- Summary: {p['ai_summary']}\n\n"

        final_prompt = f"""
Berikut daftar produk yang direkomendasikan untuk user dengan kulit: {', '.join(skin)} dan concern: {', '.join(concern)}.
Gunakan data ini untuk menjawab pertanyaan mereka sebagai beauty advisor AI.

{context}

Pertanyaan: {user_msg}
"""

        with st.chat_message("assistant"):
            with st.spinner("💬 AI sedang menjawab..."):
                response_text = ""
                box = st.empty()
                for token in get_chat_response_streaming(OPENROUTER_API_KEY, final_prompt):
                    response_text += token
                    box.markdown(f"<div class='chat-bubble'>{response_text}</div>", unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
