import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Caminho para o arquivo de promoções (ajuste se necessário)
PROMO_FILE = Path("public/data/promocoes.json")
TTL_HOURS = 72

def cleanup_promotions():
    if not PROMO_FILE.exists():
        print("⚠️ Arquivo promocoes.json não encontrado.")
        return

    try:
        # Carregar dados
        content = PROMO_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        
        if "promocoes" not in data:
            print("❌ Formato de JSON inválido.")
            return

        agora = datetime.now(timezone.utc)
        limite = timedelta(hours=TTL_HOURS)
        
        total_antes = len(data["promocoes"])
        mantidos = []

        for promo in data["promocoes"]:
            timestamp = promo.get("timestamp")
            
            if not timestamp:
                mantidos.append(promo)
                continue

            try:
                # Converter timestamp ISO para objeto datetime
                # Lida com formatos 2026-01-14T16:18:40.796Z
                data_promo = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if (agora - data_promo) <= limite:
                    mantidos.append(promo)
            except Exception as e:
                print(f"⚠️ Erro ao processar data da promo {promo.get('id')}: {e}")
                mantidos.append(promo)

        # Salvar se houver mudanças
        if len(mantidos) != total_antes:
            data["promocoes"] = mantidos
            PROMO_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"🧹 Limpeza concluída: {total_antes - len(mantidos)} itens removidos.")
            print(f"✅ Itens restantes: {len(mantidos)}")
        else:
            print("✨ Nada para limpar. Todas as promoções estão dentro do prazo.")

    except Exception as e:
        print(f"❌ Erro crítico: {e}")

if __name__ == "__main__":
    cleanup_promotions()