import json
from pathlib import Path
from datetime import datetime

IN_FILE = Path("data/raw/promobit.json")
OUT_FILE = Path("data/inbox/promobit_normalized.json")

def parse_date(dt_str: str) -> str:
    """
    Ex: 2025-12-29T08:31:40-0300
    """
    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S%z")
    return dt.isoformat()

def coletar_promobit():
    print("🧹 Normalizando Promobit…")

    raw_items = json.loads(IN_FILE.read_text(encoding="utf-8"))
    normalized = []

    for item in raw_items:
        price = item.get("offerPrice")
        price_old = item.get("offerOldPrice") or None

        normalized.append({
            "id": f"promobit-{item['offerId']}",
            "source": "promobit",
            "title": item.get("offerTitle"),
            "price": float(price) if price is not None else None,
            "price_old": float(price_old) if price_old else None,
            "price_text": f"R$ {price}".replace(".", ",") if price else None,
            "store": item.get("storeName"),
            "store_domain": item.get("storeDomain"),
            "image": (
                f"https://i.promobit.com.br{item['offerPhoto']}"
                if item.get("offerPhoto")
                else None
            ),
            "url": f"https://www.promobit.com.br/oferta/{item['offerSlug']}",
            "published_at": parse_date(item["offerPublished"]),
            "raw": item
        })

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"✅ {len(normalized)} itens normalizados em {OUT_FILE}")

if __name__ == "__main__":
    coletar_promobit()
