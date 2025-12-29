"""\
API do Mercado Livre com OAuth2 (v4)

O que este script resolve (do seu caso real):
- URLs de catálogo (/p/MLBxxxx) NÃO são um anúncio (item). São um *product_id* do catálogo.
- Em alguns produtos, o campo `buy_box_winner` vem **null** no /products/{product_id}.
  Isso pode acontecer, por exemplo, quando:
  - o produto é um “pai” e você precisa descer para um filho/variante (children_ids / pickers)
  - não há oferta ganhadora disponível no momento

Estratégia v4:
1) Detecta se é /p/MLB... (catálogo) ou MLB... (id)
2) Para catálogo:
   - tenta pegar buy_box_winner.item_id em /products/{product_id}
   - se vier null, faz fallback navegando em children_ids e/ou pickers[*].products[*].product_id
3) Com item_id, busca preço via /items/{item_id}/sale_price (fallback: /items/{item_id}.price)

Obs importante:
- Mesmo resolvendo item_id, alguns itens podem retornar 403 em /items por políticas/permissões.
  Nesse caso o script vai devolver um erro bem explícito.
"""

from __future__ import annotations

import json
import re
from collections import deque
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import requests

from ml_oauth import get_access_token, API_BASE


# =====================================================
# HTTP
# =====================================================

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; dicas.emcasacomcecilia.com; +https://dicas.emcasacomcecilia.com)",
    }


# =====================================================
# EXTRAÇÃO DE ID
# =====================================================

