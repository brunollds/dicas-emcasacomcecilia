from playwright.sync_api import sync_playwright
from pathlib import Path
import json
from datetime import datetime, timezone
import re

URL = "https://www.promobit.com.br/promocoes/recentes/"
OUT = Path("data/raw/promobit.json")

def clean_price(price_str):
    if not price_str: return None
    clean = re.sub(r'[^\d,\.]', '', price_str)
    clean = clean.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None

def clean_title(raw_text, store_name):
    """
    Limpa o título removendo loja, preço, e badges comuns.
    Ex: "amazon.com.br Frete Grátis iPhone 15 R$ 5000" -> "iPhone 15"
    """
    if not raw_text: return ""
    
    # 1. Corta tudo a partir do primeiro "R$" (Preço)
    text = raw_text.split("R$")[0]
    
    # 2. Remove o nome da loja do início (case insensitive)
    if store_name:
        text = re.sub(f"^{re.escape(store_name)}", "", text, flags=re.IGNORECASE)
    
    # 3. Remove badges comuns do início
    badges = ["Frete Grátis", "Parcelado", "Nacional", "Internacional", "Gold", "Platinum"]
    for badge in badges:
        text = re.sub(f"^{badge}", "", text.strip(), flags=re.IGNORECASE)
        
    return text.strip()

def smart_scroll(page, min_items=100, max_retries=5):
    print(f"📜 Iniciando Scroll Inteligente (Meta: ~{min_items} ofertas)...")
    last_count = 0
    retries = 0
    
    while True:
        page.keyboard.press("End")
        page.wait_for_timeout(2500)
        
        links = page.locator('a[href^="/oferta/"]')
        current_count = links.count()
        # Promobit costuma ter links duplicados por card (img + titulo), estimamos /2
        offers_estimate = current_count 
        
        print(f"   ↳ Links encontrados: {current_count}")
        
        if offers_estimate >= min_items:
            print("   ✅ Meta atingida!")
            break
            
        if current_count == last_count:
            retries += 1
            page.mouse.wheel(0, -500)
            page.wait_for_timeout(500)
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(1000)
            
            if retries >= max_retries:
                print("   ⏹️ Site parou de carregar.")
                break
        else:
            retries = 0
        last_count = current_count

def coletar_promobit():
    print(f"🔎 Coletando Promobit (Visual/DOM) - {URL}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(5000)

        # 1. Scroll
        smart_scroll(page, min_items=100)

        # 2. Coleta Links
        links = page.locator('a[href^="/oferta/"]')
        count = links.count()
        print(f"🧪 Total de links brutos: {count}")

        candidates = {}

        # 3. Agrupamento
        for i in range(count):
            try:
                el = links.nth(i)
                href = el.get_attribute("href")
                if not href: continue
                
                full_url = "https://www.promobit.com.br" + href.split("#")[0]
                text = el.inner_text().strip()
                
                if full_url not in candidates:
                    candidates[full_url] = []
                
                candidates[full_url].append({
                    'index': i,
                    'text': text,
                    'length': len(text)
                })
            except:
                continue

        print(f"📦 Ofertas únicas identificadas: {len(candidates)}")
        
        ofertas = []

        # 4. Extração e Limpeza
        for url, items in candidates.items():
            try:
                best_link = max(items, key=lambda x: x['length'])
                el = links.nth(best_link['index'])
                
                # Texto Bruto (contém Loja + Titulo + Preço)
                raw_text = best_link['text']
                if not raw_text: raw_text = el.get_attribute("title") or ""
                
                price, price_text, store_name = None, None, None
                
                # Busca Preço no texto bruto
                m_price = re.search(r"R\$\s*[\d\.,]+", raw_text)
                if m_price:
                    price_text = m_price.group(0)
                    price = clean_price(price_text)
                
                # Busca Loja (Domínios .com .br no início)
                m_store = re.search(r"([a-zA-Z0-9-]+\.(com|net|org)(\.br)?)", raw_text)
                if m_store:
                    store_name = m_store.group(0)
                else:
                    # Fallback: tenta pegar a primeira palavra se não for R$
                    parts = raw_text.split("\n")
                    if parts and "R$" not in parts[0] and len(parts[0]) < 20:
                        store_name = parts[0]

                # LIMPEZA DO TÍTULO
                clean_title_text = clean_title(raw_text, store_name)

                item = {
                    "id": url.strip("/").split("-")[-1],
                    "source": "promobit",
                    "title": clean_title_text,
                    "url": url,
                    "price": price,
                    "price_text": price_text,
                    "store": store_name,
                    "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                }
                
                if item["title"]:
                    ofertas.append(item)

            except Exception:
                continue

        browser.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(ofertas, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ {len(ofertas)} ofertas salvas em {OUT}")

if __name__ == "__main__":
    coletar_promobit()


