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

# CSS Styling dengan Estetika Girly, Luxury, dan Skincare
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Poppins:wght@300;500&display=swap" rel="stylesheet">
<style>
html, body, .stApp {
    background: linear-gradient(135deg, #fff0f5, #f8e1e9);
    font-family: 'Poppins', sans-serif;
    color: #4a2c40;
    animation: fadeIn 1.2s ease-in-out;
}
h1, h2, h3 {
    font-family: 'Playfair Display', serif;
    color: #c71585;
}
.navbar {
    background: rgba(255, 245, 250, 0.95);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
    backdrop-filter: blur(10px);
}
.navbar .stButton > button {
    background: linear-gradient(45deg, #c71585, #ff69b4);
    color: white;
    border-radius: 25px;
    padding: 10px 20px;
    font-weight: 500;
    transition: all 0.3s ease;
}
.navbar .stButton > button:hover {
    background: linear-gradient(45deg, #ad1457, #ff1493);
    transform: translateY(-2px);
}
.stButton > button {
    background: linear-gradient(45deg, #c71585, #ff69b4);
    color: white;
    border-radius: 25px;
    padding: 12px 25px;
    font-weight: 500;
    border: none;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background: linear-gradient(45deg, #ad1457, #ff1493);
    transform: translateY(-2px);
}
.chat-bubble {
    background: #fff0f5;
    padding: 15px;
    border-radius: 20px;
    margin: 10px 0;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
    animation: bounceIn 0.5s ease;
}
.product-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    border: 2px solid #ffe4e1;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    animation: slideUp 0.6s ease;
}
.product-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 25px rgba(0,0,0,0.12);
}
.product-image {
    width: 100%;
    border-radius: 15px;
    margin-bottom: 15px;
    transition: transform 0.3s ease;
}
.product-image:hover {
    transform: scale(1.05);
}
.product-name {
    font-size: 18px;
    font-weight: 600;
    color: #4a2c40;
}
.product-brand {
    font-size: 14px;
    color: #777;
}
.product-price {
    font-size: 16px;
    font-weight: bold;
    color: #c71585;
}
.product-rating {
    font-size: 14px;
    color: #777;
}
.details-summary {
    font-size: 14px;
    color: #c71585;
    cursor: pointer;
}
.details-content {
    font-size: 14px;
    color: #555;
    margin-top: 5px;
}
.analysis-box {
    background: linear-gradient(135deg, #fff0f5, #ffe4e1);
    border-radius: 20px;
    padding: 25px;
    margin: 30px 0;
    box-shadow: 0 6px 15px rgba(0,0,0,0.1);
    animation: fadeIn 1s ease-in-out;
}
.tip-box {
    background: #ffffff;
    border-radius: 15px;
    padding: 20px;
    margin-top: 30px;
    border-left: 6px solid #c71585;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    animation: slideIn 0.8s ease;
}
.welcome-section {
    text-align: center;
    margin-bottom: 40px;
    animation: fadeIn 1.2s ease-in-out;
}
.welcome-section h2 {
    color: #c71585;
    font-size: 32px;
}
.welcome-section p {
    color: #777;
    font-size: 16px;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes bounceIn {
    0% { opacity: 0; transform: scale(0.8); }
    60% { opacity: 1; transform: scale(1.05); }
    100% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

# Welcome Section
st.markdown("""
<div class='welcome-section'>
    <h2>💎 Skincare Match Finder</h2>
    <p>Discover the perfect skincare products tailored to your unique skin needs with a touch of elegance.</p>
</div>
""", unsafe_allow_html=True)

# Options
SKIN_TYPES = ["Kulit Kering", "Kulit Berminyak", "Kulit Kombinasi", "Kulit Normal", "Kulit Sensitif"]
CONCERNS = [
    "Kulit Sensitif", "Komedo", "Penuaan", "Kulit Kusam", "Kantung Mata", "Pori Besar",
    "Stretch Mark", "Selulit", "Pengencangan Kulit", "Jerawat", "Rambut Rontok", "Berminyak",
    "Ketombe", "Kusam", "Noda Hitam", "Komedo & Pori Tersumbat", "Jerawat & Noda",
    "Kulit Kepala Kering", "Puting Kering & Pecah", "Minyak Berlebih", "Normal", "Stretch Marks", "Lingkaran Hitam"
]
CATEGORY_GROUPS = {
    "Treatment": ["Acne Patch", "Acne Treatment Gel/Cream", "Toner", "Essence", "Face Serum"],
    "Cleanser": ["Face Wash", "Cleansing Oil", "Cleansing Balm", "Makeup Remover"],
    "Mask": ["Sheet Mask", "Clay Mask", "Sleeping Mask"],
    "Moisturizer": ["Face Gel", "Face Cream & Lotion", "Face Oil"],
    "Sun Care": ["Sunscreen", "Touch-Up Sunscreen"],
    "Lip Care": ["Lip Balm", "Lip Scrub", "Lip Serum"],
    "Eye Care": ["Eye Cream", "Eye Mask", "Eye Serum"],
}
ALL_SUBCATEGORIES = [f"{cat} - {sub}" for cat, subs in CATEGORY_GROUPS.items() for sub in subs]

# Sidebar for Form
with st.sidebar:
    st.markdown("<h3 style='margin-bottom:20px;'>✨ Customize Your Skincare</h3>", unsafe_allow_html=True)
    with st.form("form-premium"):
        skin = st.multiselect("🧬 Jenis Kulit", SKIN_TYPES, placeholder="Pilih jenis kulit")
        concern = st.multiselect("❗ Concern Kulit", CONCERNS, placeholder="Pilih concern kulit")
        subcat_selected = st.multiselect("📂 Subkategori Produk", ALL_SUBCATEGORIES, placeholder="Pilih subkategori")
        budget_min = st.number_input("💰 Budget Min (Rp)", 0, value=100000)
        budget_max = st.number_input("💎 Budget Max (Rp)", 0, value=2000000)
        form_btn = st.form_submit_button("🔍 Find Recommendations")

# Submit Logic
if form_btn:
    st.session_state.form_submitted = True
    st.session_state.show_chat = False
    st.session_state.chat_history = []
    st.session_state.skin_types = skin
    st.session_state.concerns = concern

# Result
if st.session_state.form_submitted:
    st.markdown(f"""
    <div class='analysis-box'>
        <h3>✨ Your Skin Analysis</h3>
        <p><b>Jenis Kulit:</b> <span style="color:#c71585;">{', '.join(skin)}</span></p>
        <p><b>Concern Kulit:</b> <span style="color:#c71585;">{', '.join(concern)}</span></p>
    </div>
    """, unsafe_allow_html=True)

    products = load_relevant_products(subcat_list=subcat_selected, skin_types=skin, concerns=concern,
                                      budget_min=budget_min, budget_max=budget_max, data_dir="data")

    with st.spinner("💬 AI is analyzing the best products..."):
        summaries = analyze_products_batch(products[:6], skin, concern, OPENROUTER_API_KEY)

    final_products = []
    for p in products:
        if p["id"] in summaries and is_positive_summary(summaries[p["id"]]):
            p["ai_summary"] = summaries[p["id"]]
            final_products.append(p)

    st.session_state.final_products = final_products

    if not final_products:
        st.warning("No matching products found.")
    else:
        with st.spinner("🩺 AI Dermatologist is writing tips..."):
            tip = get_dermatologist_tip_cached(final_products, skin, concern, api_key=OPENROUTER_API_KEY)

        st.markdown(f"""
        <div class='tip-box'>
            <h4>🩺 Skincare Tips from AI Dermatologist</h4>
            <p>{tip}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🧴 Recommended Products")
        cols = st.columns(3)
        for idx, p in enumerate(final_products):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class='product-card'>
                    <img src="{p['img']}" class='product-image'/>
                    <div class='product-name'>{p['name']}</div>
                    <div class='product-brand'>{p['brand']}</div>
                    <div class='product-price'>Rp{p['price']:,}</div>
                    <div class='product-rating'>⭐ {p['rating']:.1f} / 5</div>
                    <details>
                        <summary class='details-summary'>💡 Why It Suits You</summary>
                        <p class='details-content'>{p['why']}</p>
                    </details>
                    <details>
                        <summary class='details-summary'>🧪 Ingredients</summary>
                        <p class='details-content'>{p['ingredients']}</p>
                    </details>
                    <details>
                        <summary class='details-summary'>🧴 How to Use</summary>
                        <p class='details-content'>{p['how_to_use']}</p>
                    </details>
                    <details>
                        <summary class='details-summary'>🧠 AI Review Summary</summary>
                        <p class='details-content'>{p.get("ai_summary", "Not available yet")}</p>
                    </details>
                    <a href="{p['url']}" target="_blank" style='display:inline-block;margin-top:15px;font-weight:500;color:#c71585;text-decoration:none;'>🌐 View Product</a>
                </div>
                """, unsafe_allow_html=True)

        if st.button("💬 Ask AI About These Products"):
            st.session_state.show_chat = True

# Chat Session
if st.session_state.show_chat and st.session_state.final_products:
    st.markdown("### 🤖 Chat with Your Skincare AI")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(f"<div class='chat-bubble'>{msg['content']}</div>", unsafe_allow_html=True)

    user_msg = st.chat_input("Ask anything about the products...")
    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(f"<div class='chat-bubble'>{user_msg}</div>", unsafe_allow_html=True)

        context = ""
        for p in st.session_state.final_products:
            context += f"Product: {p['name']} ({p['brand']})\n- Ingredients: {p['ingredients']}\n- Summary: {p['ai_summary']}\n\n"

        final_prompt = f"""
Recommended products for user with skin type: {', '.join(skin)} and concerns: {', '.join(concern)}.
Use this data to answer their question as an AI beauty advisor.

{context}

Question: {user_msg}
"""

        with st.chat_message("assistant"):
            with st.spinner("💬 AI is responding..."):
                response_text = ""
                box = st.empty()
                for token in get_chat_response_streaming(OPENROUTER_API_KEY, final_prompt):
                    response_text += token
                    box.markdown(f"<div class='chat-bubble'>{response_text}</div>", unsafe_allow_html=True)
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
