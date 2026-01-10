"""
Shopee Affiliates API - GraphQL
Em Casa com Cecília

Documentação: https://affiliate.shopee.com.br/open_api
"""

import requests
import hashlib
import time
import json

# =====================================================
# CREDENCIAIS
# =====================================================

APP_ID = "18366030282"
SECRET = "6O3BGLID65IBOKMCHQOXJ2TKJJDYVZ6R"

BASE_URL = "https://open-api.affiliate.shopee.com.br/graphql"

# =====================================================
# AUTENTICAÇÃO
# =====================================================

def gerar_assinatura(app_id, timestamp, payload, secret):
    """
    Gera assinatura SHA256 conforme documentação Shopee.
    Formato: SHA256(app_id + timestamp + payload + secret)
    """
    base_string = f"{app_id}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    return signature


def fazer_requisicao(query, variables=None):
    """
    Faz requisição GraphQL autenticada para a API Shopee.
    """
    timestamp = int(time.time())
    
    # Payload GraphQL
    payload_dict = {"query": query}
    if variables:
        payload_dict["variables"] = variables
    
    payload = json.dumps(payload_dict, separators=(',', ':'))
    
    signature = gerar_assinatura(APP_ID, timestamp, payload, SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'SHA256 Credential={APP_ID}, Timestamp={timestamp}, Signature={signature}'
    }
    
    print(f"   🔗 URL: {BASE_URL}")
    print(f"   📦 Query: {query[:100].replace(chr(10), ' ')}...")
    print(f"   🔑 Timestamp: {timestamp}")
    
    response = requests.post(BASE_URL, headers=headers, data=payload, timeout=30)
    
    print(f"   📡 Status: {response.status_code}")
    print(f"   📄 Resposta: {response.text[:500]}")
    
    try:
        return response.json()
    except:
        return {"error": f"Resposta inválida: {response.text[:200]}"}


# =====================================================
# QUERIES GRAPHQL
# =====================================================

def gerar_link_afiliado(url):
    """
    Gera link de afiliado para uma URL de produto.
    """
    query = '''
    mutation {
        generateShortLink(input: {originUrl: "%s", subIds: ["emcasacomcecilia"]}) {
            shortLink
        }
    }
    ''' % url
    
    result = fazer_requisicao(query)
    
    if result.get('errors'):
        return {"erro": result['errors']}
    
    data = result.get('data', {}).get('generateShortLink', {})
    return {
        "link_afiliado": data.get('shortLink', ''),
        "link_original": url
    }


def buscar_ofertas(limite=10):
    """
    Busca ofertas/promoções disponíveis.
    Endpoint: productOfferV2
    """
    query = '''
    query {
        productOfferV2(listType: 0, sortType: 2, limit: %d) {
            nodes {
                productName
                commissionRate
                sales
                priceMin
                priceMax
                imageUrl
                shopName
                productLink
                offerLink
            }
        }
    }
    ''' % limite
    
    result = fazer_requisicao(query)
    
    if result.get('errors'):
        return {"erro": result['errors']}
    
    nodes = result.get('data', {}).get('productOfferV2', {}).get('nodes', [])
    
    ofertas = []
    for item in nodes:
        ofertas.append({
            "titulo": item.get('productName', ''),
            "preco": item.get('priceMin', 0),
            "preco_max": item.get('priceMax', 0),
            "imagem": item.get('imageUrl', ''),
            "url": item.get('offerLink') or item.get('productLink', ''),
            "loja": item.get('shopName', ''),
            "comissao": item.get('commissionRate', 0),
            "vendas": item.get('sales', 0)
        })
    
    return ofertas


def buscar_lojas_ofertas(limite=10):
    """
    Busca ofertas de lojas.
    Endpoint: shopOfferV2
    """
    query = '''
    query {
        shopOfferV2(sortType: 2, limit: %d) {
            nodes {
                shopName
                shopId
                commissionRate
                imageUrl
                offerLink
                ratingStar
            }
        }
    }
    ''' % limite
    
    result = fazer_requisicao(query)
    
    if result.get('errors'):
        return {"erro": result['errors']}
    
    return result.get('data', {}).get('shopOfferV2', {}).get('nodes', [])


def buscar_produto_por_ids(shop_id, item_id):
    """
    Busca informações de um produto específico.
    """
    query = '''
    query {
        productOfferV2(shopId: %s, itemId: %s, limit: 1) {
            nodes {
                productName
                priceMin
                priceMax
                imageUrl
                shopName
                productLink
                stock
            }
        }
    }
    ''' % (shop_id, item_id)
    
    result = fazer_requisicao(query)
    
    if result.get('errors'):
        return {"erro": result['errors']}
    
    nodes = result.get('data', {}).get('productOfferV2', {}).get('nodes', [])
    
    if not nodes:
        return {"erro": "Produto não encontrado"}
    
    item = nodes[0]
    return {
        "titulo": item.get('productName', ''),
        "preco": item.get('priceMin', 0),
        "imagem": item.get('imageUrl', ''),
        "loja": item.get('shopName', ''),
        "disponivel": item.get('stock', 0) > 0
    }


def extrair_ids_da_url(url):
    """
    Extrai shop_id e item_id de uma URL Shopee.
    Formatos:
    - https://shopee.com.br/produto-i.123456.789012
    - https://shopee.com.br/product/123456/789012
    """
    import re
    
    # Formato: produto-i.SHOPID.ITEMID
    match = re.search(r'-i\.(\d+)\.(\d+)', url)
    if match:
        return match.group(1), match.group(2)
    
    # Formato: /product/SHOPID/ITEMID
    match = re.search(r'/product/(\d+)/(\d+)', url)
    if match:
        return match.group(1), match.group(2)
    
    return None, None


def scrape_shopee(url):
    """
    Função compatível com price_scraper_v2.py
    """
    shop_id, item_id = extrair_ids_da_url(url)
    
    if not shop_id or not item_id:
        return {"erro": "Não foi possível extrair IDs da URL"}
    
    resultado = buscar_produto_por_ids(shop_id, item_id)
    
    if 'erro' not in resultado:
        link_info = gerar_link_afiliado(url)
        if 'erro' not in link_info:
            resultado['link_afiliado'] = link_info.get('link_afiliado')
    
    return resultado


# =====================================================
# TESTE
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛒 Shopee Affiliates API - Teste GraphQL")
    print("=" * 60)
    
    # Teste 1: Buscar ofertas
    print("\n📦 Buscando ofertas (productOfferV2)...")
    ofertas = buscar_ofertas(limite=3)
    
    if isinstance(ofertas, list) and len(ofertas) > 0:
        print(f"\n   ✅ {len(ofertas)} ofertas encontradas:")
        for i, oferta in enumerate(ofertas, 1):
            print(f"   {i}. {oferta['titulo'][:50]}...")
            print(f"      💰 R$ {oferta['preco']} | 🏪 {oferta['loja']}")
    elif isinstance(ofertas, dict) and 'erro' in ofertas:
        print(f"\n   ❌ Erro: {ofertas['erro']}")
    else:
        print("\n   ⚠️ Nenhuma oferta encontrada")
    
    # Teste 2: Gerar link afiliado
    print("\n" + "-" * 60)
    print("\n🔗 Testando geração de link afiliado...")
    url_teste = "https://shopee.com.br/product/123456/789012"
    link = gerar_link_afiliado(url_teste)
    
    if 'erro' not in link:
        print(f"\n   ✅ Link gerado: {link.get('link_afiliado', 'N/A')}")
    else:
        print(f"\n   ❌ Erro: {link['erro']}")
    
    print("\n" + "=" * 60)
