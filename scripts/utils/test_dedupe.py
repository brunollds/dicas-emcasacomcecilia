import json
from pathlib import Path
from deduplicator import is_duplicate

DATA = Path("data/inbox")

files = list(DATA.glob("*.json"))
items = []

for f in files:
    items.extend(json.loads(f.read_text(encoding="utf-8")))

print(f"🔎 Testando {len(items)} itens...")

dupes = []

for i, a in enumerate(items):
    for b in items[i+1:]:
        if a["source"] != b["source"] and is_duplicate(a, b):
            dupes.append((a["id"], b["id"]))

print(f"⚠️ Duplicatas encontradas: {len(dupes)}")
for d in dupes[:10]:
    print(" ↪", d)
