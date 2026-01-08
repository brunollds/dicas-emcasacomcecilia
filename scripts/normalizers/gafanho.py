import json
from pathlib import Path
from datetime import datetime

IN_FILE = Path("data/raw/gafanho.json")
OUT_FILE = Path("data/inbox/gafanho_normalized.json")

def parse_price(price_str):
    if not price_str:
        return None
    try:
        return float(
            price_str.replace("R$", "")
                     .replace(".", "")
                     .replace(",", ".")
                     .strip()
        )
    except Exception:
        return None

def parse_date(date_str):
    # formato: "29/12 14:31"
    try:
        dt = datetime.strptime(date_str + f"/{datetime.now().year}", "%d/%m %H:%M/%Y")
        return dt.isoformat()
    except Exception:
        return None

def normalize():
    print("🧹 Normalizando Gafanhoto…")

    data = json.loads(IN_FILE.read_text(encoding="utf-8"))
    out = []

    for p in data:
        item = {
            "id": f"gafanho-{p['id']}",
            "source": "gafanho",
            "title": p.get("title"),
            "price": parse_price(p.get("price")),
            "price_text": p.get("price"),
            "store": p.get("storeName"),
            "image": p.get("imageUrlBig") or p.get("imageUrlMini"),
            "url": p.get("links"),
            "published_at": parse_date(p.get("publicationDate")),
            "raw": p
        }
        out.append(item)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ {len(out)} itens normalizados em {OUT_FILE}")

if __name__ == "__main__":
    normalize()
