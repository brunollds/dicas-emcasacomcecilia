import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

STOPWORDS = {
    "com", "para", "de", "da", "do", "e",
    "novo", "nova", "original", "oficial",
    "ml", "kg", "g", "l", "un", "pack"
}

def normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^\w\s]", " ", title)
    words = [
        w for w in title.split()
        if w not in STOPWORDS and len(w) > 2
    ]
    return " ".join(words)

def extract_store_domain(url: str | None) -> str | None:
    if not url:
        return None
    try:
        netloc = urlparse(url).netloc
        return netloc.replace("www.", "")
    except Exception:
        return None

def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def price_close(p1: float | None, p2: float | None, tolerance=0.05) -> bool:
    if not p1 or not p2:
        return False
    return abs(p1 - p2) / min(p1, p2) <= tolerance

def is_duplicate(item_a: dict, item_b: dict) -> bool:
    # 1️⃣ Mesmo domínio de loja
    dom_a = extract_store_domain(item_a.get("url"))
    dom_b = extract_store_domain(item_b.get("url"))
    if dom_a and dom_b and dom_a == dom_b:
        return True

    # 2️⃣ Título parecido
    t1 = normalize_title(item_a.get("title", ""))
    t2 = normalize_title(item_b.get("title", ""))
    sim = title_similarity(t1, t2)

    if sim >= 0.85 and price_close(item_a.get("price"), item_b.get("price")):
        return True

    return False
