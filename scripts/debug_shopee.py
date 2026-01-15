import os
import time
import json
import hashlib
import requests
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

APP_ID = os.getenv("SHOPEE_APP_ID")
SECRET = os.getenv("SHOPEE_SECRET")

print("="*50)
print(f"🔑 Verificando Credenciais:")
print(f"   APP_ID: {APP_ID}")
print(f"   SECRET: {SECRET[:5]}... (Oculto)" if SECRET else "   SECRET: ❌ NÃO ENCONTRADO")
print("="*50)

if not APP_ID or not SECRET:
    print("❌ ERRO: Suas credenciais não estão no arquivo .env!")
    exit()

def debug_link():
    url_api = "https://open-api.affiliate.shopee.com.br/graphql"
    original_url = "https://shopee.com.br/product/344463945/23296168214"
    timestamp = int(time.time())

    # Payload exato
    query = f'''mutation {{
        generateShortLink(originUrl: "{original_url}", subIds: ["teste_debug"]) {{
            shortLink
        }}
    }}'''

    payload_dict = {"query": query}
    payload_str = json.dumps(payload_dict) # Importante: Assinar a string exata

    # Assinatura
    base_string = f"{APP_ID}{timestamp}{payload_str}{SECRET}"
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID}, Timestamp={timestamp}, Signature={signature}"
    }

    print(f"\n🚀 Enviando requisição para Shopee ({url_api})...")
    
    try:
        r = requests.post(url_api, headers=headers, data=payload_str, timeout=10)
        
        print(f"\n📥 Status Code: {r.status_code}")
        print(f"📜 Resposta Completa:\n{r.text}")
        
        if "shortLink" in r.text:
            print("\n✅ SUCESSO! A API gerou o link. O problema era no código do bot.")
        else:
            print("\n❌ FALHA! A API recusou. Leia a mensagem de erro acima ('message').")
            if "signature" in r.text.lower():
                print("💡 Dica: Verifique se o SHOPEE_SECRET está correto (sem espaços extras).")
            if "app" in r.text.lower() and "id" in r.text.lower():
                print("💡 Dica: Verifique se o SHOPEE_APP_ID é apenas números.")

    except Exception as e:
        print(f"❌ Erro de Conexão: {e}")

if __name__ == "__main__":
    debug_link()