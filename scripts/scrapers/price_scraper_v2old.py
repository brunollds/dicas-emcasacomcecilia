"""
Scraper de Preços Unificado
Em Casa com Cecília

Suporta:
- Mercado Livre (scraping)
- Shopee (scraping)
- Magazine Luiza (scraping)
- Amazon (API)
"""

import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from pathlib import Path
import os

# =====================================================
# CONFIGURAÇÃO DE LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("price_scraper.log"),
        logging.StreamHandler()
    ]
)

# =====================================================
# USER AGENTS
# =====================================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

# =====================================================
# CONFIGURAÇÕES POR LOJA
# =====================================================

STORE_CONFIGS = {
    "Amazon": {
        "price_selectors": [
            "span.a-price-whole", 
            "span.a-offscreen",
            "span#priceblock_ourprice",
            "span#priceblock_dealprice",
            "span.a-price span.a-offscreen"
        ],
        "delay": (1.5, 2.5)  # Amazon rate limit: 1 req/sec
    },
    "Mercado Livre": {
        "price_selectors": [
            "span.andes-money-amount__fraction",
            "span.price-tag-fraction",
            "meta[itemprop='price']"
        ],
        "decimal_selectors": [
            "span.andes-money-amount__cents",
            "span.price-tag-cents"
        ],
        "delay": (1, 2)
    },
    "Shopee": {
        "price_selectors": [
            "div.pqTWkA",
            "div._3n5NQx",
            "div.IZPeQz",
            "div.pmmxKx",
            "span.pqTWkA"
        ],
        "delay": (2, 4)
    },
    "Magazine Luiza": {
        "price_selectors": [
            "p[data-testid='price-value']",
            "span.sc-dcJsrY",
            "span.sc-kpDqfm",
            "p.sc-dcJsrY",
            "div[data-testid='price-value']"
        ],
        "delay": (1, 3)
    },
    "default": {
        "price_selectors": [
            "span.price", 
            "div.price", 
            "p.price", 
            ".product-price"
        ],
        "delay": (1, 3)
    }
}

# Amazon API (carregar do .env se disponível)
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

AMAZON_ACCESS_KEY = os.getenv('AMAZON_ACCESS_KEY', '')
AMAZON_SECRET_KEY = os.getenv('AMAZON_SECRET_KEY', '')
AMAZON_PARTNER_TAG = os.getenv('AMAZON_PARTNER_TAG', '')


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def get_random_user_agent():
    """Retorna um User-Agent aleatório"""
    return random.choice(USER_AGENTS)


def get_headers():
    """Retorna headers para requisição"""
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }


def parse_price(price_text):
    """Converte texto de preço para float"""
    if not price_text:
        return None
    
    # Remover caracteres não numéricos (exceto vírgula e ponto)
    price_text = re.sub(r'[^\d,.]', '', str(price_text))
    
    if not price_text:
        return None
    
    # Formato brasileiro: R$ 1.999,99
    if ',' in price_text and '.' in price_text:
        price_text = price_text.replace('.', '').replace(',', '.')
    # Formato: R$ 1999,99
    elif ',' in price_text:
        price_text = price_text.replace(',', '.')
    
    try:
        price = float(price_text)
        # Validar range razoável
        if 0.01 < price < 1000000:
            return price
    except ValueError:
        pass
    
    return None


# =====================================================
# SCRAPER MERCADO LIVRE
# =====================================================

