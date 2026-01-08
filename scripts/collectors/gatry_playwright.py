from playwright.sync_api import sync_playwright
from pathlib import Path
import json
from datetime import datetime, timezone

URL = "https://gatry.com/"
OUT = Path("data/raw/gatry.json")

def coletar_gatry():
    print("🔎 Coletando Gatry via Playwright (DOM real)…")
    ofertas = []
    vistos = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(6000)

        # scroll para carregar mais artigos
        for _ in range(5):
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(2000)

        artigos = page.locator("article")
        total = artigos.count()
        print(f"🧪 Articles encontrados: {total}")

        for i in range(total):
            try:
                art = artigos.nth(i)

                # título + link externo
                title_el = art.locator("h3 a")
                if title_el.count() == 0:
                    continue

                title = title_el.inner_text().strip()
                url = title_el.get_attribute("href")

                if not title or not url:
                    continue

                # link interno Gatry (para ID)
                promo_el = art.locator("a[href^='/promocoes/']").first
                promo_href = promo_el.get_attribute("href") if promo_el.count() else None

                if not promo_href:
                    continue

                promo_id = promo_href.split("/")[2]  # /promocoes/{id}/slug

                uid = f"gatry-{promo_id}"
                if uid in vistos:
                    continue
                vistos.add(uid)

                # preço
                price_text = None
                try:
                    price_text = art.locator(".price").inner_text().strip()
                except:
                    pass

                # loja
                store = None
                try:
                    store = art.locator(".option-store a").inner_text().replace("Ir para", "").strip()
                except:
                    pass

                ofertas.append({
                    "id": uid,
                    "source": "gatry",
                    "title": title,
                    "url": url,
                    "price_text": price_text,
                    "store": store,
                    "collected_at": datetime.now(timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z")
                })

            except:
                continue

        browser.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(ofertas, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"✅ {len(ofertas)} ofertas salvas em {OUT}")

if __name__ == "__main__":
    coletar_gatry()
