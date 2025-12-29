"""
API do Mercado Livre - Versão Busca
Em Casa com Cecília

Usa o endpoint de busca que é mais aberto
"""

import requests
import json
import re
import os

# Carregar token se existir
TOKENS_FILE = "ml_tokens.json"

def get_token():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('access_token')
    return None

def extrair_id_produto(url):
    """Extrai MLB123456 de uma URL do ML"""
    if not url:
        return None
    
    clean = url.strip().upper().replace('-', '')
    if re.match(r'^MLB\d+$', clean):
        return clean
    
    match = re.search(r'/p/(MLB\d+)', url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    match = re.search(r'(MLB)-?(\d+)', url, re.IGNORECASE)
    if match:
        return f"MLB{match.group(2)}"
    
    return None


def buscar_por_id(item_id):
    """
    Busca produto usando endpoint de busca por ID
    """
    
    # Endpoint que funciona melhor
    url = f"https://api.mercadolibre.com/items/{item_id}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    token = get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # Tentar com atributos específicos (às vezes funciona melhor)
    params = {
        'attributes': 'id,title,price,original_price,thumbnail,pictures,permalink,shipping,available_quantity'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            imagem = None
            if data.get('pictures'):
                imagem = data['pictures'][0].get('secure_url', '')
            if not imagem:
                imagem = data.get('thumbnail', '').replace('http:', 'https:')
            
            return {
                "id": data.get('id'),
                "titulo": data.get('title'),
                "preco": data.get('price'),
                "imagem": imagem,
                "link": data.get('permalink'),
                "frete_gratis": data.get('shipping', {}).get('free_shipping', False),
                "disponivel": data.get('available_quantity', 0) > 0,
            }
        
        # Se falhou, tentar via busca
        return buscar_via_search(item_id)
        
    except Exception as e:
        return {"erro": str(e), "id": item_id}


def buscar_via_search(item_id):
    """
    Busca alternativa via endpoint de search
    """
    
    url = "https://api.mercadolibre.com/sites/MLB/search"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # Buscar pelo ID no campo de busca
    params = {'q': item_id}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            # Procurar o item específico
            for item in results:
                if item.get('id') == item_id:
                    return {
                        "id": item.get('id'),
                        "titulo": item.get('title'),
                        "preco": item.get('price'),
                        "imagem": item.get('thumbnail', '').replace('http:', 'https:'),
                        "link": item.get('permalink'),
                        "frete_gratis": item.get('shipping', {}).get('free_shipping', False),
                        "disponivel": item.get('available_quantity', 0) > 0,
                    }
            
            # Se não encontrou exato, retorna o primeiro
            if results:
                item = results[0]
                return {
                    "id": item.get('id'),
                    "titulo": item.get('title'),
                    "preco": item.get('price'),
                    "imagem": item.get('thumbnail', '').replace('http:', 'https:'),
                    "link": item.get('permalink'),
                    "aviso": "Produto similar (ID exato não encontrado)"
                }
        
        return {"erro": f"Busca retornou {response.status_code}", "id": item_id}
        
    except Exception as e:
        return {"erro": str(e), "id": item_id}


def buscar_por_texto(texto, limite=5):
    """
    Busca produtos por texto
    """
    
    url = "https://api.mercadolibre.com/sites/MLB/search"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    params = {
        'q': texto,
        'limit': limite
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for item in data.get('results', []):
                results.append({
                    "id": item.get('id'),
                    "titulo": item.get('title'),
                    "preco": item.get('price'),
                    "imagem": item.get('thumbnail', '').replace('http:', 'https:'),
                    "link": item.get('permalink'),
                    "frete_gratis": item.get('shipping', {}).get('free_shipping', False),
                })
            
            return results
        
        return {"erro": f"Status {response.status_code}"}
        
    except Exception as e:
        return {"erro": str(e)}


def buscar_vendedor(seller_id, limite=10):
    """
    Busca produtos de um vendedor específico
    """
    
    url = "https://api.mercadolibre.com/sites/MLB/search"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    params = {
        'seller_id': seller_id,
        'limit': limite
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for item in data.get('results', []):
                results.append({
                    "id": item.get('id'),
                    "titulo": item.get('title'),
                    "preco": item.get('price'),
                    "imagem": item.get('thumbnail', '').replace('http:', 'https:'),
                    "link": item.get('permalink'),
                })
            
            return results
        
        return {"erro": f"Status {response.status_code}"}
        
    except Exception as e:
        return {"erro": str(e)}


# =====================================================
# TESTE
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛒 API Mercado Livre - Busca")
    print("=" * 60)
    
    # Teste 1: Buscar por texto
    print("\n📍 Teste 1: Buscar 'cafeteira nespresso'")
    print("-" * 50)
    
    resultados = buscar_por_texto("cafeteira nespresso essenza mini", limite=3)
    
    if isinstance(resultados, list):
        for r in resultados:
            print(f"✅ {r['titulo'][:50]}...")
            print(f"   💰 R$ {r['preco']}")
            print(f"   🖼️ {r['imagem'][:50]}...")
            print()
    else:
        print(f"❌ {resultados}")
    
    # Teste 2: Buscar Damie
    print("\n📍 Teste 2: Buscar 'poltrona damie'")
    print("-" * 50)
    
    resultados = buscar_por_texto("poltrona damie reclinavel", limite=3)
    
    if isinstance(resultados, list):
        for r in resultados:
            print(f"✅ {r['titulo'][:50]}...")
            print(f"   💰 R$ {r['preco']}")
            print(f"   🔗 {r['id']}")
            print()
    else:
        print(f"❌ {resultados}")
    
    print("=" * 60)
