from pathlib import Path
import json
from datetime import datetime, timezone, timedelta

# Configurações
INBOX_FILE = Path("data/inbox/rascunhos.json")
TTL_HOURS = 24

def parse_iso(date_str: str) -> datetime:
    """
    Converte ISO8601 com Z ou +00:00 para datetime UTC
    """
    if date_str.endswith("Z"):
        date_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(date_str).astimezone(timezone.utc)

def cleanup_drafts():
    if not INBOX_FILE.exists():
        print("⚠️ Nenhum rascunho encontrado (arquivo inexistente).")
        return

    data = json.loads(INBOX_FILE.read_text(encoding="utf-8"))

    agora = datetime.now(timezone.utc)
    ttl = timedelta(hours=TTL_HOURS)

    mantidos = []
    removidos = []

    for item in data:
        status = item.get("status", "draft")
        pinned = item.get("pinned", False)
        created_at = item.get("created_at")

        # Segurança máxima: se faltar data, mantém
        if not created_at:
            mantidos.append(item)
            continue

        try:
            criado_em = parse_iso(created_at)
        except Exception:
            mantidos.append(item)
            continue

        expirado = (agora - criado_em) > ttl

        if status == "draft" and not pinned and expirado:
            removidos.append(item)
        else:
            mantidos.append(item)

    INBOX_FILE.write_text(
        json.dumps(mantidos, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("🧹 Limpeza de rascunhos concluída")
    print(f"📦 Total antes: {len(data)}")
    print(f"🗑️ Removidos: {len(removidos)}")
    print(f"✅ Mantidos: {len(mantidos)}")

    if removidos:
        print("\n🗂️ IDs removidos:")
        for item in removidos[:10]:
            print(" -", item.get("id"))
        if len(removidos) > 10:
            print(f"   ... +{len(removidos) - 10} itens")

if __name__ == "__main__":
    cleanup_drafts()
