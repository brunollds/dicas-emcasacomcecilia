import json
from pathlib import Path
from datetime import datetime, timezone

INBOX_FILE = Path("data/inbox/unified.json")
OUT_FILE = Path("data/inbox/ranked.json")

# ======================================================
# 🔒 Lista de Lojas Permitidas (Suas Afiliações)
# ======================================================
# Se a loja não contiver uma dessas palavras, será descartada.
ALLOWED_STORES = [
    "amazon", 
    "shopee", 
    "mercado livre", "mercadolivre", 
    "magalu", "magazine luiza", "magazine voce",
    "aliexpress", 
    "damie", 
    "tiktok"
]

# Palavras que banem o produto (acessórios inúteis, serviços)
BLOCKLIST = [
    "capinha", "capa para", "película", "pelicula", 
    "cabo usb", "adaptador", "suporte para", 
    "aluguel", "assinatura", "curso", "ebook", 
    "conserto", "manutenção", "troca de vidro",
    "vitrine", "mostruário", "usado", "reembalado",
    "refil", "pulseira para"
]

# Palavras que dão pontos extras (Produtos de desejo)
INTERESTS = [
    ("rtx", 50), ("iphone", 40), ("galaxy s", 30), 
    ("notebook", 30), ("ps5", 40), ("xbox", 30), 
    ("oled", 30), ("qled", 30), ("ar condicionado", 40),
    ("lava e seca", 30), ("geladeira", 20),
    ("air fryer", 20), ("fritadeira", 20)
]

def load_json(path):
    if not path.exists(): return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return []

def calculate_score(item):
    score = 0
    title = str(item.get("title", "")).lower()
    store = str(item.get("store", "")).lower()
    price = item.get("price", 0)

    # 1. Filtro de Loja Permitida (CRÍTICO)
    # Se a loja não estiver na lista permitida, tchau.
    if not any(loja in store for loja in ALLOWED_STORES):
        # Debug: Pode descomentar para ver o que está perdendo
        # print(f"🚫 Loja não afiliada: {store}")
        return -1

    # 2. Filtro de Palavras Banidas
    for bad_word in BLOCKLIST:
        if bad_word in title:
            return -1

    # 3. Pontuação Base
    score = 50 # Começa com 50 se passou nos filtros

    # 4. Bônus por Palavras-Chave
    for keyword, points in INTERESTS:
        if keyword in title:
            score += points

    # 5. Bônus por Menor Preço Histórico (Se disponível)
    if item.get("is_lowest_price"):
        score += 30
    
    # 6. Penalidade para preços muito baixos (provável erro ou acessório não filtrado)
    if price < 10: 
        score -= 20
    
    return score

def rank_offers():
    print("⚖️  Iniciando Ranking (Filtro de Afiliação Ativo)...")
    items = load_json(INBOX_FILE)
    
    ranked_items = []
    rejected_store = 0
    rejected_block = 0

    for item in items:
        # Verifica loja antes de tudo para estatística
        store_lower = str(item.get("store", "")).lower()
        if not any(loja in store_lower for loja in ALLOWED_STORES):
            rejected_store += 1
            continue

        score = calculate_score(item)
        
        if score < 0:
            rejected_block += 1
            continue 
            
        item["score"] = score
        
        # Tags Visuais
        tags = []
        if item.get("is_lowest_price"): tags.append("🔥 Menor Preço")
        if score >= 80: tags.append("💎 Top")
        item["tags"] = tags
        
        ranked_items.append(item)

    # Ordena
    ranked_items.sort(key=lambda x: (x["score"], -x["price"]), reverse=True)

    # Salva
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(ranked_items, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"📊 Total Entrada: {len(items)}")
    print(f"🚫 Rejeitados (Loja não afiliada): {rejected_store}")
    print(f"🗑️ Rejeitados (Blocklist/Lixo): {rejected_block}")
    print(f"✅ Aprovados para Rascunho: {len(ranked_items)}")

if __name__ == "__main__":
    rank_offers()
