"""
Amazon Product Advertising API
Em Casa com Cecília

Busca dados de produtos da Amazon (preço, imagem, título)
"""

import requests
import json
import re
import hashlib
import hmac
import datetime
from urllib.parse import quote

# =====================================================
# CREDENCIAIS
# =====================================================

ACCESS_KEY = "AKPAN57HRO1765836936"
SECRET_KEY = "kiQc99K51XtABwhDeIBOFV/luZtNZvH910BWQi91"
PARTNER_TAG = "ceciliamauadc-20"

# Região Brasil
HOST = "webservices.amazon.com.br"
REGION = "us-east-1"
SERVICE = "ProductAdvertisingAPI"

# =====================================================
# ASSINATURA AWS (Signature Version 4)
# =====================================================

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing

def create_signed_request(operation, payload):
    """Cria requisição assinada para a Amazon PA API"""
    
    method = 'POST'
    endpoint = f'https://{HOST}/paapi5/{operation.lower()}'
    
    # Timestamps
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    # Headers canônicos
    content_type = 'application/json; charset=UTF-8'
    
    canonical_uri = f'/paapi5/{operation.lower()}'
    canonical_querystring = ''
    
    # Payload
    request_body = json.dumps(payload)
    payload_hash = hashlib.sha256(request_body.encode('utf-8')).hexdigest()
    
    canonical_headers = (
        f'content-encoding:amz-1.0\n'
        f'content-type:{content_type}\n'
        f'host:{HOST}\n'
        f'x-amz-date:{amz_date}\n'
        f'x-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{operation}\n'
    )
    
    signed_headers = 'content-encoding;content-type;host;x-amz-date;x-amz-target'
    
    canonical_request = (
        f'{method}\n'
        f'{canonical_uri}\n'
        f'{canonical_querystring}\n'
        f'{canonical_headers}\n'
        f'{signed_headers}\n'
        f'{payload_hash}'
    )
    
    # String to sign
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f'{date_stamp}/{REGION}/{SERVICE}/aws4_request'
    
    string_to_sign = (
        f'{algorithm}\n'
        f'{amz_date}\n'
        f'{credential_scope}\n'
        f'{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
    )
    
    # Assinatura
    signing_key = get_signature_key(SECRET_KEY, date_stamp, REGION, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    authorization_header = (
        f'{algorithm} '
        f'Credential={ACCESS_KEY}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, '
        f'Signature={signature}'
    )
    
    headers = {
        'content-encoding': 'amz-1.0',
        'content-type': content_type,
        'host': HOST,
        'x-amz-date': amz_date,
        'x-amz-target': f'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{operation}',
        'Authorization': authorization_header,
    }
    
    return endpoint, headers, request_body


# =====================================================
# FUNÇÕES DE BUSCA
# =====================================================

def extrair_asin(url):
    """Extrai ASIN de uma URL da Amazon"""
    if not url:
        return None
    
    # Padrão: /dp/B0XXXXX ou /gp/product/B0XXXXX
    match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    # Padrão: /product/B0XXXXX
    match = re.search(r'/product/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    
    # ASIN direto
    match = re.match(r'^[A-Z0-9]{10}$', url.strip())
    if match:
        return url.strip()
    
    return None


def buscar_produto_amazon(asin):
    """
    Busca dados de um produto pelo ASIN.
    
    Retorna:
    {
        "asin": str,
        "titulo": str,
        "preco": float,
        "preco_original": float,
        "imagem": str,
        "link": str,
        "disponivel": bool
    }
    """
    
    payload = {
        "PartnerTag": PARTNER_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com.br",
        "ItemIds": [asin],
        "Resources": [
            "Images.Primary.Large",
            "ItemInfo.Title",
            "Offers.Listings.Price",
            "Offers.Listings.SavingBasis",
            "Offers.Listings.Availability.Type",
        ]
    }
    
    try:
        endpoint, headers, body = create_signed_request("GetItems", payload)
        
        response = requests.post(endpoint, headers=headers, data=body, timeout=15)
        
        if response.status_code != 200:
            return {"erro": f"Status {response.status_code}: {response.text[:200]}", "asin": asin}
        
        data = response.json()
        
        # Verificar erros
        if 'Errors' in data:
            erro = data['Errors'][0].get('Message', 'Erro desconhecido')
            return {"erro": erro, "asin": asin}
        
        items = data.get('ItemsResult', {}).get('Items', [])
        if not items:
            return {"erro": "Produto não encontrado", "asin": asin}
        
        item = items[0]
        
        # Extrair dados
        resultado = {
            "asin": item.get('ASIN'),
            "link": item.get('DetailPageURL'),
        }
        
        # Título
        item_info = item.get('ItemInfo', {})
        titulo = item_info.get('Title', {}).get('DisplayValue')
        if titulo:
            resultado['titulo'] = titulo
        
        # Imagem
        images = item.get('Images', {})
        primary = images.get('Primary', {})
        large = primary.get('Large', {})
        if large.get('URL'):
            resultado['imagem'] = large['URL']
        
        # Preço
        offers = item.get('Offers', {})
        listings = offers.get('Listings', [])
        if listings:
            listing = listings[0]
            
            price = listing.get('Price', {})
            if price.get('Amount'):
                resultado['preco'] = price['Amount']
            
            # Preço original (de)
            saving_basis = listing.get('SavingBasis', {})
            if saving_basis.get('Amount'):
                resultado['preco_original'] = saving_basis['Amount']
            
            # Disponibilidade
            availability = listing.get('Availability', {})
            resultado['disponivel'] = availability.get('Type') == 'Now'
        
        return resultado
        
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro de conexão: {str(e)}", "asin": asin}
    except Exception as e:
        return {"erro": f"Erro: {str(e)}", "asin": asin}


def buscar_por_url(url):
    """Busca produto a partir da URL da Amazon"""
    
    asin = extrair_asin(url)
    if not asin:
        return {"erro": "Não consegui extrair ASIN da URL", "url": url}
    
    return buscar_produto_amazon(asin)


def buscar_por_termo(termo, limite=5):
    """
    Busca produtos por termo de pesquisa.
    """
    
    payload = {
        "PartnerTag": PARTNER_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com.br",
        "Keywords": termo,
        "SearchIndex": "All",
        "ItemCount": limite,
        "Resources": [
            "Images.Primary.Medium",
            "ItemInfo.Title",
            "Offers.Listings.Price",
        ]
    }
    
    try:
        endpoint, headers, body = create_signed_request("SearchItems", payload)
        
        response = requests.post(endpoint, headers=headers, data=body, timeout=15)
        
        if response.status_code != 200:
            return {"erro": f"Status {response.status_code}"}
        
        data = response.json()
        
        if 'Errors' in data:
            return {"erro": data['Errors'][0].get('Message', 'Erro')}
        
        items = data.get('SearchResult', {}).get('Items', [])
        
        resultados = []
        for item in items:
            r = {
                "asin": item.get('ASIN'),
                "link": item.get('DetailPageURL'),
            }
            
            titulo = item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue')
            if titulo:
                r['titulo'] = titulo
            
            imagem = item.get('Images', {}).get('Primary', {}).get('Medium', {}).get('URL')
            if imagem:
                r['imagem'] = imagem
            
            listings = item.get('Offers', {}).get('Listings', [])
            if listings:
                preco = listings[0].get('Price', {}).get('Amount')
                if preco:
                    r['preco'] = preco
            
            resultados.append(r)
        
        return resultados
        
    except Exception as e:
        return {"erro": str(e)}


# =====================================================
# ATUALIZAR JSON
# =====================================================

def atualizar_products_json(caminho_json, dry_run=False):
    """Atualiza preços/imagens dos produtos Amazon no products.json"""
    
    import time
    from pathlib import Path
    
    caminho = Path(caminho_json)
    
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
        
        if 'Amazon' not in precos:
            ignorados += 1
            continue
        
        link = precos['Amazon'].get('link', '')
        if not link:
            ignorados += 1
            continue
        
        print(f"\n[{i+1}/{len(produtos)}] {nome}...")
        
        # Delay para não exceder rate limit
        time.sleep(1)
        
        dados = buscar_por_url(link)
        
        if 'erro' in dados:
            print(f"   ❌ {dados['erro']}")
            erros += 1
            continue
        
        alteracoes = []
        
        if dados.get('preco'):
            preco_antigo = precos['Amazon'].get('price')
            preco_novo = dados['preco']
            
            if preco_antigo != preco_novo:
                alteracoes.append(f"Preço: R${preco_antigo} → R${preco_novo}")
                if not dry_run:
                    precos['Amazon']['price'] = preco_novo
        
        if dados.get('imagem') and not produto.get('image'):
            alteracoes.append(f"Imagem adicionada")
            if not dry_run:
                produto['image'] = dados['imagem']
        
        if alteracoes:
            atualizados += 1
            for alt in alteracoes:
                print(f"   ✅ {alt}")
        else:
            print(f"   ⏸️ Sem alterações")
    
    print("\n" + "=" * 60)
    print(f"📊 Resumo: ✅ {atualizados} | ❌ {erros} | ⏭️ {ignorados}")
    
    if not dry_run and atualizados > 0:
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(produtos, f, ensure_ascii=False, indent=2)
        print(f"💾 Arquivo atualizado!")
    
    return {"atualizados": atualizados, "erros": erros}


# =====================================================
# TESTE
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛒 Amazon Product Advertising API")
    print("   Em Casa com Cecília")
    print("=" * 60)
    
    # Teste 1: Buscar por ASIN
    print("\n📍 Teste 1: Buscar por ASIN")
    print("-" * 50)
    
    # ASIN de exemplo (Echo Dot)
    asin_teste = "B09B8VGCR8"
    
    dados = buscar_produto_amazon(asin_teste)
    
    if 'erro' not in dados:
        print(f"✅ {dados.get('titulo', 'N/A')[:50]}...")
        print(f"   💰 R$ {dados.get('preco', 'N/A')}")
        print(f"   🖼️ {dados.get('imagem', 'N/A')[:50]}...")
    else:
        print(f"❌ {dados['erro']}")
    
    # Teste 2: Buscar por termo
    print("\n📍 Teste 2: Buscar 'echo dot'")
    print("-" * 50)
    
    resultados = buscar_por_termo("echo dot", limite=3)
    
    if isinstance(resultados, list):
        for r in resultados:
            print(f"✅ {r.get('titulo', 'N/A')[:40]}... - R$ {r.get('preco', 'N/A')}")
    else:
        print(f"❌ {resultados.get('erro', 'Erro')}")
    
    print("\n" + "=" * 60)
