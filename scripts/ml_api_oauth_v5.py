"""
API do Mercado Livre com OAuth2 (v5)
Objetivo: pegar preço automático mesmo quando a URL é de catálogo (/p/MLBxxxx).

Estratégia de resolução:
1) Se for item_id: /items/{id}
2) Se for product_id: /products/{id}
   - Se existir buy_box_winner.item_id -> usa
   - Senão tenta /products/{id}/items para listar publicações concorrentes
   - Senão tenta children_ids/pickers (profundidade limitada)

Preço:
- Preferir /items/{item_id}/sale_price (amount / regular_amount)
- Fallback: campos price/original_price do /items (pode falhar conforme políticas)

Observação:
- Não usa proxy/rotacionar IP nem técnicas de evasão.
"""

import json
import re
from pathlib import Path

import requests

from ml_oauth import get_access_token, API_BASE


MAX_DEPTH = 6
DEBUG_DIR = Path(".")
UA = "Mozilla/5.0 (compatible; dicas.emcasacomcecilia.com; +https://dicas.emcasacomcecilia.com)"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": UA,
    }


def extrair_alvo(url_or_id: str):
    """
    Retorna ("product"|"item"|"unknown", "MLB...") ou (None, None)
    """
    if not url_or_id:
        return (None, None)

    s = url_or_id.strip()

    clean = s.upper().replace("-", "")
    if re.match(r"^MLB\d+$", clean):
        return ("unknown", clean)

    m = re.search(r"/p/(MLB\d+)", s, re.IGNORECASE)
    if m:
        return ("product", m.group(1).upper())

    m = re.search(r"(MLB)-?(\d+)", s, re.IGNORECASE)
    if m:
        return ("item", f"MLB{m.group(2)}")

    if "/sec/" in s:
        try:
            r = requests.get(s, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
            return extrair_alvo(r.url)
        except Exception:
            return (None, None)

    return (None, None)


def _save_debug(name: str, payload: dict):
    try:
        (DEBUG_DIR / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _extract_item_ids_from_anything(obj):
    """
    Varre estrutura e tenta coletar IDs MLB... que parecem item_id.
    Atenção: product_id também tem formato MLB\d+, então isso é apenas fallback.
    """
    ids = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("item_id", "id"):
                    if isinstance(v, str) and re.match(r"^MLB\d+$", v.upper()):
                        ids.add(v.upper())
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return list(ids)


def listar_items_de_product(product_id: str, token: str):
    """
    Tenta obter as publicações concorrentes via /products/{product_id}/items
    (citada em docs de competição de catálogo).
    Retorna lista de item_ids.
    """
    h = _headers(token)
    url = f"{API_BASE}/products/{product_id}/items"
    r = requests.get(url, headers=h, timeout=20)

    if r.status_code != 200:
        return []

    try:
        data = r.json()
    except Exception:
        return []

    items = []

    # Formatos comuns: lista direta ou dict com results/items
    if isinstance(data, list):
        for e in data:
            if isinstance(e, str) and re.match(r"^MLB\d+$", e.upper()):
                items.append(e.upper())
            elif isinstance(e, dict):
                _id = e.get("id") or e.get("item_id")
                if isinstance(_id, str) and re.match(r"^MLB\d+$", _id.upper()):
                    items.append(_id.upper())
    elif isinstance(data, dict):
        for key in ("results", "items"):
            if isinstance(data.get(key), list):
                for e in data[key]:
                    if isinstance(e, str) and re.match(r"^MLB\d+$", e.upper()):
                        items.append(e.upper())
                    elif isinstance(e, dict):
                        _id = e.get("id") or e.get("item_id")
                        if isinstance(_id, str) and re.match(r"^MLB\d+$", _id.upper()):
                            items.append(_id.upper())
        # fallback: varredura
        if not items:
            items = _extract_item_ids_from_anything(data)

    # dedupe preservando ordem
    seen = set()
    out = []
    for it in items:
        if it not in seen:
            out.append(it)
            seen.add(it)
    return out


def resolver_item_id(ml_id: str, token: str, depth: int = 0, visited=None):
    """
    Resolve qualquer MLB... para um item_id.
    """
    if visited is None:
        visited = set()
    if ml_id in visited:
        return (None, None)
    visited.add(ml_id)

    if depth > MAX_DEPTH:
        return (None, None)

    h = _headers(token)

    # 1) tenta como item
    r_item = requests.get(f"{API_BASE}/items/{ml_id}", headers=h, timeout=15)
    if r_item.status_code == 200:
        return ("item", ml_id)

    # se deu 401/403, ainda podemos tentar resolver via product e depois item.
    # se deu 404, é forte indício de que não é item_id.

    # 2) tenta como product
    r_prod = requests.get(f"{API_BASE}/products/{ml_id}", headers=h, timeout=20)
    if r_prod.status_code != 200:
        return (None, None)

    prod = r_prod.json()

    # salva dump completo do product para debug
    _save_debug(f"debug_product_{ml_id}.json", prod)

    winner = prod.get("buy_box_winner") or {}
    item_id = winner.get("item_id")
    if not item_id and isinstance(winner.get("item"), dict):
        item_id = winner["item"].get("id")

    if item_id and re.match(r"^MLB\d+$", str(item_id).upper()):
        return ("item", str(item_id).upper())

    # 2b) fallback forte: listar publicações concorrentes do product
    candidates = listar_items_de_product(ml_id, token)
    if candidates:
        # tenta o primeiro que realmente responda /items 200
        for cand in candidates[:10]:
            rr = requests.get(f"{API_BASE}/items/{cand}", headers=h, timeout=15)
            if rr.status_code == 200:
                return ("item", cand)

    # 2c) fallback: children_ids (produto pai)
    children = prod.get("children_ids") or []
    if isinstance(children, list):
        for child in children[:20]:
            if isinstance(child, str) and re.match(r"^MLB\d+$", child.upper()):
                _, resolved = resolver_item_id(child.upper(), token, depth=depth + 1, visited=visited)
                if resolved:
                    return ("item", resolved)

    # 2d) fallback: pickers -> products -> product_id
    pickers = prod.get("pickers") or []
    if isinstance(pickers, list):
        for p in pickers:
            if not isinstance(p, dict):
                continue
            prods = p.get("products") or []
            if isinstance(prods, list):
                for pr in prods[:20]:
                    if isinstance(pr, dict):
                        pid = pr.get("product_id") or pr.get("id")
                        if isinstance(pid, str) and re.match(r"^MLB\d+$", pid.upper()):
                            _, resolved = resolver_item_id(pid.upper(), token, depth=depth + 1, visited=visited)
                            if resolved:
                                return ("item", resolved)

    return (None, None)


def buscar_sale_price(item_id: str, token: str):
    h = _headers(token)
    r = requests.get(f"{API_BASE}/items/{item_id}/sale_price", headers=h, timeout=20)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


def buscar_produto(item_id: str):
    token = get_access_token()
    if not token:
        return {"erro": "Sem token de acesso. Execute sua autenticação OAuth primeiro."}

    h = _headers(token)

    r = requests.get(f"{API_BASE}/items/{item_id}", headers=h, timeout=20)

    if r.status_code == 404:
        return {"erro": "Item não encontrado (ID inválido para /items)", "id": item_id}
    if r.status_code == 401:
        return {"erro": "Token expirado (401). Refaça a autenticação.", "id": item_id}
    if r.status_code == 403:
        return {"erro": "Acesso bloqueado (403) ao /items. Pode ser política/scope.", "id": item_id}

    r.raise_for_status()
    data = r.json()

    imagem = None
    if data.get("pictures"):
        imagem = data["pictures"][0].get("secure_url")
    if not imagem:
        imagem = (data.get("thumbnail") or "").replace("http:", "https:")

    sp = buscar_sale_price(item_id, token)
    preco_atual = None
    preco_regular = None
    moeda = None
    if sp:
        preco_atual = sp.get("amount")
        preco_regular = sp.get("regular_amount")
        moeda = sp.get("currency_id")

    # fallback (caso sale_price falhe)
    if preco_atual is None:
        preco_atual = data.get("price")
    if preco_regular is None:
        preco_regular = data.get("original_price")

    return {
        "id": data.get("id"),
        "titulo": data.get("title"),
        "preco": preco_atual,
        "preco_original": preco_regular,
        "moeda": moeda or data.get("currency_id"),
        "imagem": imagem,
        "link": data.get("permalink"),
        "disponivel": (data.get("available_quantity") or 0) > 0,
        "quantidade": data.get("available_quantity"),
        "frete_gratis": data.get("shipping", {}).get("free_shipping", False),
        "condicao": data.get("condition"),
        "vendedor_id": data.get("seller_id"),
        "categoria_id": data.get("category_id"),
    }


def buscar_por_url(url_or_id: str):
    tipo, ml_id = extrair_alvo(url_or_id)
    if not ml_id:
        return {"erro": "Não foi possível extrair um ID MLB da entrada", "entrada": url_or_id}

    token = get_access_token()
    if not token:
        return {"erro": "Sem token de acesso. Execute sua autenticação OAuth primeiro."}

    # se veio como item, tenta direto
    if tipo == "item":
        return buscar_produto(ml_id)

    # product/unknown: resolve para item_id
    _, item_id = resolver_item_id(ml_id, token, depth=0, visited=set())
    if not item_id:
        return {
            "erro": "Não consegui resolver esse MLB como item (sem buy_box_winner e sem itens concorrentes).",
            "product_id": ml_id,
        }

    return buscar_produto(item_id)


def main():
    print("=" * 60)
    print("🛒 API Mercado Livre (OAuth2) - v5")
    print("=" * 60)

    token = get_access_token()
    if token:
        print("✅ Token válido!")
    else:
        print("❌ Sem token. Rode seu OAuth primeiro.")
        return

    url_teste = "https://www.mercadolivre.com.br/poltrona-reclinavel-damie/p/MLB37776701"
    print(f"\n📍 Testando: {url_teste[:72]}...")
    print("-" * 50)

    dados = buscar_por_url(url_teste)

    if "erro" not in dados:
        print(f"✅ {dados.get('titulo')}")
        print(f"   💰 Preço: {dados.get('preco')}  |  Riscado: {dados.get('preco_original')}")
        print(f"   🔗 {dados.get('link')}")
        print(f"   🖼️ {dados.get('imagem')}")
    else:
        print(f"❌ {dados['erro']}")
        if "product_id" in dados:
            print(f"   product_id: {dados['product_id']}")
        if "entrada" in dados:
            print(f"   entrada: {dados['entrada']}")

    print("\n(Se existir, confira o arquivo debug_product_MLB37776701.json na pasta.)")
    print("=" * 60)


if __name__ == "__main__":
    main()
