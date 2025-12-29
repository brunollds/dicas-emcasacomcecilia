"""
API do Mercado Livre com OAuth2
Em Casa com Cecília

Requer: ml_tokens.json (gerado pelo ml_oauth.py)
"""

import requests
import json
import re
import os

# Importar funções de autenticação
from ml_oauth import get_access_token, carregar_tokens, API_BASE

# =====================================================
# FUNÇÕES DE BUSCA
# =====================================================

def extrair_id_produto(url):
    """Extrai MLB123456 de uma URL do ML"""
    if not url:
        return None
    
    # Se já é um ID
    clean = url.strip().upper().replace('-', '')
    if re.match(r'^MLB\d+$', clean):
        return clean
    
    # /p/MLB123456
    match = re.search(r'/p/(MLB\d+)', url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    # MLB-123456 na URL
    match = re.search(r'(MLB)-?(\d+)', url, re.IGNORECASE)
    if match:
        return f"MLB{match.group(2)}"
    
    # Short link - resolver
    if '/sec/' in url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            return extrair_id_produto(r.url)
        except:
            pass
    
    return None


def buscar_produto(item_id):
    """
    Busca dados de um produto via API autenticada.
    
    Retorna dict com: titulo, preco, imagem, link, frete_gratis, etc.
    """
    
    token = get_access_token()
    if not token:
        return {"erro": "Sem token de acesso. Execute ml_oauth.py primeiro."}
    
    headers = {'Authorization': f'Bearer {token}'}
    url = f"{API_BASE}/items/{item_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return {"erro": "Produto não encontrado", "id": item_id}
        
        if response.status_code == 401:
            return {"erro": "Token expirado. Execute ml_oauth.py novamente.", "id": item_id}
        
        response.raise_for_status()
        data = response.json()
        
        # Extrair imagem
        imagem = None
        if data.get('pictures'):
            imagem = data['pictures'][0].get('secure_url')
            if imagem:
                # Alta resolução
                imagem = imagem.replace('-O.jpg', '-F.jpg').replace('-I.jpg', '-F.jpg')
        if not imagem:
            imagem = data.get('thumbnail', '').replace('http:', 'https:')
        
        return {
            "id": data.get('id'),
            "titulo": data.get('title'),
            "preco": data.get('price'),
            "preco_original": data.get('original_price'),
            "imagem": imagem,
            "imagens": [p.get('secure_url') for p in data.get('pictures', [])],
            "link": data.get('permalink'),
            "disponivel": data.get('available_quantity', 0) > 0,
            "quantidade": data.get('available_quantity'),
            "frete_gratis": data.get('shipping', {}).get('free_shipping', False),
            "condicao": data.get('condition'),
            "vendedor_id": data.get('seller_id'),
            "categoria_id": data.get('category_id'),
        }
        
    except requests.exceptions.RequestException as e:
        return {"erro": str(e), "id": item_id}


def buscar_por_url(url):
    """
    Busca produto a partir da URL completa.
    """
    item_id = extrair_id_produto(url)
    
    if not item_id:
        return {"erro": "Não foi possível extrair ID da URL", "url": url}
    
    return buscar_produto(item_id)


def buscar_multiplos(item_ids):
    """
    Busca múltiplos produtos de uma vez (max 20 por requisição).
    """
    
    token = get_access_token()
    if not token:
        return {"erro": "Sem token"}
    
    headers = {'Authorization': f'Bearer {token}'}
    resultados = []
    
    for i in range(0, len(item_ids), 20):
        batch = item_ids[i:i+20]
        ids_str = ",".join(batch)
        
        url = f"{API_BASE}/items?ids={ids_str}"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            for item in response.json():
                if item.get('code') == 200:
                    body = item['body']
                    imagem = body.get('pictures', [{}])[0].get('secure_url') if body.get('pictures') else body.get('thumbnail')
                    
                    resultados.append({
                        "id": body.get('id'),
                        "titulo": body.get('title'),
                        "preco": body.get('price'),
                        "imagem": imagem,
                        "link": body.get('permalink'),
                    })
                else:
                    resultados.append({"id": batch[0], "erro": "Não encontrado"})
        except Exception as e:
            print(f"Erro no batch: {e}")
    
    return resultados


# =====================================================
# ATUALIZAR JSON
# =====================================================

def atualizar_products_json(caminho):
    """
    Atualiza preços e imagens dos produtos ML no products.json
    """
    
    with open(caminho, 'r', encoding='utf-8') as f:
        produtos = json.load(f)
    
    atualizados = 0
    erros = 0
    
    for produto in produtos:
        precos = produto.get('prices', {})
        
        if 'Mercado Livre' in precos:
            link = precos['Mercado Livre'].get('link', '')
            
            if link:
                print(f"\n📦 {produto.get('name', '?')[:40]}...")
                
                dados = buscar_por_url(link)
                
                if 'erro' not in dados and dados.get('preco'):
                    # Atualizar preço
                    precos['Mercado Livre']['price'] = dados['preco']
                    
                    # Atualizar imagem se não tiver
                    if dados.get('imagem') and not produto.get('image'):
                        produto['image'] = dados['imagem']
                    
                    atualizados += 1
                    print(f"   ✅ R$ {dados['preco']}")
                else:
                    erros += 1
                    print(f"   ❌ {dados.get('erro', '?')}")
    
    # Salvar
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"✅ {atualizados} atualizados | ❌ {erros} erros")
    
    return {"atualizados": atualizados, "erros": erros}


# =====================================================
# TESTE
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛒 API Mercado Livre (OAuth2)")
    print("=" * 60)
    
    # Verificar token
    token = get_access_token()
    if not token:
        print("\n❌ Execute primeiro: python ml_oauth.py")
        exit(1)
    
    print("✅ Token válido!\n")
    
    # Teste
    url_teste = "https://www.mercadolivre.com.br/poltrona-reclinavel-manual-massagem-aquecimento-damie-cinema/p/MLB37776701"
    
    print(f"📍 Testando: {url_teste[:50]}...")
    print("-" * 50)
    
    dados = buscar_por_url(url_teste)
    
    if 'erro' not in dados:
        print(f"✅ {dados['titulo'][:50]}...")
        print(f"   💰 R$ {dados['preco']}")
        print(f"   🖼️ {dados['imagem'][:60]}..." if dados.get('imagem') else "   🖼️ Sem imagem")
        print(f"   🚚 Frete grátis: {'Sim' if dados.get('frete_gratis') else 'Não'}")
    else:
        print(f"❌ {dados['erro']}")
    
    print("\n" + "=" * 60)
