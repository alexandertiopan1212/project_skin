import os
import json
import re
from collections import defaultdict

def clean_html(raw_html: str) -> str:
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html or '').replace('\n', ' ').strip()

def normalize(text):
    return text.lower().strip().replace(" ", "_").replace("/", "_").replace("&", "and")

def text_contains_keywords(text, keywords):
    text = text.lower()
    return sum(1 for kw in keywords if kw.lower() in text)

def load_relevant_products(subcat_list, skin_types=[], concerns=[], data_dir="data", budget_min=0, budget_max=10_000_000):
    all_keywords = [kw.lower() for kw in (skin_types + concerns)]
    normalized_subcats = [normalize(sub.split(" - ")[1]) for sub in subcat_list]
    subcat_to_products = defaultdict(list)

    detail_path = os.path.join(data_dir, "product_details_all_subcategories_20250429_083919.json")
    with open(detail_path, encoding="utf-8") as f:
        detail_data = json.load(f)
    detail_lookup = {item["product_id"]: item for item in detail_data}

    for fname in os.listdir(data_dir):
        if not fname.endswith(".json") or fname.startswith("product_details_"):
            continue
        fname_norm = fname.lower()
        matched_subcat = next((sc for sc in normalized_subcats if sc in fname_norm), None)
        if not matched_subcat:
            continue

        filepath = os.path.join(data_dir, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for item in data:
                    price = item.get("price_after_discount", 0)
                    if price < budget_min or price > budget_max:
                        continue
                    if not item.get("is_in_stock", False):
                        continue

                    reviews = item.get("reviews", [])
                    matched_reviews = []
                    keyword_review_hits = 0

                    for rev in reviews:
                        review_text = clean_html(rev.get("review", {}).get("review_text", ""))
                        user_skin = rev.get("user", {}).get("skin_types", [])
                        match_user = any(s.lower() in map(str.lower, user_skin) for s in skin_types + concerns)
                        keyword_hits = text_contains_keywords(review_text, all_keywords)

                        if match_user:
                            matched_reviews.append(review_text)
                        keyword_review_hits += keyword_hits

                    if keyword_review_hits < 2:
                        continue

                    detail = detail_lookup.get(item["id"], {})
                    description = clean_html(detail.get("description", ""))
                    how_to_use = clean_html(detail.get("how_to_use", ""))
                    ingredients = clean_html(detail.get("ingredients", ""))

                    subcat_to_products[matched_subcat].append({
                        "id": item["id"],
                        "name": item["name"],
                        "brand": item["brand"],
                        "price": price,
                        "rating": item.get("average_rating", 0),
                        "img": item.get("image_url", ""),
                        "url": item.get("product_url", "#"),
                        "why": description + "..." if description else "Cocok berdasarkan review dengan concern/skin type kamu.",
                        "ingredients": ingredients or "Tidak ada info bahan.",
                        "how_to_use": how_to_use or "Tidak ada info cara pakai.",
                        "reviews_text": "\n\n".join(matched_reviews) or "Belum ada review relevan.",
                        "subcategory": matched_subcat
                    })
            except Exception as e:
                print(f"Gagal parsing {fname}: {e}")

    final_products = []
    for subcat in normalized_subcats:
        top_products = sorted(subcat_to_products[subcat], key=lambda x: (x["rating"]), reverse=True)
        final_products.extend(top_products[:3])

    return sorted(final_products, key=lambda x: x["rating"], reverse=True)[:10]
