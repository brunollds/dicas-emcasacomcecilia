"""
Integração com API do Mercado Livre
Em Casa com Cecília - Dicas

Funções:
- Extrair dados de produtos (imagem, preço, título)
- Atualizar products.json e promocoes.json
"""

import requests
import json
import re
import os
from datetime import datetime

# =====================================================
# CREDENCIAIS
# =====================================================

ML_CLIENT_ID = "5878524513877787"
ML_CLIENT_SECRET = "j9a3u2Q85o5muoSj3Jvx1jpuXJsMldoI"

# URLs da API
ML_API_BASE = "https://api.mercadolibre.com"

# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def extrair_id_produto(url):
    """
    Extrai o ID do produto de uma URL do Mercado Livre.
    
    Exemplos de URLs suportadas:
    - https://www.mercadolivre.com.br/produto-xyz/p/MLB12345678
    - https://produto.mercadolivre.com.br/MLB-12345678-titulo
    - https://mercadolivre.com/sec/2zB1urD (short link)
    - MLB12345678 ou MLB-1234567890
    """
    
    # Se já é um ID direto
    if re.match(r'^MLB-?\d+$', url.replace('-', '')):
        return url.replace('-', '')
    
    # Padrão 1: /p/MLB12345678
    match = re.search(r'/p/(MLB\d+)', url)
    if match:
        return match.group(1)
    
    # Padrão 2: MLB-12345678-titulo ou MLB12345678
    match = re.search(r'(MLB)-?(\d+)', url)
    if match:
        return f"MLB{match.group(2)}"
    
    # Short link - precisa resolver o redirect
    if 'mercadolivre.com/sec/' in url or 'mercadolibre.com/sec/' in url:
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            return extrair_id_produto(response.url)
        except:
            pass
    
    return None


def buscar_produto(item_id):
    """
    Busca dados de um produto pelo ID.
    Retorna dict com: id, titulo, preco, imagem, link, disponivel
    """
    
    url = f"{ML_API_BASE}/items/{item_id}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            return {"erro": "Produto não encontrado", "id": item_id}
        
        response.raise_for_status()
        data = response.json()
        
        # Extrair melhor imagem disponível
        imagem = None
        if data.get('pictures') and len(data['pictures']) > 0:
            # Pegar a maior resolução disponível
            pic = data['pictures'][0]
            # Tentar URL de alta resolução
            imagem = pic.get('secure_url') or pic.get('url')
            # Substituir por versão de alta qualidade se possível
            if imagem:
                imagem = imagem.replace('-O.jpg', '-F.jpg').replace('-I.jpg', '-F.jpg')
        
        if not imagem:
            imagem = data.get('thumbnail', '').replace('http:', 'https:')
        
        return {
            "id": data.get('id'),
            "titulo": data.get('title'),
            "preco": data.get('price'),
            "preco_original": data.get('original_price'),
            "moeda": data.get('currency_id'),
            "imagem": imagem,
            "imagens": [p.get('secure_url') for p in data.get('pictures', [])],
            "link": data.get('permalink'),
            "disponivel": data.get('available_quantity', 0) > 0,
            "quantidade": data.get('available_quantity'),
            "condicao": data.get('condition'),  # new, used
            "frete_gratis": data.get('shipping', {}).get('free_shipping', False),
            "vendedor": data.get('seller_id'),
            "categoria": data.get('category_id'),
        }
        
    except requests.exceptions.RequestException as e:
        return {"erro": str(e), "id": item_id}