def scrape_mercadolivre(url):
    """Scraping do Mercado Livre"""
    store_config = STORE_CONFIGS["Mercado Livre"]
    
    try:
        time.sleep(random.uniform(*store_config["delay"]))
        
        response = requests.get(url, headers=get_headers(), timeout=30, allow_redirects=True)
        
        if response.status_code != 200:
            return {"erro": f"Status {response.status_code}"}
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        resultado = {'loja': 'Mercado Livre'}
        
        # Tentar extrair preço via seletores
        price_text = None
        decimal_text = "00"
        
        for selector in store_config["price_selectors"]:
            if selector.startswith("meta"):
                elem = soup.select_one(selector)
                if elem and elem.get('content'):
                    price_text = elem.get('content')
                    break
            else:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.text.strip()
                    break
        
        # Extrair decimais se houver
        if price_text and "decimal_selectors" in store_config:
            for selector in store_config["decimal_selectors"]:
                elem = soup.select_one(selector)
                if elem:
                    decimal_text = elem.text.strip()
                    break
            
            # Combinar inteiro + decimal se necessário
            if ',' not in price_text and '.' not in price_text and decimal_text:
                price_text = f"{price_text}.{decimal_text}"
        
        # Fallback: regex no HTML
        if not price_text:
            match = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?', html)
            if match:
                price_text = match.group(1)
        
        resultado['preco'] = parse_price(price_text)
        
        # Título
        title_elem = soup.select_one('h1.ui-pdp-title')
        if title_elem:
            resultado['titulo'] = title_elem.text.strip()
        else:
            og_title = soup.select_one('meta[property="og:title"]')
            if og_title:
                resultado['titulo'] = og_title.get('content', '').split('|')[0].strip()
        
        # Imagem
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image:
            resultado['imagem'] = og_image.get('content', '')
        
        resultado['disponivel'] = not bool(
            soup.find(string=re.compile(r'não está mais disponível|indisponível|esgotou', re.IGNORECASE))
        )
        
        if not resultado.get('preco'):
            return {"erro": "Preço não encontrado"}
        
        return resultado
        
    except Exception as e:
        return {"erro": str(e)}


# =====================================================
# SCRAPER SHOPEE
# =====================================================

def scrape_shopee(url):
    """
    Scraping da Shopee
    NOTA: Shopee usa muito JavaScript e proteção anti-bot.
    Recomendado usar API oficial quando disponível.
    """
    store_config = STORE_CONFIGS["Shopee"]
    
    try:
        time.sleep(random.uniform(*store_config["delay"]))
        
        # Shopee tem problemas com redirects, usar timeout menor
        response = requests.get(url, headers=get_headers(), timeout=10, allow_redirects=True)
        
        if response.status_code != 200:
            return {"erro": f"Status {response.status_code}"}
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        resultado = {'loja': 'Shopee'}
        
        # Tentar seletores CSS
        price_text = None
        for selector in store_config["price_selectors"]:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.text.strip()
                break
        
        # Fallback: regex para preço no HTML/JSON
        if not price_text:
            # Shopee armazena preço em centavos às vezes
            match = re.search(r'"price"\s*:\s*(\d+)', html)
            if match:
                preco_raw = int(match.group(1))
                # Se for muito alto, provavelmente está em centavos
                if preco_raw > 100000:
                    resultado['preco'] = preco_raw / 100000
                else:
                    resultado['preco'] = preco_raw
        
        if not resultado.get('preco') and price_text:
            resultado['preco'] = parse_price(price_text)
        
        # Fallback: regex R$
        if not resultado.get('preco'):
            match = re.search(r'R\$\s*([\d.,]+)', html)
            if match:
                resultado['preco'] = parse_price(match.group(1))
        
        # Título
        title_elem = soup.select_one('div.qaNIZv span')
        if title_elem:
            resultado['titulo'] = title_elem.text.strip()
        else:
            og_title = soup.select_one('meta[property="og:title"]')
            if og_title:
                resultado['titulo'] = og_title.get('content', '').split('|')[0].strip()
        
        # Imagem
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image:
            resultado['imagem'] = og_image.get('content', '')
        
        resultado['disponivel'] = True
        
        if not resultado.get('preco'):
            return {"erro": "Preço não encontrado (Shopee requer API)"}
        
        return resultado
    
    except requests.exceptions.Timeout:
        return {"erro": "Timeout (Shopee bloqueou)"}
    except requests.exceptions.SSLError:
        return {"erro": "Erro SSL (Shopee bloqueou)"}
    except requests.exceptions.ConnectionError:
        return {"erro": "Conexão recusada (Shopee bloqueou)"}
    except Exception as e:
        return {"erro": f"Erro: {str(e)[:50]}"}


# =====================================================
# SCRAPER MAGAZINE LUIZA
# =====================================================

