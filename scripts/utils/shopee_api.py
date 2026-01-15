import requests
import json
import hashlib
import time

def get_shopee_product_info(url):
    """Tenta pegar informações do produto via API da Shopee"""
    try:
        # Extrai shop_id e item_id da URL
        import re
        match = re.search(r'(\d{8,})[./](\d{8,})', url)
        if not match:
            return None
        
        shop_id, item_id = match.groups()
        
        # API pública da Shopee
        api_url = f"https://shopee.com.br/api/v4/item/get"
        params = {
            "itemid": item_id,
            "shopid": shop_id
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://shopee.com.br/"
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            item = data.get('data', {})
            
            return {
                "title": item.get('name', ''),
                "price": float(item.get('price', 0)) / 100000,  # Shopee usa centavos
                "image": f"https://cf.shopee.com.br/file/{item.get('image', '')}",
                "store": "Shopee",
                "original_url": url
            }
    except Exception as e:
        print(f"Erro API Shopee: {e}")
    
    return None