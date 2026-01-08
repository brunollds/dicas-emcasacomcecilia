from playwright.sync_api import sync_playwright
from pathlib import Path
import json
from datetime import datetime, timezone
import re
import time

URL = "https://gafanho.to/recentes"
OUT = Path("data/raw/gafanho.json")

def clean_price(price_str):
    if not price_str: return None
    # Remove R$, espaços e caracteres não numéricos exceto vírgula e ponto
    clean = re.sub(r'[^\d,\.]', '', str(price_str))
    clean = clean.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None

def smart_scroll(page, max_scrolls=20):
    """
    Rola a página até parar de crescer ou atingir o limite.
    No Gafanho, monitoramos a altura do scroll (scrollHeight) pois não temos um seletor fácil.
    """
    print(f"📜 Iniciando Scroll (Max: {max_scrolls} tentativas)...")
    last_height = 0
    
    for i in range(max_scrolls):
        # Pega altura atual
        new_height = page.evaluate("document.body.scrollHeight")
        
        if new_height == last_height:
            print("   ⏹️ Fim da página alcançado (altura parou de crescer).")
            break
            
        # Rola até o fim
        page.keyboard.press("End")
        page.wait_for_timeout(2000) # Gafanho é um pouco mais lento para renderizar
        
        print(f"   ↳ Scroll {i+1}/{max_scrolls} (Altura: {new_height})")
        last_height = new_height

def coletar_gafanho():
    print(f"🔎 Coletando Gafanho.to (Angular Scope + Scroll) - {URL}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        
        # 1. Garante que carregou o inicial
        page.wait_for_timeout(3000)

        # 2. Scroll para carregar histórico
        smart_scroll(page, max_scrolls=15) 

        # 3. Extração via Angular (Sua lógica original, que é excelente)
        raw_posts = page.evaluate("""
        () => {
            if (typeof angular === 'undefined') return [];
            const results = [];
            // O Gafanho costuma ter um controller principal que segura todos os posts
            document.querySelectorAll('*').forEach(el => {
                try {
                    const scope = angular.element(el).scope();
                    if (scope && scope.posts && Array.isArray(scope.posts) && scope.posts.length > 0) {
                        // Evita duplicar se achar varios elementos com o mesmo scope
                        if(results.length === 0 || results[0].length < scope.posts.length) {
                             results.push(scope.posts);
                        }
                    }
                } catch (e) {}
            });
            // Retorna o array mais longo encontrado (o que contem todos os posts carregados)
            return results.sort((a, b) => b.length - a.length)[0] || [];
        }
        """)
        
        browser.close()

    print(f"🧪 Itens brutos capturados via Angular: {len(raw_posts)}")

    # 4. Normalização e Limpeza (Para ficar igual ao Pelando/Promobit)
    ofertas = []
    ids_vistos = set()

    for post in raw_posts:
        try:
            # Evita duplicatas (Angular as vezes mantém lixo)
            pid = str(post.get("id"))
            if pid in ids_vistos:
                continue
            ids_vistos.add(pid)

            # Preço: Gafanho manda "R$ 1.500,00"
            price = clean_price(post.get("price"))
            
            # Link: Gafanho manda varios, pegamos o primeiro principal
            url_oferta = post.get("links", "")
            if " " in url_oferta: # Às vezes vem múltiplos links separados por espaço
                url_oferta = url_oferta.split(" ")[0]

            item = {
                "id": pid,
                "source": "gafanho",
                "title": post.get("title", "").strip(),
                "url": url_oferta,
                "price": price,
                "price_text": post.get("price"),
                "store": post.get("storeName"),
                "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
            
            ofertas.append(item)
        except Exception:
            continue

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(ofertas, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ {len(ofertas)} ofertas normalizadas salvas em {OUT}")

if __name__ == "__main__":
    coletar_gafanho()



