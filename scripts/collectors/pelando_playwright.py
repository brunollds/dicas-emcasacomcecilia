from playwright.sync_api import sync_playwright
from pathlib import Path
import json
from datetime import datetime, timezone
import re
import time

# 1. AJUSTE CONFIRMADO: URL correta para pegar o feed cronológico
URL = "https://www.pelando.com.br/recentes"
OUT = Path("data/raw/pelando.json")

def clean_price(price_str):
    if not price_str: return None
    # Remove tudo que não for dígito, vírgula ou ponto
    clean = re.sub(r'[^\d,\.]', '', price_str)
    # Padroniza para formato float (ponto decimal)
    clean = clean.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None

def smart_scroll(page, min_items=150, max_retries=5):
    """
    Rola a página pressionando END até atingir a meta de itens.
    """
    print(f"📜 Iniciando Scroll Inteligente (Meta: ~{min_items} ofertas)...")
    
    last_count = 0
    retries = 0
    
    while True:
        # Pressiona END para ir ao rodapé
        page.keyboard.press("End")
        page.wait_for_timeout(2000) # Espera o site carregar novos itens
        
        links = page.locator('a[href^="https://www.pelando.com.br/d/"]')
        current_count = links.count()
        offers_estimate = current_count // 4
        
        print(f"   ↳ Links encontrados: {current_count} (~{offers_estimate} ofertas)")
        
        if offers_estimate >= min_items:
            print("   ✅ Meta de ofertas atingida!")
            break
            
        if current_count == last_count:
            retries += 1
            # Tenta desenroscar com scroll manual
            page.mouse.wheel(0, -500)
            page.wait_for_timeout(500)
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(1000)
            
            if retries >= max_retries:
                print("   ⏹️ O site parou de carregar novos itens.")
                break
        else:
            retries = 0
            
        last_count = current_count

def coletar_pelando():
    print(f"🔎 Coletando Pelando - Aba RECENTES ({URL})...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(5000) # Espera inicial segura

        # 1. Executa o Scroll Inteligente
        smart_scroll(page, min_items=150)

        # 2. Coleta Link Brutos
        links = page.locator('a[href^="https://www.pelando.com.br/d/"]')
        count = links.count()
        print(f"🧪 Total final de links para processar: {count}")

        candidates = {}

        # 3. Agrupamento por URL (Lógica vencedora)
        for i in range(count):
            try:
                el = links.nth(i)
                href = el.get_attribute("href")
                if not href: continue
                
                clean_url = href.split("#")[0]
                if "#comments" in clean_url: continue

                text = el.inner_text().strip()
                
                if clean_url not in candidates:
                    candidates[clean_url] = []
                
                candidates[clean_url].append({
                    'index': i,
                    'text': text,
                    'length': len(text)
                })
            except:
                continue

        print(f"📦 Ofertas únicas identificadas: {len(candidates)}")
        
        ofertas = []

        # 4. Extração final de dados
        for url, items in candidates.items():
            try:
                # O link com maior texto é o título
                best_link = max(items, key=lambda x: x['length'])
                if best_link['length'] == 0: continue

                el = links.nth(best_link['index'])
                title = best_link['text']
                
                # Busca profunda de preço e loja (subindo no DOM)
                price, price_text, store_name = None, None, None
                card_text = title
                parent = el
                
                for _ in range(6):
                    try:
                        parent = parent.locator("xpath=..")
                        full_text = parent.inner_text()
                        if "R$" in full_text or "Vendido por" in full_text:
                            card_text = full_text
                            if "R$" in full_text: break
                    except: break

                m_price = re.search(r"R\$\s*[\d\.,]+", card_text)
                if m_price:
                    price_text = m_price.group(0)
                    price = clean_price(price_text)

                m_store = re.search(r"Vendido por\s*(.*?)(?:\n|$|\r)", card_text, re.IGNORECASE)
                if m_store:
                    store_name = m_store.group(1).strip().replace("*", "")

                item = {
                    "id": url.split("/")[-1].split("?")[0],
                    "source": "pelando",
                    "title": title,
                    "url": url,
                    "price": price,
                    "price_text": price_text,
                    "store": store_name,
                    "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                }
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
    coletar_pelando()
