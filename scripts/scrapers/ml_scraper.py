"""
Integração com Mercado Livre via Scraping
Em Casa com Cecília - Dicas

Como a API exige OAuth2, usamos scraping direto do site.
Funciona para extrair: título, preço, imagem, frete grátis
"""

import requests
import json
import re
from urllib.parse import unquote

# Headers para simular navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

def extrair_id_produto(url):
    """
    Extrai o ID do produto (MLB123456) de uma URL do ML.
    """
    if not url:
        return None
    
    # Se já é um ID direto
    clean_id = url.strip().upper().replace('-', '')
    if re.match(r'^MLB\d+$', clean_id):
        return clean_id
    
    # Padrão: /p/MLB12345678
    match = re.search(r'/p/(MLB\d+)', url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    # Padrão: MLB-12345678 na URL
    match = re.search(r'(MLB)-?(\d+)', url, re.IGNORECASE)
    if match:
        return f"MLB{match.group(2)}"
    
    # Short link - resolver redirect
    if '/sec/' in url:
        try:
            response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
            return extrair_id_produto(response.url)
        except:
            pass
    
    return None


def buscar_produto_ml(url_ou_id):
    """
    Busca dados de um produto do Mercado Livre.
    Aceita URL completa ou ID (MLB123456).
    
    Retorna:
    {
        "id": "MLB123456",
        "titulo": "Nome do produto",
        "preco": 199.90,
        "preco_original": 299.90,
        "imagem": "https://...",
        "link": "https://...",
        "frete_gratis": True/False,
        "disponivel": True/False
    }
    """
    
    # Extrair ID se for URL
    item_id = extrair_id_produto(url_ou_id) if 'http' in url_ou_id else url_ou_id.upper().replace('-', '')
    
    if not item_id:
        return {"erro": "Não foi possível extrair ID do produto", "url": url_ou_id}
    
    # Tentar buscar pela página do produto
    urls_tentar = [
        f"https://www.mercadolivre.com.br/p/{item_id}",
        f"https://produto.mercadolivre.com.br/{item_id}",
    ]
    
    for url in urls_tentar:
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                dados = extrair_dados_html(html, item_id, response.url)
                if dados and dados.get('titulo'):
                    return dados
                    
        except Exception as e:
            continue
    
    return {"erro": "Produto não encontrado", "id": item_id}


def extrair_dados_html(html, item_id, url_final):
    """
    Extrai dados do produto do HTML da página.
    """
    
    resultado = {
        "id": item_id,
        "link": url_final,
    }
    
    # ===== TÍTULO =====
    # Tentar meta og:title primeiro
    match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
    if match:
        resultado['titulo'] = match.group(1).strip()
    else:
        # Tentar tag title
        match = re.search(r'<title>([^<]+)</title>', html)
        if match:
            titulo = match.group(1).replace(' | MercadoLivre', '').replace(' - MercadoLivre', '').strip()
            resultado['titulo'] = titulo
    
    # ===== PREÇO =====
    # Procurar no JSON embutido na página
    match = re.search(r'"price"\s*:\s*(\d+\.?\d*)', html)
    if match:
        resultado['preco'] = float(match.group(1))
    else:
        # Tentar formato visual
        match = re.search(r'R\$\s*([\d.,]+)', html)
        if match:
            preco_str = match.group(1).replace('.', '').replace(',', '.')
            try:
                resultado['preco'] = float(preco_str)
            except:
                pass
    
    # Preço original (riscado)
    match = re.search(r'"original_price"\s*:\s*(\d+\.?\d*)', html)
    if match:
        resultado['preco_original'] = float(match.group(1))
    
    # ===== IMAGEM =====
    # Procurar imagem de alta qualidade
    patterns = [
        r'"(https://http2\.mlstatic\.com/D_NQ_NP_[^"]+\.(?:jpg|webp|png))"',
        r'"(https://http2\.mlstatic\.com/D_[^"]+\.(?:jpg|webp|png))"',
        r'<meta\s+property="og:image"\s+content="([^"]+)"',
        r'<img[^>]+data-src="(https://[^"]*mlstatic[^"]+)"',
        r'<img[^>]+src="(https://[^"]*mlstatic[^"]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            imagem = match.group(1)
            # Tentar pegar versão de alta qualidade
            imagem = re.sub(r'-[A-Z]\.', '-F.', imagem)
            resultado['imagem'] = imagem
            break
    
    # Lista de imagens
    imagens = re.findall(r'"(https://http2\.mlstatic\.com/D_[^"]+\.(?:jpg|webp|png))"', html)
    if imagens:
        # Remover duplicatas e pegar únicas
        resultado['imagens'] = list(dict.fromkeys(imagens))[:5]
    
    # ===== FRETE GRÁTIS =====
    resultado['frete_gratis'] = bool(
        re.search(r'Frete\s*gr[áa]tis', html, re.IGNORECASE) or
        re.search(r'"free_shipping"\s*:\s*true', html, re.IGNORECASE)
    )
    
    # ===== DISPONIBILIDADE =====
    resultado['disponivel'] = not bool(
        re.search(r'Este produto não está mais disponível', html, re.IGNORECASE) or
        re.search(r'Produto indisponível', html, re.IGNORECASE)
    )
    
    # ===== VENDEDOR =====
    match = re.search(r'"seller_id"\s*:\s*(\d+)', html)
    if match:
        resultado['vendedor_id'] = match.group(1)
    
    match = re.search(r'"seller"\s*:\s*\{[^}]*"nickname"\s*:\s*"([^"]+)"', html)
    if match:
        resultado['vendedor'] = match.group(1)
    
    return resultado


def processar_url_ml(url):
    """
    Função principal: recebe URL, retorna dados formatados.
    """
    print(f"📦 Buscando produto...")
    dados = buscar_produto_ml(url)
    
    if 'erro' in dados:
        print(f"❌ Erro: {dados['erro']}")
        return None
    
    print(f"✅ {dados.get('titulo', 'Sem título')[:50]}...")
    print(f"   💰 R$ {dados.get('preco', 'N/A')}")
    if dados.get('imagem'):
        print(f"   🖼️ {dados['imagem'][:60]}...")
    print(f"   🚚 Frete grátis: {'Sim' if dados.get('frete_gratis') else 'Não'}")
    
    return dados


def atualizar_products_json(caminho_json):
    """
    Atualiza preços e imagens dos produtos ML no products.json
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
                print(f"\n📦 {produto.get('name', 'Sem nome')[:40]}...")
                
                dados = buscar_produto_ml(link_ml)
                
                if 'erro' not in dados and dados.get('preco'):
                    # Atualizar preço
                    precos['Mercado Livre']['price'] = dados['preco']
                    
                    # Atualizar imagem se não tiver
                    if dados.get('imagem') and (not produto.get('image') or 'placeholder' in produto.get('image', '')):
                        produto['image'] = dados['imagem']
                    
                    atualizados += 1
                    print(f"   ✅ R$ {dados['preco']}")
                else:
                    erros += 1
                    print(f"   ❌ {dados.get('erro', 'Erro desconhecido')}")
    
    # Salvar
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"✅ Concluído: {atualizados} atualizados, {erros} erros")
    return {"atualizados": atualizados, "erros": erros}


# =====================================================
# TESTE
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛒 Mercado Livre Scraper - Em Casa com Cecília")
    print("=" * 60)
    
    # URLs de teste
    urls_teste = [
        "https://www.mercadolivre.com.br/poltrona-reclinavel-manual-massagem-aquecimento-damie-cinema/p/MLB37776701",
        "MLB37776701",
    ]
    
    for url in urls_teste:
        print(f"\n📍 Testando: {url[:50]}...")
        print("-" * 50)
        resultado = processar_url_ml(url)
        
        if resultado:
            print(f"\n   📋 Dados completos:")
            for k, v in resultado.items():
                if k != 'imagens':
                    valor = str(v)[:60] + '...' if len(str(v)) > 60 else v
                    print(f"      {k}: {valor}")
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!")
    print("=" * 60)
