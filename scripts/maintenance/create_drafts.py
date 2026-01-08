from pathlib import Path
import json
from datetime import datetime, timezone

SRC = Path("data/inbox/unified.json")
DST = Path("data/inbox/rascunhos.json")

def criar_rascunhos():
    if not SRC.exists():
        print("❌ unified.json não encontrado.")
        return

    itens = json.loads(SRC.read_text(encoding="utf-8"))
    agora = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    rascunhos = []

    for item in itens:
        rascunhos.append({
            **item,
            "status": "draft",
            "pinned": False,
            "created_at": agora
        })

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(
        json.dumps(rascunhos, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"📝 {len(rascunhos)} rascunhos criados em {DST}")

if __name__ == "__main__":
    criar_rascunhos()