def scrape_magalu(url):
    """Scraping do Magazine Luiza"""
    store_config = STORE_CONFIGS["Magazine Luiza"]
    
    try:
        time.sleep(random.uniform(*store_config["delay"]))
        
        response = requests.get(url, headers=get_headers(), timeout=30, allow_redirects=True)
        
        if response.status_code != 200:
            return {"erro": f"Status {response.status_code}"}
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        resultado = {'loja': 'Magazine Luiza'}
        
        # Tentar JSON-LD primeiro (mais confiável)
        script_ld = soup.find('script', type='application/ld+json')
        if script_ld:
            try:
                data = json.loads(script_ld.string)
                if isinstance(data, list):
                    data = data[0]
                
                if 'offers' in data:
                    offers = data['offers']
                    if isinstance(offers, list):
                        offers = offers[0]
                    if 'price' in offers:
                        resultado['preco'] = float(offers['price'])
                
                if 'name' in data:
                    resultado['titulo'] = data['name']
                
                if 'image' in data:
                    img = data['image']
                    resultado['imagem'] = img[0] if isinstance(img, list) else img
            except:
                pass
        
        # Fallback: seletores CSS
        if not resultado.get('preco'):
            for selector in store_config["price_selectors"]:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.text.strip()
                    resultado['preco'] = parse_price(price_text)
                    if resultado['preco']:
                        break
        
        # Fallback: regex
        if not resultado.get('preco'):
            match = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?', html)
            if match:
                resultado['preco'] = parse_price(match.group(1))
        
        # Título fallback
        if not resultado.get('titulo'):
            h1 = soup.select_one('h1')
            if h1:
                resultado['titulo'] = h1.text.strip()
        
        resultado['disponivel'] = not bool(
            soup.find(string=re.compile(r'indisponível|esgotado|não disponível', re.IGNORECASE))
        )
        
        if not resultado.get('preco'):
            return {"erro": "Preço não encontrado"}
        
        return resultado
        
    except Exception as e:
        return {"erro": str(e)}


# =====================================================
# AMAZON API
# =====================================================

