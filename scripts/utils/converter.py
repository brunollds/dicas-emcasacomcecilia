import os
import re
import time
import json
import hashlib
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse

load_dotenv()

AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG")
MAGALU_ID = os.getenv("MAGALU_ID")
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET")

def generate_shopee_link(original_url):
    """Gera link curto usando a API de Afiliados Shopee (Corrigido SubID)"""
    if not SHOPEE_APP_ID or not SHOPEE_SECRET:
        return None

    try:
        url_api = "https://open-api.affiliate.shopee.com.br/graphql"
        timestamp = int(time.time())
        
        # --- CORREÇÃO FINAL: SubID sem caracteres especiais ---
        # Antes: "bot_telegram" (Inválido por causa do '_')
        # Agora: "telegram" (Válido)
        query = f'''mutation {{
            generateShortLink(input: {{ originUrl: "{original_url}", subIds: ["telegram"] }}) {{
                shortLink
            }}
        }}'''
        
        payload_dict = {"query": query}
        payload_str = json.dumps(payload_dict)
        
        # Assinatura
        base_string = f"{SHOPEE_APP_ID}{timestamp}{payload_str}{SHOPEE_SECRET}"
        signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"
        }
        
        print(f"⏳ Shopee: Gerando link via API...")
        response = requests.post(url_api, headers=headers, data=payload_str, timeout=10)
        data = response.json()
        
        # Debug de erro
        if "errors" in data:
            print(f"⚠️ Erro Shopee API: {data['errors'][0]['message']}")
            return None
            
        if "data" in data and data["data"] and "generateShortLink" in data["data"]:
            short_link = data["data"]["generateShortLink"]["shortLink"]
            print(f"✅ Shopee: Link gerado: {short_link}")
            return short_link
            
        return None

    except Exception as e:
        print(f"❌ Shopee Exception: {e}")
        return None

def convert_link(url, store):
    print(f"--- CONVERTENDO: {store} ---")
    
    # 1. AMAZON
    if store == "Amazon" and AMAZON_PARTNER_TAG:
        asin_match = re.search(r'/(?:dp|gp/product)/([A-Za-z0-9]{10})', url)
        if asin_match:
            return f"https://www.amazon.com.br/dp/{asin_match.group(1)}?tag={AMAZON_PARTNER_TAG}&linkCode=sl1&language=pt_BR"
        if "tag=" not in url:
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}tag={AMAZON_PARTNER_TAG}&linkCode=sl1&language=pt_BR"
        return url

    # 2. MAGALU
    if store == "Magalu" and MAGALU_ID:
        clean_id = MAGALU_ID.lower().replace("magazine", "").replace("voce", "").strip()
        match = re.search(r'magazineluiza\.com\.br(/.*)', url)
        path = match.group(1) if match else urlparse(url).path
        path = re.sub(r'/magazine[^/]+/', '/', path)
        final = f"https://www.magazinevoce.com.br/magazine{clean_id}{path}".replace("//p/", "/p/")
        return final

    # 3. SHOPEE
    if store == "Shopee":
        # Tenta API Oficial (Agora com SubID correto)
        short_link = generate_shopee_link(url)
        if short_link:
            return short_link
            
        # Fallback (Só acontece se API falhar)
        if "shope.ee" in url: return url
        match = re.search(r'(\d{8,})[./](\d{8,})', url)
        if match:
            return f"https://shopee.com.br/product/{match.group(1)}/{match.group(2)}"
        return url.split('?')[0]

    # 4. MERCADO LIVRE
    if store == "Mercado Livre":
        if "/sec/" in url: return url
        try:
            match = re.search(r'(MLB-?\d+)', url)
            if match:
                mlb_id = match.group(1).replace("-", "")
                return f"https://produto.mercadolivre.com.br/MLB-{mlb_id[3:]}"
            return url.split('?')[0]
        except:
            return url

    return url