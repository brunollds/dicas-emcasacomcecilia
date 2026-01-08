from pathlib import Path
import json
import re
from datetime import datetime, timezone, timedelta

# --- Configuração ---
RAW_DIR = Path("data/raw")
OUT = Path("data/inbox/unified.json")
TZ_BR = timezone(timedelta(hours=-3))

def parse_price(text):
    if text is None: return None
    if isinstance(text, (int, float)): return float(text)
    # Limpeza bruta de preço
    text = str(text).replace("R$", "").replace("\xa0", "").strip()
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except:
        return None

def normalize_item(item, source):
    # 1. TÍTULO (Busca em todas as variações possíveis)
    title = item.get("title") or item.get("offerTitle") or item.get("name")
    
    # 2. URL (Onde o bicho pega: Gafanho usa 'links', Promobit usa 'offerSlug')
    url = item.get("url") or item.get("link") or item.get("offerLink") or item.get("links")
    
    # Tratamento especial Promobit se não tiver URL
    if not url and source == "promobit" and item.get("offerSlug"):
        url = f"https://www.promobit.com.br/oferta/{item['offerSlug']}"
    
    # Tratamento Gafanho (às vezes vem vários links separados por espaço)
    if url and isinstance(url, str) and " " in url:
        url = url.split(" ")[0]

    if not title or not url:
        return None

    # 3. PREÇO
    price = item.get("price")
    if price is None:
        price_text = item.get("price_text") or item.get("offerPrice") or item.get("priceText")
        price = parse_price(price_text)
    
    # Regra: Se não tem preço, aceitamos se tiver ID (para histórico), 
    # mas marcamos como 0.0 para não quebrar ordenação
    if price is None:
        price = 0.0

    # 4. LOJA e IMAGEM
    store = item.get("store") or item.get("storeName") or item.get("store_name") or "Desconhecida"
    image = item.get("image") or item.get("imageUrlBig") or item.get("offerPhoto") or item.get("img")
    
    # Ajuste URL de imagem relativa
    if image and image.startswith("/") and source == "promobit":
        image = "https://www.promobit.com.br" + image

    # 5. DATAS
    collected_at = item.get("collected_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # 6. ID UNIVERSAL
    raw_id = str(item.get("id") or item.get("offerId") or "")
    if not raw_id:
        raw_id = str(abs(hash(url)))

    # Garante prefixo único (ex: gatry-123)
    prefix = f"{source}-"
    uid = raw_id if raw_id.startswith(prefix) else f"{prefix}{raw_id}"

    return {
        "id": uid,
        "source": source,
        "title": str(title).strip(),
        "price": price,
        "store": str(store).strip(),
        "url": str(url).strip(),
        "image": image,
        "collected_at": collected_at,
        "raw": item
    }

def main():
    print("🔄 Iniciando Unificação V4 (Universal)...")
    unified = []
    ids_vistos = set()

    if not RAW_DIR.exists():
        print(f"❌ Pasta {RAW_DIR} não existe!")
        return

    # Ignora arquivos de debug
    arquivos = [f for f in sorted(RAW_DIR.glob("*.json")) if "debug" not in f.name]

    for file in arquivos:
        source = file.stem 
        print(f"   📂 Lendo: {file.name}...", end=" ")
        
        try:
            content = file.read_text(encoding="utf-8")
            if not content.strip(): continue
            data = json.loads(content)
        except:
            print("❌ Erro ao ler JSON.")
            continue

        if not isinstance(data, list): continue

        count_local = 0
        for item in data:
            try:
                norm = normalize_item(item, source)
                if not norm: continue
                
                # Deduplicação
                if norm['id'] in ids_vistos: continue
                
                # Filtro opcional: Se quiser ignorar itens sem preço REAL
                if norm['price'] == 0 and source != "promobit": # Promobit as vezes tem grátis válido
                     pass 
                
                unified.append(norm)
                ids_vistos.add(norm['id'])
                count_local += 1
            except: continue
        
        print(f"✅ {count_local} itens recuperados.")

    # Ordena pelo mais recente
    unified.sort(key=lambda x: x['collected_at'], reverse=True)
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(unified, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n🎉 Resultado Final: {len(unified)} ofertas em {OUT}")

if __name__ == "__main__":
    main()
