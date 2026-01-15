import logging
import re
import asyncio
import os
import json
import time
from seleniumbase import SB

logging.basicConfig(level=logging.INFO)

# ==============================================================================
# 1. EXTRATOR PELANDO (Resolve o redirecionamento)
# ==============================================================================
def scrape_pelando(url):
    data = None
    final_url = url
    
    with SB(uc=True, headless=True, page_load_strategy="eager") as sb:
        try:
            logging.info(f"🕵️ Pelando: Acessando {url}...")
            sb.activate_cdp_mode(url)
            sb.sleep(4) # Espera carregar
            
            # --- 1. Extração Visual (Título/Preço/Img) ---
            title = ""
            price = 0.0
            image_url = ""
            
            # Tenta seletores variados do Pelando (eles mudam muito as classes)
            try: title = sb.get_text("h1")
            except: pass
            
            # Preço: Procura qualquer R$ grande
            try:
                price_elem = sb.find_element("span[class*='Price'], div[class*='Price']")
                if price_elem:
                    clean = re.sub(r'[^\d,]', '', price_elem.text).replace(',', '.')
                    if clean: price = float(clean)
            except: pass
            
            # Imagem: Pega a imagem principal (geralmente tem alt igual ao titulo ou é a maior)
            try:
                image_url = sb.get_attribute("img[class*='Image']", "src")
            except: pass

            # --- 2. RESOLUÇÃO DE LINK (O Pulo do Gato) ---
            logging.info("🔗 Tentando descobrir o link da loja...")
            try:
                # O botão geralmente é "Pegar promoção" ou um link com /visit/
                # Vamos tentar clicar nele para ver onde vai
                visit_button = "a[href*='/visit/'], button:contains('Pegar promoção')"
                
                if sb.is_element_visible(visit_button):
                    # Salva a URL atual antes do clique
                    sb.click(visit_button)
                    sb.sleep(5) # Espera o redirecionamento acontecer
                    
                    # Verifica se abriu nova aba ou mudou a atual
                    if len(sb.driver.window_handles) > 1:
                        sb.switch_to_window(1)
                        final_url = sb.get_current_url()
                        sb.driver.close()
                        sb.switch_to_window(0)
                    else:
                        final_url = sb.get_current_url()
                    
                    logging.info(f"✅ Link da loja descoberto: {final_url}")
                else:
                    logging.warning("⚠️ Botão de ir para loja não encontrado.")
            except Exception as e:
                logging.warning(f"⚠️ Erro ao resolver link: {e}")

            # Define a loja baseado na URL final descoberta
            store_name = "Oferta"
            if "shopee" in final_url: store_name = "Shopee"
            elif "amazon" in final_url: store_name = "Amazon"
            elif "magalu" in final_url or "magazine" in final_url: store_name = "Magalu"

            if title:
                data = {
                    "title": title,
                    "price": price,
                    "original_price": price,
                    "image": image_url,
                    "store": store_name,
                    "original_url": final_url # Importante: Retorna o link da loja, não do Pelando!
                }

        except Exception as e:
            logging.error(f"❌ Erro Pelando: {e}")
            
    return data

# ==============================================================================
# 2. EXTRATOR SHOPEE (Via API Injection - Mais seguro que visual)
# ==============================================================================
def scrape_shopee_injection(url):
    data = None
    clean_url = url.split('?')[0]
    ids = re.findall(r'(\d{9,})', clean_url) # IDs Shopee
    if not ids: 
        # Tenta IDs curtos se falhar
        ids = re.findall(r'(\d{8,})', clean_url)
    
    shop_id, item_id = None, None
    if len(ids) >= 2:
        shop_id = ids[-2]
        item_id = ids[-1]
    elif len(ids) == 1:
        item_id = ids[0]

    if not item_id:
        return None

    # Monta a URL da API V4
    api_url = f"https://shopee.com.br/api/v4/item/get?itemid={item_id}"
    if shop_id: api_url += f"&shopid={shop_id}"

    with SB(uc=True, headless=True, page_load_strategy="eager") as sb:
        try:
            logging.info(f"💉 Shopee: Injetando API para ID {item_id}...")
            # Abre a Home (sem login)
            sb.activate_cdp_mode("https://shopee.com.br")
            sb.sleep(3)
            
            # Script JS para buscar os dados direto da API (usando cookies do navegador)
            js = f"""
                window._api_data = null;
                fetch("{api_url}", {{ headers: {{ "x-requested-with": "XMLHttpRequest" }} }})
                .then(r => r.json())
                .then(d => window._api_data = d)
                .catch(e => window._api_data = {{error: e.toString()}});
            """
            sb.execute_script(js)
            
            # Espera a resposta
            for _ in range(20):
                res = sb.execute_script("return window._api_data;")
                if res: break
                sb.sleep(0.3)
            
            if res and ("data" in res or "item" in res):
                item = res.get("data") or res.get("item")
                if item:
                    # Sucesso!
                    title = item.get("name")
                    price = float(item.get("price_min") or item.get("price") or 0) / 100000
                    img = item.get("image")
                    image_url = f"https://cf.shopee.com.br/file/{img}" if img else None
                    
                    logging.info("✅ Dados capturados via Injeção API!")
                    data = {
                        "title": title,
                        "price": price,
                        "original_price": price,
                        "image": image_url,
                        "store": "Shopee",
                        "original_url": url
                    }
        except Exception as e:
            logging.error(f"❌ Erro Shopee Injection: {e}")
            
    return data

# ==============================================================================
# 3. ROTEADOR
# ==============================================================================
async def extract_metadata(raw_url):
    logging.info(f"🧠 Processando: {raw_url}")

    # Rota 1: Pelando
    if "pelando.com.br" in raw_url:
        return await asyncio.to_thread(scrape_pelando, raw_url)

    # Rota 2: Shopee
    if "shopee" in raw_url or "shope.ee" in raw_url:
        data = await asyncio.to_thread(scrape_shopee_injection, raw_url)
        if data: return data
        
        # Fallback Shopee
        logging.warning("⚠️ Shopee falhou. Gerando link simples.")
        return {
            "title": "Oferta Shopee (Ver site)",
            "price": 0.0,
            "original_price": 0.0,
            "image": None,
            "store": "Shopee",
            "original_url": raw_url
        }

    return None