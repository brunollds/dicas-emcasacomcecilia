"""
Scraper de Preços - Mercado Livre
Em Casa com Cecília

Extrai preço e imagem direto do HTML da página do produto.
Funciona com URLs de catálogo (/p/MLB...) e anúncios normais.
"""

import requests
import json
import re
import time
import random
from pathlib import Path
from datetime import datetime

# =====================================================
# CONFIGURAÇÃO
# =====================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}

# Delay entre requisições (evitar bloqueio)
# Use valores menores para teste, maiores para produção
MIN_DELAY = 1
MAX_DELAY = 2

# =====================================================
# FUNÇÕES DE EXTRAÇÃO
# =====================================================

def extrair_id_ml(url):
    """Extrai ID do produto da URL"""
    if not url:
        return None
    
    # /p/MLB123456
    match = re.search(r'/p/(MLB\d+)', url, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    # MLB-123456 ou MLB123456
    match = re.search(r'(MLB)-?(\d+)', url, re.IGNORECASE)
    if match:
        return f"MLB{match.group(2)}"
    
    return None


def scrape_produto_ml(url):
    """
    Faz scraping da página do produto e extrai dados.
    
    Retorna:
    {
        "titulo": str,
        "preco": float,
        "preco_original": float ou None,
        "imagem": str,
        "disponivel": bool,
        "frete_gratis": bool,
        "erro": str (se houver)
    }
    """
    
    try:
        # Adiciona delay aleatório
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        
        # Headers mais completos
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Criar sessão para manter cookies
        session = requests.Session()
        
        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 404:
            return {"erro": "Produto não encontrado (404)"}
        
        if response.status_code != 200:
            return {"erro": f"Status {response.status_code}"}
        
        html = response.text
        resultado = {}
        
        # Debug: salvar HTML se não encontrar nada
        with open('debug_ml.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        # ===== TÍTULO =====
        patterns_titulo = [
            r'<h1[^>]*class="ui-pdp-title"[^>]*>([^<]+)</h1>',
            r'"name"\s*:\s*"([^"]+)"',
            r'<meta\s+property="og:title"\s+content="([^"]+)"',
            r'<meta\s+name="twitter:title"\s+content="([^"]+)"',
            r'<title>([^<|]+)',
        ]
        for pattern in patterns_titulo:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                titulo = match.group(1).strip()
                titulo = re.sub(r'\s*\|\s*MercadoLivre.*$', '', titulo)
                titulo = re.sub(r'\s*-\s*MercadoLivre.*$', '', titulo)
                titulo = re.sub(r'\s*\|.*$', '', titulo)
                if len(titulo) > 5:  # Evitar títulos muito curtos
                    resultado['titulo'] = titulo
                    break
        
        # ===== PREÇO =====
        patterns_preco = [
            # JSON-LD e dados estruturados
            r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?',
            r'"amount"\s*:\s*"?(\d+(?:\.\d+)?)"?',
            r'"lowPrice"\s*:\s*"?(\d+(?:\.\d+)?)"?',
            # Meta tags
            r'<meta\s+itemprop="price"\s+content="(\d+(?:\.\d+)?)"',
            r'<meta\s+property="product:price:amount"\s+content="(\d+(?:\.\d+)?)"',
            # Elementos visuais
            r'class="andes-money-amount__fraction"[^>]*>(\d+(?:[\.,]\d+)?)<',
            r'<span[^>]*price[^>]*>R\$\s*([\d.,]+)</span>',
            # Formato brasileiro no HTML
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'R\$\s*(\d+(?:,\d{2})?)',
        ]
        
        for pattern in patterns_preco:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Limpar e converter
                        preco_str = match if isinstance(match, str) else match[0]
                        preco_str = preco_str.replace('.', '').replace(',', '.')
                        preco = float(preco_str)
                        # Validar range razoável
                        if 0.01 < preco < 1000000:
                            resultado['preco'] = preco
                            break
                    except:
                        continue
                if 'preco' in resultado:
                    break
        
        # Preço original (riscado)
        patterns_preco_original = [
            r'"original_price"\s*:\s*"?(\d+(?:\.\d+)?)"?',
            r'"regular_amount"\s*:\s*"?(\d+(?:\.\d+)?)"?',
            r'"highPrice"\s*:\s*"?(\d+(?:\.\d+)?)"?',
            r'<s[^>]*>R\$\s*([\d.,]+)</s>',
            r'class="[^"]*price[^"]*through[^"]*"[^>]*>R\$\s*([\d.,]+)',
        ]
        
        for pattern in patterns_preco_original:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                try:
                    preco_str = match.group(1).replace('.', '').replace(',', '.')
                    preco_original = float(preco_str)
                    if preco_original > resultado.get('preco', 0):
                        resultado['preco_original'] = preco_original
                        break
                except:
                    continue
        
        # ===== IMAGEM =====
        patterns_img = [
            r'"(https://http2\.mlstatic\.com/D_NQ_NP_2X_[^"]+\.(?:jpg|webp|png))"',
            r'"(https://http2\.mlstatic\.com/D_NQ_NP_[^"]+\.(?:jpg|webp|png))"',
            r'"(https://http2\.mlstatic\.com/D_[^"]+\.(?:jpg|webp|png))"',
            r'<meta\s+property="og:image"\s+content="([^"]+)"',
            r'<meta\s+property="og:image:secure_url"\s+content="([^"]+)"',
            r'"image"\s*:\s*"(https://[^"]+mlstatic[^"]+)"',
            r'src="(https://[^"]*mlstatic\.com/[^"]+\.(?:jpg|webp|png))"',
        ]
        for pattern in patterns_img:
            match = re.search(pattern, html)
            if match:
                imagem = match.group(1)
                # Tentar versão de alta qualidade
                imagem = re.sub(r'-[A-Z]\.', '-F.', imagem)
                if 'mlstatic' in imagem:
                    resultado['imagem'] = imagem
                    break
        
        # ===== DISPONIBILIDADE =====
        indisponivel = bool(
            re.search(r'Este produto não está mais disponível', html, re.IGNORECASE) or
            re.search(r'Produto indisponível', html, re.IGNORECASE) or
            re.search(r'Este produto esgotou', html, re.IGNORECASE) or
            re.search(r'no longer available', html, re.IGNORECASE)
        )
        resultado['disponivel'] = not indisponivel
        
        # ===== FRETE GRÁTIS =====
        resultado['frete_gratis'] = bool(
            re.search(r'Frete\s*gr[áa]tis', html, re.IGNORECASE) or
            re.search(r'"free_shipping"\s*:\s*true', html, re.IGNORECASE) or
            re.search(r'Envio\s*gr[áa]tis', html, re.IGNORECASE)
        )
        
        # Validar se conseguiu o mínimo
        if not resultado.get('preco') and not resultado.get('titulo'):
            # Tentar detectar se é uma página de erro ou captcha
            if 'captcha' in html.lower() or 'robot' in html.lower():
                return {"erro": "Página bloqueada (captcha)"}
            return {"erro": "Não consegui extrair dados da página"}
        
        return resultado
        
    except requests.exceptions.Timeout:
        return {"erro": "Timeout na requisição"}
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro de conexão: {str(e)}"}
    except Exception as e:
        return {"erro": f"Erro inesperado: {str(e)}"}


def atualizar_products_json(caminho_json, dry_run=False):
    """
    Atualiza preços e imagens dos produtos ML no products.json
    
    Args:
        caminho_json: Caminho para o arquivo products.json
        dry_run: Se True, não salva alterações (só mostra)
    """
    
    caminho = Path(caminho_json)
    
    if not caminho.exists():
        print(f"❌ Arquivo não encontrado: {caminho}")
        return
    
    with open(caminho, 'r', encoding='utf-8') as f:
        produtos = json.load(f)
    
    print(f"📦 {len(produtos)} produtos encontrados")
    print("=" * 60)
    
    atualizados = 0
    erros = 0
    ignorados = 0
    
    for i, produto in enumerate(produtos):
        nome = produto.get('name', 'Sem nome')[:40]
        precos = produto.get('prices', {})
        
        # Verificar se tem link do ML
        if 'Mercado Livre' not in precos:
            ignorados += 1
            continue
        
        link_ml = precos['Mercado Livre'].get('link', '')
        if not link_ml:
            ignorados += 1
            continue
        
        print(f"\n[{i+1}/{len(produtos)}] {nome}...")
        
        # Fazer scraping
        dados = scrape_produto_ml(link_ml)
        
        if 'erro' in dados:
            print(f"   ❌ {dados['erro']}")
            erros += 1
            continue
        
        # Atualizar dados
        alteracoes = []
        
        if dados.get('preco'):
            preco_antigo = precos['Mercado Livre'].get('price')
            preco_novo = dados['preco']
            
            if preco_antigo != preco_novo:
                alteracoes.append(f"Preço: R${preco_antigo} → R${preco_novo}")
                precos['Mercado Livre']['price'] = preco_novo
        
        if dados.get('imagem') and not produto.get('image'):
            alteracoes.append(f"Imagem adicionada")
            produto['image'] = dados['imagem']
        
        if alteracoes:
            atualizados += 1
            for alt in alteracoes:
                print(f"   ✅ {alt}")
        else:
            print(f"   ⏸️ Sem alterações (R${precos['Mercado Livre'].get('price')})")
    
    print("\n" + "=" * 60)
    print(f"📊 Resumo:")
    print(f"   ✅ Atualizados: {atualizados}")
    print(f"   ❌ Erros: {erros}")
    print(f"   ⏭️ Ignorados (sem ML): {ignorados}")
    
    # Salvar
    if not dry_run and atualizados > 0:
        # Backup
        backup_path = caminho.with_suffix(f'.json.backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(produtos, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Backup salvo: {backup_path.name}")
        
        # Salvar atualizado
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(produtos, f, ensure_ascii=False, indent=2)
        print(f"💾 Arquivo atualizado: {caminho}")
    elif dry_run:
        print("\n⚠️ Modo dry-run: alterações não foram salvas")
    
    return {"atualizados": atualizados, "erros": erros, "ignorados": ignorados}


# =====================================================
# TESTE
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛒 Scraper Mercado Livre - Em Casa com Cecília")
    print("=" * 60)
    
    # Teste com URL real
    url_teste = "https://www.mercadolivre.com.br/cafeteira-nespresso-essenza-mini-d30-automatica-preta-para-capsulas-monodose/p/MLB19112932"
    
    print(f"\n📍 Testando: {url_teste[:60]}...")
    print("-" * 60)
    
    # Modo debug: salvar HTML
    DEBUG_MODE = True
    
    dados = scrape_produto_ml(url_teste)
    
    if 'erro' not in dados:
        print(f"✅ Título: {dados.get('titulo', 'N/A')[:50]}...")
        print(f"💰 Preço: R$ {dados.get('preco', 'N/A')}")
        if dados.get('preco_original'):
            print(f"💰 Preço original: R$ {dados['preco_original']}")
        print(f"🖼️ Imagem: {dados.get('imagem', 'N/A')[:60]}...")
        print(f"📦 Disponível: {'Sim' if dados.get('disponivel') else 'Não'}")
        print(f"🚚 Frete grátis: {'Sim' if dados.get('frete_gratis') else 'Não'}")
    else:
        print(f"❌ Erro: {dados['erro']}")
        if DEBUG_MODE:
            print("\n💡 Dica: Verifique se o arquivo 'debug_ml.html' foi criado")
            print("   Abra no navegador para ver o que o ML está retornando")
    
    print("\n" + "=" * 60)