def extrair_alvo(url_or_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Retorna ("product"|"item"|"unknown", "MLB...") ou (None, None)."""
    if not url_or_id:
        return (None, None)

    s = url_or_id.strip()

    # Caso o usuário passe só o ID (MLB123...) ou MLB-123...
    m = re.fullmatch(r"\s*(MLB)-?(\d+)\s*", s, flags=re.IGNORECASE)
    if m:
        return ("unknown", f"MLB{m.group(2)}")

    # /p/MLB123456  -> catálogo (product_id)
    m = re.search(r"/p/(MLB\d+)", s, re.IGNORECASE)
    if m:
        return ("product", m.group(1).upper())

    # .../MLB-1234567890-... -> anúncio (item_id)
    m = re.search(r"(MLB)-?(\d+)", s, re.IGNORECASE)
    if m:
        return ("item", f"MLB{m.group(2)}")

    # Short link /sec/ -> segue redirect e tenta de novo
    if "/sec/" in s:
        try:
            r = requests.get(s, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
            return extrair_alvo(r.url)
        except Exception:
            return (None, None)

    return (None, None)


# =====================================================
# PRODUTOS (CATÁLOGO) -> ITEM_ID
# =====================================================

def _get_product(product_id: str, token: str) -> Optional[Dict[str, Any]]:
    r = requests.get(f"{API_BASE}/products/{product_id}", headers=_headers(token), timeout=20)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


def _extract_winner_item_id(product_json: Dict[str, Any]) -> Optional[str]:
    winner = product_json.get("buy_box_winner")
    if not winner:
        return None

    # Formato comum: {"item_id":"MLB..."}
    item_id = winner.get("item_id") if isinstance(winner, dict) else None

    # Formato alternativo: {"item": {"id":"MLB..."}}
    if not item_id and isinstance(winner, dict) and isinstance(winner.get("item"), dict):
        item_id = winner["item"].get("id")

    if isinstance(item_id, str) and item_id.upper().startswith("MLB"):
        return item_id.upper().replace("-", "")
    return None


def _child_product_ids(product_json: Dict[str, Any]) -> List[str]:
    """Extrai possíveis product_ids filhos a partir de children_ids e pickers."""
    out: List[str] = []

    # children_ids: ["MLB...", ...]
    children = product_json.get("children_ids")
    if isinstance(children, list):
        for cid in children:
            if isinstance(cid, str) and re.match(r"^MLB\d+$", cid, flags=re.IGNORECASE):
                out.append(cid.upper())

    # pickers: [ { picker_id, products: [ { product_id: "MLB..." }, ... ] }, ...]
    pickers = product_json.get("pickers")
    if isinstance(pickers, list):
        for p in pickers:
            if not isinstance(p, dict):
                continue
            prods = p.get("products")
            if isinstance(prods, list):
                for pr in prods:
                    if isinstance(pr, dict):
                        pid = pr.get("product_id") or pr.get("id")
                        if isinstance(pid, str) and re.match(r"^MLB\d+$", pid, flags=re.IGNORECASE):
                            out.append(pid.upper())

    # Alguns retornos podem ter parent_id (subir e tentar também)
    parent_id = product_json.get("parent_id")
    if isinstance(parent_id, str) and re.match(r"^MLB\d+$", parent_id, flags=re.IGNORECASE):
        out.append(parent_id.upper())

    # dedup mantendo ordem
    seen: Set[str] = set()
    uniq: List[str] = []
    for pid in out:
        if pid not in seen:
            uniq.append(pid)
            seen.add(pid)
    return uniq


def resolver_item_id_de_catalogo(product_id: str, token: str, *, max_depth: int = 2, max_visits: int = 40) -> Tuple[Optional[str], Dict[str, Any]]:
    """Tenta resolver um /p/MLB... para um item_id navegando em filhos.

    Retorna (item_id ou None, debug_info)
    """
    visited: Set[str] = set()
    q: deque[Tuple[str, int]] = deque([(product_id, 0)])
    last_product: Optional[Dict[str, Any]] = None

    while q and len(visited) < max_visits:
        pid, depth = q.popleft()
        if pid in visited:
            continue
        visited.add(pid)

        pj = _get_product(pid, token)
        if not pj:
            continue
        last_product = pj

        winner_item = _extract_winner_item_id(pj)
        if winner_item:
            return winner_item, {
                "resolved_from_product_id": pid,
                "visited": len(visited),
                "depth": depth,
            }

        if depth >= max_depth:
            continue

        for child_pid in _child_product_ids(pj):
            if child_pid not in visited:
                q.append((child_pid, depth + 1))

    # Falhou
    dbg: Dict[str, Any] = {
        "visited": len(visited),
        "max_depth": max_depth,
        "note": "Sem buy_box_winner encontrado. Pode ser produto sem oferta ganhadora ou precisa selecionar variação específica.",
    }

    # Se tiver um product_json pra inspecionar, extraímos um resumo útil
    if last_product:
        dbg.update(
            {
                "last_product_id": last_product.get("id"),
                "status": last_product.get("status"),
                "children_ids_count": len(last_product.get("children_ids") or []) if isinstance(last_product.get("children_ids"), list) else 0,
                "has_pickers": isinstance(last_product.get("pickers"), list),
            }
        )
    return None, dbg


# =====================================================
# ITEM (ANÚNCIO) -> PREÇO
# =====================================================

def buscar_sale_price(item_id: str, token: str) -> Optional[Dict[str, Any]]:
    r = requests.get(f"{API_BASE}/items/{item_id}/sale_price", headers=_headers(token), timeout=20)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


def buscar_produto(item_id: str) -> Dict[str, Any]:
    token = get_access_token()
    if not token:
        return {"erro": "Sem token de acesso. Execute ml_oauth.py primeiro."}

    try:
        r = requests.get(f"{API_BASE}/items/{item_id}", headers=_headers(token), timeout=20)

        if r.status_code == 404:
            return {"erro": "Item não encontrado (ID inválido para /items)", "id": item_id}
        if r.status_code == 401:
            return {"erro": "Token expirado (401). Rode ml_oauth.py de novo.", "id": item_id}
        if r.status_code == 403:
            return {
                "erro": "Acesso bloqueado (403) ao /items. Hoje o ML pode restringir leitura de itens que não são do usuário/token.",
                "id": item_id,
            }

        r.raise_for_status()
        data = r.json()

        # imagem principal
        imagem = None
        if data.get("pictures"):
            imagem = data["pictures"][0].get("secure_url")
            if imagem:
                imagem = imagem.replace("-O.jpg", "-F.jpg").replace("-I.jpg", "-F.jpg")
        if not imagem:
            imagem = (data.get("thumbnail") or "").replace("http:", "https:")

        # preço via sale_price
        sp = buscar_sale_price(item_id, token)
        preco_atual = None
        preco_regular = None
        moeda = None
        if sp:
            preco_atual = sp.get("amount")
            preco_regular = sp.get("regular_amount")
            moeda = sp.get("currency_id")

        # fallback
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
            "imagens": [p.get("secure_url") for p in data.get("pictures", [])],
            "link": data.get("permalink"),
            "disponivel": (data.get("available_quantity") or 0) > 0,
            "quantidade": data.get("available_quantity"),
            "frete_gratis": data.get("shipping", {}).get("free_shipping", False),
            "condicao": data.get("condition"),
            "vendedor_id": data.get("seller_id"),
            "categoria_id": data.get("category_id"),
        }

    except requests.exceptions.RequestException as e:
        return {"erro": str(e), "id": item_id}


# =====================================================
# ENTRADA ÚNICA (URL/ID)
# =====================================================

def buscar_por_url(url_or_id: str) -> Dict[str, Any]:
    tipo, ml_id = extrair_alvo(url_or_id)
    if not ml_id:
        return {"erro": "Não foi possível extrair um ID MLB da entrada", "entrada": url_or_id}

    token = get_access_token()
    if not token:
        return {"erro": "Sem token de acesso. Execute ml_oauth.py primeiro."}

    # Catálogo (/p/MLB...)
    if tipo == "product":
        item_id, dbg = resolver_item_id_de_catalogo(ml_id, token)
        if not item_id:
            # salva um debug mínimo pra você inspecionar sem poluir o terminal
            try:
                with open(f"debug_product_{ml_id}.json", "w", encoding="utf-8") as f:
                    f.write(json.dumps({"product_id": ml_id, "debug": dbg}, ensure_ascii=False, indent=2))
            except Exception:
                pass
            return {
                "erro": "Produto de catálogo sem buy_box_winner (não deu pra achar item_id)",
                "product_id": ml_id,
                "debug": dbg,
            }
        return buscar_produto(item_id)

    # Item (URL de anúncio)
    if tipo == "item":
        return buscar_produto(ml_id)

    # unknown: decide tentando /products primeiro. Se existir, é catálogo.
    pj = _get_product(ml_id, token)
    if pj is not None:
        item_id, dbg = resolver_item_id_de_catalogo(ml_id, token)
        if not item_id:
            return {
                "erro": "Esse MLB parece ser product_id, mas não achei buy_box_winner (sem item_id)",
                "product_id": ml_id,
                "debug": dbg,
            }
        return buscar_produto(item_id)

    # Senão, trata como item_id mesmo
    return buscar_produto(ml_id)


# =====================================================
# TESTE
# =====================================================

def main():
    print("=" * 60)
    print("🛒 API Mercado Livre (OAuth2) - v4")
    print("=" * 60)

    token = get_access_token()
    if token:
        print("✅ Token válido!")
    else:
        print("❌ Sem token. Rode ml_oauth.py.")
        return

    url_teste = "https://www.mercadolivre.com.br/poltrona-reclinavel-damie/p/MLB37776701"
    print(f"\n📍 Testando: {url_teste[:70]}...")
    print("-" * 60)

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
        if "id" in dados:
            print(f"   id: {dados['id']}")
        if "debug" in dados:
            # print só um resumo pro terminal
            dbg = dados["debug"]
            if isinstance(dbg, dict):
                resumo = {k: dbg.get(k) for k in ("status", "children_ids_count", "has_pickers", "visited", "depth", "note") if k in dbg}
                print("   debug:", json.dumps(resumo, ensure_ascii=False))

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
