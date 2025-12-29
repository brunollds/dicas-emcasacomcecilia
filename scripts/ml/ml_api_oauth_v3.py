"""
API do Mercado Livre com OAuth2 (v3)
- Suporta URLs de catálogo (/p/MLBxxxx) resolvendo product_id -> item_id via /products/{product_id}
- Busca preço via /items/{item_id}/sale_price (amount / regular_amount)
"""

import requests
import json
import re

from ml_oauth import get_access_token, API_BASE

# =====================================================
# HELPERS
# =====================================================

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        # Alguns ambientes/proxies ficam menos chatos com UA
        "User-Agent": "Mozilla/5.0 (compatible; dicas.emcasacomcecilia.com; +https://dicas.emcasacomcecilia.com)",
    }

def extrair_alvo(url_or_id: str):
    """
    Retorna ("product"|"item", "MLB...") ou (None, None)
    """
    if not url_or_id:
        return (None, None)

    s = url_or_id.strip()

    # Caso o usuário passe só o ID (MLB123...)
    clean = s.upper().replace("-", "")
    if re.match(r"^MLB\d+$", clean):
        # Pode ser item_id OU product_id. A gente decide depois tentando resolver.
        return ("unknown", clean)

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

def resolver_item_id(product_or_item_id: str, token: str):
    """
    Recebe um ID MLB... e tenta resolver para item_id válido.
    Estratégia:
    1) tenta /items/{id}; se 200 -> já é item_id
    2) se 404 -> tenta /products/{id} e pega buy_box_winner.item_id
    """
    h = _headers(token)

    # 1) tentar como item_id
    r = requests.get(f"{API_BASE}/items/{product_or_item_id}", headers=h, timeout=15)
    if r.status_code == 200:
        return ("item", product_or_item_id)

    if r.status_code not in (404, 403, 401):
        # outros erros, deixa o chamador tratar
        return ("item", product_or_item_id)

    # 2) tentar como product_id
    rp = requests.get(f"{API_BASE}/products/{product_or_item_id}", headers=h, timeout=15)
    if rp.status_code != 200:
        return (None, None)

    data = rp.json()
    winner = data.get("buy_box_winner") or {}

    # Formatos possíveis: winner.item_id (mais comum), ou winner.item.id
    item_id = winner.get("item_id")
    if not item_id and isinstance(winner.get("item"), dict):
        item_id = winner["item"].get("id")

    if item_id:
        return ("item", item_id)

    return (None, None)

def buscar_sale_price(item_id: str, token: str):
    """
    Retorna dict com amount/regular_amount/currency_id, ou None se não conseguir.
    """
    h = _headers(token)
    r = requests.get(f"{API_BASE}/items/{item_id}/sale_price", headers=h, timeout=15)

    if r.status_code != 200:
        return None

    try:
        return r.json()
    except Exception:
        return None

# =====================================================
# API PRINCIPAL
# =====================================================

def buscar_produto(item_id: str):
    """
    Busca dados do item + preço via sale_price.
    """
    token = get_access_token()
    if not token:
        return {"erro": "Sem token de acesso. Execute ml_oauth.py primeiro."}

    h = _headers(token)

    try:
        r = requests.get(f"{API_BASE}/items/{item_id}", headers=h, timeout=15)

        if r.status_code == 404:
            return {"erro": "Item não encontrado (ID inválido para /items)", "id": item_id}

        if r.status_code == 401:
            return {"erro": "Token expirado (401). Rode ml_oauth.py de novo.", "id": item_id}

        if r.status_code == 403:
            return {"erro": "Acesso bloqueado (403) ao /items. Pode ser política/scope.", "id": item_id}

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

        # preço via sale_price (preferido)
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

def buscar_por_url(url_or_id: str):
    """
    Aceita URL do ML (incluindo /p/MLB...) OU um ID MLB...
    """
    tipo, ml_id = extrair_alvo(url_or_id)
    if not ml_id:
        return {"erro": "Não foi possível extrair um ID MLB da entrada", "entrada": url_or_id}

    token = get_access_token()
    if not token:
        return {"erro": "Sem token de acesso. Execute ml_oauth.py primeiro."}

    # Se veio como product, resolve direto
    if tipo == "product":
        _, item_id = resolver_item_id(ml_id, token)
        if not item_id:
            return {"erro": "Produto de catálogo sem buy_box_winner (não deu pra achar item_id)", "product_id": ml_id}
        return buscar_produto(item_id)

    # Se veio como item, tenta direto
    if tipo == "item":
        return buscar_produto(ml_id)

    # unknown: tenta resolver automaticamente
    _, item_id = resolver_item_id(ml_id, token)
    if not item_id:
        return {"erro": "Não consegui resolver esse MLB... como item nem como product", "id": ml_id}
    return buscar_produto(item_id)

# =====================================================
# TESTE
# =====================================================

def main():
    print("=" * 60)
    print("🛒 API Mercado Livre (OAuth2) - v3")
    print("=" * 60)

    token = get_access_token()
    if token:
        print("✅ Token válido!")
    else:
        print("❌ Sem token. Rode ml_oauth.py.")
        return

    # Teste padrão (o seu caso /p/MLB...)
    url_teste = "https://www.mercadolivre.com.br/poltrona-reclinavel-damie/p/MLB37776701"
    print(f"\n📍 Testando: {url_teste[:60]}...")
    print("-" * 50)

    dados = buscar_por_url(url_teste)

    if "erro" not in dados:
        print(f"✅ {dados.get('titulo')}")
        print(f"   💰 Preço: {dados.get('preco')}  |  Riscado: {dados.get('preco_original')}")
        print(f"   🔗 {dados.get('link')}")
        print(f"   🖼️ {dados.get('imagem')}")
    else:
        print(f"❌ {dados['erro']}")
        # ajuda de debug
        for k in ("id", "product_id", "entrada"):
            if k in dados:
                print(f"   {k}: {dados[k]}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
