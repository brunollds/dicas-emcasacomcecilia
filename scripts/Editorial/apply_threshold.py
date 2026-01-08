import json
from pathlib import Path
from datetime import datetime, timezone

# ---- Paths ----
IN_FILE = Path("data/inbox/ranked.json")
OUT_DRAFTS = Path("data/inbox/rascunhos.json")

def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def load_json(path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def apply_threshold():
    if not IN_FILE.exists():
        print("❌ ranked.json não encontrado.")
        return

    ranked = load_json(IN_FILE)
    drafts = []
    seen_ids = set()

    for item in ranked:
        item_id = item.get("id")
        if not item_id or item_id in seen_ids:
            continue

        seen_ids.add(item_id)

        item["editorial_checked_at"] = now_utc()
        drafts.append(item)

    save_json(OUT_DRAFTS, drafts)

    print(f"📝 Rascunhos: {len(drafts)}")
    print("✅ Modo 3 aplicado: nenhum item rejeitado automaticamente.")

if __name__ == "__main__":
    apply_threshold()