def buscar_multiplos_produtos(item_ids):
    """
    Busca dados de múltiplos produtos de uma vez.
    Máximo 20 por requisição.
    """
    
    resultados = []
    
    # API aceita até 20 IDs por vez
    for i in range(0, len(item_ids), 20):
        batch = item_ids[i:i+20]
        ids_str = ",".join(batch)
        
        url = f"{ML_API_BASE}/items?ids={ids_str}"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for item in data:
                if item.get('code') == 200:
                    body = item.get('body', {})
                    
                    imagem = None
                    if body.get('pictures'):
                        imagem = body['pictures'][0].get('secure_url')
                    if not imagem:
                        imagem = body.get('thumbnail', '').replace('http:', 'https:')
                    
                    resultados.append({
                        "id": body.get('id'),
                        "titulo": body.get('title'),
                        "preco": body.get('price'),
                        "imagem": imagem,
                        "link": body.get('permalink'),
                        "disponivel": body.get('available_quantity', 0) > 0,
                    })
                else:
                    resultados.append({
                        "id": item.get('body', {}).get('id'),
                        "erro": "Não encontrado"
                    })
                    
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar batch: {e}")
    
    return resultados


def atualizar_imagem_promo(url_produto):
    """
    Dado um link do ML, retorna a imagem e preço atual.
    Útil para preencher promoções.
    """
    
    item_id = extrair_id_produto(url_produto)
    if not item_id:
        return {"erro": "Não foi possível extrair ID do produto"}
    
    dados = buscar_produto(item_id)
    
    if 'erro' in dados:
        return dados
    
    return {
        "imagem": dados['imagem'],
        "preco": dados['preco'],
        "titulo": dados['titulo'],
        "disponivel": dados['disponivel'],
        "frete_gratis": dados['frete_gratis']
    }


# =====================================================
# FUNÇÕES PARA ATUALIZAR ARQUIVOS JSON
# =====================================================

def atualizar_products_json(caminho_json):
    """
    Lê o products.json e atualiza preços/imagens dos produtos do ML.
    """
    
    with open(caminho_json, 'r', encoding='utf-8') as f:
        produtos = json.load(f)
    
    atualizados = 0
    erros = 0
    
    for produto in produtos:
        precos = produto.get('prices', {})
        
        if 'Mercado Livre' in precos:
            link_ml = precos['Mercado Livre'].get('link', '')
            
            if link_ml:
                print(f"Atualizando: {produto.get('name', 'Sem nome')[:50]}...")
                
                dados = atualizar_imagem_promo(link_ml)
                
                if 'erro' not in dados:
                    # Atualizar preço
                    precos['Mercado Livre']['price'] = dados['preco']
                    
                    # Atualizar imagem se não tiver ou for placeholder
                    if not produto.get('image') or 'placeholder' in produto.get('image', ''):
                        produto['image'] = dados['imagem']
                    
                    atualizados += 1
                    print(f"  ✓ R$ {dados['preco']}")
                else:
                    erros += 1
                    print(f"  ✗ {dados['erro']}")
    
    # Salvar arquivo atualizado
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Concluído: {atualizados} atualizados, {erros} erros")
    return {"atualizados": atualizados, "erros": erros}


def processar_url_ml(url):
    """
    Função simples: recebe URL, retorna dados formatados.
    """
    item_id = extrair_id_produto(url)
    
    if not item_id:
        print(f"❌ Não consegui extrair ID de: {url}")
        return None
    
    print(f"📦 Buscando {item_id}...")
    dados = buscar_produto(item_id)
    
    if 'erro' in dados:
        print(f"❌ Erro: {dados['erro']}")
        return None
    
    print(f"✅ {dados['titulo'][:50]}...")
    print(f"   💰 R$ {dados['preco']}")
    print(f"   🖼️ {dados['imagem'][:60]}...")
    print(f"   🚚 Frete grátis: {'Sim' if dados['frete_gratis'] else 'Não'}")
    
    return dados


# =====================================================
# TESTE
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛒 API Mercado Livre - Em Casa com Cecília")
    print("=" * 60)
    
    # Teste com um produto Damie
    url_teste = "https://www.mercadolivre.com.br/poltrona-reclinavel-manual-massagem-aquecimento-damie-cinema/p/MLB37776701"
    
    print(f"\n📍 Testando URL: {url_teste[:60]}...")
    print("-" * 60)
    
    resultado = processar_url_ml(url_teste)
    
    if resultado:
        print("\n" + "=" * 60)
        print("✅ API funcionando corretamente!")
        print("=" * 60)
    else:
        print("\n❌ Falha no teste")
