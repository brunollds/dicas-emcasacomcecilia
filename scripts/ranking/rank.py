import json
from pathlib import Path
from datetime import datetime, timezone

INBOX_FILE = Path("data/inbox/unified.json")
OUT_FILE = Path("data/inbox/ranked.json")

# ======================================================
# Configuração de Pesos e Filtros
# ======================================================

# Palavras que, se estiverem no título, BANEM a oferta
BLOCKLIST = [
    "capinha", "capa para", "película", "pelicula", 
    "cabo usb", "adaptador", "suporte para", 
    "aluguel", "assinatura", "curso", "ebook", 
    "conserto", "manutenção", "troca de vidro",
    "vitrine", "mostruário", "usado", "reembalado",
    "refil", "pulseira para"
]

# Palavras que dão pontos extras (Interesse)
INTERESTS = [
    ("rtx", 50), ("iphone", 40), ("galaxy s", 30), 
    ("notebook", 30), ("ps5", 40), ("xbox", 30), 
    ("oled", 30), ("qled", 30), ("ar condicionado", 40),
    ("lava e seca", 30), ("geladeira", 20)
]

# Lojas confiáveis (Pontos extras)
TRUSTED_STORES = [
    "amazon", "mercadolivre", "mercado livre", "magalu", 
    "magazine luiza", "kabum", "terabyte", "pichau", "fast shop"
]

def load_json(path):
    if not path.exists(): return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return []

def calculate_score(item):
    score = 0
    title = item.get("title", "").lower()
    store = item.get("store", "").lower()
    price = item.get("price", 0)

    # 1. Filtro de Bloqueio (Retorna -1 para descartar)
    for bad_word in BLOCKLIST:
        if bad_word in title:
            return -1

    # 2. Pontos por Interesse
    for keyword, points in INTERESTS:
        if keyword in title:
            score += points

    # 3. Pontos por Loja Confiável
    if any(s in store for s in TRUSTED_STORES):
        score += 10

    # 4. Pontos por Histórico (Se disponível)
    # Se for o menor preço da história, ganha MUITOS pontos
    if item.get("is_lowest_price"):
        score += 50
    
    # Se o preço atual for menor que a média histórica
    avg = item.get("history_avg")
    if avg and price < avg:
        discount = ((avg - price) / avg) * 100 # % de desconto real
        score += int(discount) # +1 ponto por % de desconto

    # 5. Penalidade para preços muito baixos (provável erro ou acessório)
    if price < 10: 
        score -= 20
    
    # 6. Penalidade para Marketplace desconhecido ou sem loja
    if not store or store == "desconhecida":
        score -= 10

    return score

def rank_offers():
    print("⚖️  Iniciando Ranking e Filtragem...")
    items = load_json(INBOX_FILE)
    
    ranked_items = []
    rejected = 0

    for item in items:
        score = calculate_score(item)
        
        if score < 0:
            rejected += 1
            continue # Item banido
            
        # Adiciona score ao objeto para debug
        item["score"] = score
        
        # Define etiquetas (Tags)
        tags = []
        if item.get("is_lowest_price"): tags.append("🔥 Menor Preço")
        if score > 80: tags.append("💎 Top Oferta")
        if "frete grátis" in str(item).lower(): tags.append("🚚 Frete Grátis")
        
        item["tags"] = tags
        ranked_items.append(item)

    # Ordena: Maior Score -> Menor Preço
    ranked_items.sort(key=lambda x: (x["score"], -x["price"]), reverse=True)

    # Salva
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(ranked_items, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"📊 Processados: {len(items)}")
    print(f"🚫 Rejeitados (Blocklist): {rejected}")
    print(f"✅ Aprovados: {len(ranked_items)}")
    print(f"🏆 Top 3 Ofertas:")
    for i, item in enumerate(ranked_items[:3]):
        print(f"   {i+1}. [{item['score']}pts] {item['title']} (R$ {item['price']})")

if __name__ == "__main__":
    rank_offers()