def scrape_amazon_api(url):
    """Busca preço via Amazon Product Advertising API"""
    
    if not all([AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG]):
        return {"erro": "Credenciais Amazon não configuradas"}
    
    # Delay para respeitar rate limit (1 req/sec)
    time.sleep(random.uniform(1.5, 2.5))
    
    # Extrair ASIN da URL
    asin = None
    
    # Tentar extrair ASIN diretamente
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if match:
        asin = match.group(1)
    else:
        match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
        if match:
            asin = match.group(1)
    
    # Se não encontrou, resolver short link
    if not asin and 'amzn' in url:
        try:
            resp = requests.head(url, allow_redirects=True, timeout=10)
            match = re.search(r'/dp/([A-Z0-9]{10})', resp.url)
            if match:
                asin = match.group(1)
        except:
            pass
    
    if not asin:
        return {"erro": "Não consegui extrair ASIN da URL"}
    
    try:
        # AWS Signature v4
        host = "webservices.amazon.com.br"
        region = "us-east-1"
        service = "ProductAdvertisingAPI"
        
        t = datetime.now(timezone.utc)
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d')
        
        payload = {
            "ItemIds": [asin],
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "Offers.Listings.Price"
            ],
            "PartnerTag": AMAZON_PARTNER_TAG,
            "PartnerType": "Associates",
            "Marketplace": "www.amazon.com.br"
        }
        payload_json = json.dumps(payload, separators=(',', ':'))
        
        def sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
        
        def get_signature_key(key, date_stamp, region, service):
            k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
            k_region = sign(k_date, region)
            k_service = sign(k_region, service)
            k_signing = sign(k_service, 'aws4_request')
            return k_signing
        
        method = 'POST'
        canonical_uri = '/paapi5/getitems'
        canonical_querystring = ''
        
        payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()
        
        canonical_headers = (
            f'content-encoding:amz-1.0\n'
            f'content-type:application/json; charset=utf-8\n'
            f'host:{host}\n'
            f'x-amz-date:{amz_date}\n'
            f'x-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems\n'
        )
        signed_headers = 'content-encoding;content-type;host;x-amz-date;x-amz-target'
        
        canonical_request = (
            f'{method}\n{canonical_uri}\n{canonical_querystring}\n'
            f'{canonical_headers}\n{signed_headers}\n{payload_hash}'
        )
        
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f'{date_stamp}/{region}/{service}/aws4_request'
        
        string_to_sign = (
            f'{algorithm}\n{amz_date}\n{credential_scope}\n'
            f'{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
        )
        
        signing_key = get_signature_key(AMAZON_SECRET_KEY, date_stamp, region, service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        authorization_header = (
            f'{algorithm} Credential={AMAZON_ACCESS_KEY}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, Signature={signature}'
        )
        
        headers = {
            'content-encoding': 'amz-1.0',
            'content-type': 'application/json; charset=utf-8',
            'host': host,
            'x-amz-date': amz_date,
            'x-amz-target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems',
            'Authorization': authorization_header
        }
        
        response = requests.post(
            f'https://{host}{canonical_uri}',
            headers=headers,
            data=payload_json,
            timeout=15
        )
        
        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('Errors', [{}])[0].get('Message', f'Status {response.status_code}')
            return {"erro": error_msg}
        
        data = response.json()
        
        if 'ItemsResult' not in data or not data['ItemsResult'].get('Items'):
            return {"erro": "Produto não encontrado"}
        
        item = data['ItemsResult']['Items'][0]
        resultado = {'loja': 'Amazon'}
        
        if 'ItemInfo' in item and 'Title' in item['ItemInfo']:
            resultado['titulo'] = item['ItemInfo']['Title'].get('DisplayValue', '')
        
        if 'Offers' in item and 'Listings' in item['Offers']:
            listings = item['Offers']['Listings']
            if listings:
                price_info = listings[0].get('Price', {})
                resultado['preco'] = price_info.get('Amount', 0)
        
        if 'Images' in item and 'Primary' in item['Images']:
            resultado['imagem'] = item['Images']['Primary'].get('Large', {}).get('URL', '')
        
        resultado['disponivel'] = True
        
        if not resultado.get('preco'):
            return {"erro": "Preço não encontrado na API"}
        
        return resultado
        
    except Exception as e:
        return {"erro": str(e)}


# =====================================================
# FUNÇÃO PRINCIPAL - DETECTAR LOJA E SCRAPE
# =====================================================

def scrape_preco(url, store_name=None):
    """
    Detecta a loja pelo URL e faz o scraping apropriado.
    
    Args:
        url: URL do produto
        store_name: Nome da loja (opcional, detecta automaticamente)
    
    Retorna:
        dict com preco, titulo, imagem, disponivel, erro
    """
    
    if not url:
        return {"erro": "URL vazia"}
    
    url_lower = url.lower()
    
    # Detectar loja pela URL ou usar nome fornecido
    if store_name:
        loja = store_name
    elif 'mercadolivre' in url_lower or 'mercadolibre' in url_lower:
        loja = 'Mercado Livre'
    elif 'shopee' in url_lower:
        loja = 'Shopee'
    elif 'magazineluiza' in url_lower or 'magalu' in url_lower:
        loja = 'Magazine Luiza'
    elif 'amazon' in url_lower or 'amzn' in url_lower:
        loja = 'Amazon'
    else:
        return {"erro": f"Loja não suportada: {url[:50]}"}
    
    logging.info(f"Scraping {loja}: {url[:60]}...")
    
    if loja == 'Mercado Livre':
        return scrape_mercadolivre(url)
    elif loja == 'Shopee':
        return scrape_shopee(url)
    elif loja == 'Magazine Luiza':
        return scrape_magalu(url)
    elif loja == 'Amazon':
        return scrape_amazon_api(url)
    else:
        return {"erro": f"Loja não implementada: {loja}"}


# =====================================================
# ATUALIZAR PRODUCTS.JSON
# =====================================================

def atualizar_products_json(caminho_json, dry_run=False, lojas=None):
    """
    Atualiza preços de todas as lojas no products.json.
    
    Args:
        caminho_json: Caminho para o arquivo
        dry_run: Se True, não salva alterações
        lojas: Lista de lojas para atualizar (None = todas)
    """
    
    if lojas is None:
        # Shopee removida - usa muito JS e bloqueia scraping
        # Recomendado usar API oficial quando disponível
        lojas = ['Mercado Livre', 'Magazine Luiza', 'Amazon']
    
    caminho = Path(caminho_json)
    
    if not caminho.exists():
        logging.error(f"Arquivo não encontrado: {caminho}")
        return
    
    with open(caminho, 'r', encoding='utf-8') as f:
        produtos = json.load(f)
    
    print(f"📦 {len(produtos)} produtos encontrados")
    print(f"🏪 Lojas: {', '.join(lojas)}")
    print("=" * 60)
    
    stats = {loja: {'atualizados': 0, 'erros': 0, 'sem_alteracao': 0} for loja in lojas}
    
    for i, produto in enumerate(produtos):
        nome = produto.get('name', 'Sem nome')[:40]
        precos = produto.get('prices', {})
        
        print(f"\n[{i+1}/{len(produtos)}] {nome}")
        
        for loja in lojas:
            if loja not in precos:
                continue
            
            link = precos[loja].get('link', '')
            if not link:
                continue
            
            print(f"   🔗 {loja}: ", end='', flush=True)
            
            dados = scrape_preco(link, loja)
            
            if 'erro' in dados:
                print(f"❌ {dados['erro']}")
                stats[loja]['erros'] += 1
                continue
            
            preco_antigo = precos[loja].get('price', 0)
            preco_novo = dados.get('preco', preco_antigo)
            
            if preco_novo and preco_novo != preco_antigo:
                print(f"R${preco_antigo} → R${preco_novo}")
                
                if not dry_run:
                    precos[loja]['price'] = preco_novo
                    produto['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                stats[loja]['atualizados'] += 1
            else:
                print(f"R${preco_novo} (sem alteração)")
                stats[loja]['sem_alteracao'] += 1
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 Resumo por loja:")
    
    total_atualizados = 0
    total_erros = 0
    
    for loja, s in stats.items():
        if s['atualizados'] + s['erros'] + s['sem_alteracao'] > 0:
            print(f"   {loja}:")
            print(f"      ✅ Atualizados: {s['atualizados']}")
            print(f"      ⏸️ Sem alteração: {s['sem_alteracao']}")
            print(f"      ❌ Erros: {s['erros']}")
            total_atualizados += s['atualizados']
            total_erros += s['erros']
    
    print(f"\n   📦 Total: {total_atualizados} atualizados, {total_erros} erros")
    
    if not dry_run and total_atualizados > 0:
        import shutil
        backup_path = str(caminho) + f'.backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
        shutil.copy2(caminho, backup_path)
        print(f"   💾 Backup: {backup_path}")
        
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(produtos, f, ensure_ascii=False, indent=2)
        print(f"   ✅ Salvo: {caminho}")
    elif dry_run:
        print("   ⚠️ Modo dry-run: alterações não foram salvas")
    
    return stats


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper de Preços Unificado')
    parser.add_argument('--update', '-u', help='Atualizar products.json')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Não salvar alterações')
    parser.add_argument('--lojas', '-l', nargs='+', help='Lojas específicas para atualizar')
    parser.add_argument('--test', '-t', help='Testar URL específica')
    
    args = parser.parse_args()
    
    if args.test:
        print("=" * 60)
        print("🧪 Teste de URL")
        print("=" * 60)
        resultado = scrape_preco(args.test)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    elif args.update:
        atualizar_products_json(args.update, dry_run=args.dry_run, lojas=args.lojas)
    
    else:
        # Teste padrão
        print("=" * 60)
        print("🛒 Scraper Unificado - Em Casa com Cecília")
        print("=" * 60)
        
        # Testar ML
        print("\n📍 Testando Mercado Livre...")
        resultado = scrape_mercadolivre("https://www.mercadolivre.com.br/cafeteira-nespresso-essenza-mini-d30-automatica-preta-para-capsulas-monodose/p/MLB19112932")
        if 'erro' not in resultado:
            print(f"   ✅ Preço: R$ {resultado.get('preco')}")
        else:
            print(f"   ❌ {resultado['erro']}")
        
        print("\n" + "=" * 60)
        print("💡 Uso:")
        print("   python price_scraper_v2.py --update ../public/data/products.json")
        print("   python price_scraper_v2.py --update ../public/data/products.json --dry-run")
        print("   python price_scraper_v2.py --test 'URL_DO_PRODUTO'")
        print("=" * 60)
