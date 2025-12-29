import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

PRODUCTS_FILE = Path("products.json")
PAYLOAD_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else None


def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)


def load_json(path: Path):
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        fail(f"Erro ao ler {path}: {e}")


def save_json(path: Path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def gerar_id():
    # curto, único e legível
    return f"promo-{uuid.uuid4().hex[:8]}"


def main():
    if not PAYLOAD_FILE or not PAYLOAD_FILE.exists():
        fail("Payload não encontrado")

    if not PRODUCTS_FILE.exists():
        fail("products.json não encontrado")

    payload = load_json(PAYLOAD_FILE)
    products = load_json(PRODUCTS_FILE)

    if not isinstance(products, list):
        fail("products.json precisa ser um array")

    # ---- validação mínima ----
    obrigatorios = ["produto", "preco", "loja", "link"]
    for campo in obrigatorios:
        if not payload.get(campo):
            fail(f"Campo obrigatório ausente: {campo}")

    if not isinstance(payload["preco"], (int, float)):
        fail("Preço inválido")

    # ---- evitar duplicatas grosseiras ----
    for item in products:
        if (
            item.get("produto") == payload["produto"]
            and item.get("loja") == payload["loja"]
            and abs(item.get("preco", 0) - payload["preco"]) < 0.01
        ):
            print("⚠️ Promoção aparentemente duplicada. Abortando.")
            sys.exit(0)

    # ---- normalização ----
    novo = {
        "id": gerar_id(),
        "produto": payload["produto"].strip(),
        "preco": float(payload["preco"]),
        "precoAntigo": payload.get("precoAntigo"),
        "loja": payload["loja"],
        "link": payload["link"],
        "imagem": payload.get("imagem"),
        "info": payload.get("info"),
        "categoria": payload.get("categoria", "Outros"),
        "origem": payload.get("origem", "manual"),
        "status": "ativo",
        "criado_em": datetime.utcnow().isoformat() + "Z"
    }

    # ---- inserir no topo ----
    products.insert(0, novo)

    save_json(PRODUCTS_FILE, products)

    print(f"✅ Promoção publicada: {novo['id']}")


if __name__ == "__main__":
    main()
