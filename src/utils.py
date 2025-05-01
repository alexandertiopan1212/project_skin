import os
import json
import hashlib
from src.ai_response import get_ai_response

SUMMARY_CACHE_FILE = "data/ai_summaries_advanced.json"
TIP_CACHE_FILE = "data/ai_tips_cache.json"

summary_cache = {}
tip_cache = {}

if os.path.exists(SUMMARY_CACHE_FILE):
    with open(SUMMARY_CACHE_FILE, encoding="utf-8") as f:
        summary_cache = json.load(f)

if os.path.exists(TIP_CACHE_FILE):
    with open(TIP_CACHE_FILE, encoding="utf-8") as f:
        tip_cache = json.load(f)

def save_cache():
    with open(SUMMARY_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_cache, f, ensure_ascii=False, indent=2)
    with open(TIP_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(tip_cache, f, ensure_ascii=False, indent=2)

def hash_prompt_key(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def is_positive_summary(summary: str) -> bool:
    summary = summary.lower()
    negative_phrases = [
        "kurang cocok", "tidak cocok", "kurang ideal", "tidak efektif",
        "tidak memberikan solusi maksimal", "tidak disarankan"
    ]
    return not any(phrase in summary for phrase in negative_phrases)

def analyze_products_batch(products: list, skin_types: list, concerns: list, api_key: str) -> dict:
    summaries = {}
    batch_prompt = ""

    for p in products:
        hash_key = hash_prompt_key(p["name"] + ",".join(skin_types) + ",".join(concerns))
        if hash_key in summary_cache:
            summaries[p["id"]] = summary_cache[hash_key]
        else:
            batch_prompt += f"""Produk: {p['name']} ({p['brand']})
Ingredients: {p['ingredients']}
Review: {p['reviews_text'][:300]}
Deskripsi: {p['why']}
Cara Pakai: {p['how_to_use']}

"""

    if batch_prompt:
        prompt = f"""
Berikut beberapa produk skincare. Tolong analisis dalam 3-5 kalimat per produk, berdasarkan jenis kulit: {', '.join(skin_types)} dan concern: {', '.join(concerns)}.

{batch_prompt}

Tulis analisis per produk secara terpisah. Gunakan gaya ramah seperti beauty advisor. Jangan rekomendasikan produk yang tidak cocok.
"""
        result = get_ai_response(api_key, prompt)
        blocks = result.strip().split("\n\n")

        for block in blocks:
            for p in products:
                if p["name"].lower() in block.lower():
                    key = hash_prompt_key(p["name"] + ",".join(skin_types) + ",".join(concerns))
                    summary_cache[key] = block.strip()
                    summaries[p["id"]] = block.strip()
                    break

        save_cache()

    return summaries

def get_dermatologist_tip_cached(products: list, skin_types: list, concerns: list, api_key: str) -> str:
    profile_key = hash_prompt_key(",".join(skin_types) + ",".join(concerns) + ",".join(sorted(p["ingredients"] for p in products)))
    if profile_key in tip_cache:
        return tip_cache[profile_key]

    product_info = [f"{p['name']} dari {p['brand']} mengandung: {p['ingredients']}" for p in products[:5]]
    product_summary = "\n".join(product_info)

    prompt = f"""
Berikan saran skincare seperti dermatologis profesional berdasarkan:
- Jenis Kulit: {', '.join(skin_types)}
- Concern: {', '.join(concerns)}

Produk yang direkomendasikan:
{product_summary}

Berikan 3–5 kalimat tips. Jangan bertentangan dengan kandungan produk.
"""
    result = get_ai_response(api_key=api_key, user_prompt=prompt)
    tip_cache[profile_key] = result
    save_cache()
    return result
