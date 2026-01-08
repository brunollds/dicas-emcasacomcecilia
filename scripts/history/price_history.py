import json
import statistics
from pathlib import Path
from datetime import datetime, timezone

# ======================================================
# Configuração
# ======================================================
HISTORY_FILE = Path("data/history/prices.json")
INBOX_FILE = Path("data/inbox/unified.json")

def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def load_json(path):
    if not path.exists(): return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return {} # Se corrompido, reseta

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def update_price_history():
    print("⏳ Atualizando histórico de preços...")
    
    # Carrega histórico existente (Chave = ID do produto)
    history = load_json(HISTORY_FILE)
    
    # Carrega itens novos
    if not INBOX_FILE.exists():
        print("❌ Arquivo inbox/unified.json não encontrado.")
        return
        
    items = json.loads(INBOX_FILE.read_text(encoding="utf-8"))
    
    updated_items = []
    stats_added = 0
    
    for item in items:
        pid = item.get("id")
        price = item.get("price")
        
        if not pid or price is None:
            continue
            
        # Garante que temos histórico para este ID
        if pid not in history:
            history[pid] = {
                "title": item.get("title"), # Guarda título para referência
                "prices": []
            }
            
        # Adiciona preço se for novo ou se mudou
        prices_list = history[pid]["prices"]
        
        # Só adiciona se o último preço registrado for diferente
        # ou se a lista estiver vazia (primeira vez)
        if not prices_list or prices_list[-1]["val"] != price:
            prices_list.append({
                "val": float(price),
                "at": now_utc()
            })
            stats_added += 1
            
        # --- ENRIQUECIMENTO ---
        # Calcula estatísticas e injeta no item atual para o Ranking usar
        vals = [p["val"] for p in prices_list]
        item["history_min"] = min(vals)
        item["history_max"] = max(vals)
        item["history_avg"] = statistics.mean(vals)
        item["history_count"] = len(vals)
        
        # Flag: É o menor preço histórico?
        item["is_lowest_price"] = (price <= item["history_min"])
        
        updated_items.append(item)

    # Salva histórico atualizado
    save_json(HISTORY_FILE, history)
    
    # Salva itens enriquecidos de volta no inbox (para o Ranking usar)
    save_json(INBOX_FILE, updated_items)
    
    print(f"📊 Histórico: {len(history)} produtos rastreados.")
    print(f"📈 Atualizações: {stats_added} novos preços registrados.")
    print(f"✅ Arquivo {INBOX_FILE} enriquecido com dados históricos.")

if __name__ == "__main__":
    update_price_history()
