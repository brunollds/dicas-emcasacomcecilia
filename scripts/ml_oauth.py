"""
Autenticação OAuth2 - Mercado Livre
Em Casa com Cecília

Passo 1: Execute este script
Passo 2: Acesse a URL que aparecer no navegador
Passo 3: Faça login e autorize
Passo 4: Cole a URL de callback aqui
Passo 5: Pronto! Token salvo em ml_tokens.json
"""

import requests
import json
import webbrowser
from urllib.parse import urlparse, parse_qs
import os

# =====================================================
# CREDENCIAIS DO APP
# =====================================================

CLIENT_ID = "5878524513877787"
CLIENT_SECRET = "j9a3u2Q85o5muoSj3Jvx1jpuXJsMldoI"
REDIRECT_URI = "https://dicas.emcasacomcecilia.com/callback"

# Arquivo para salvar tokens
TOKENS_FILE = "ml_tokens.json"

# =====================================================
# URLs da API
# =====================================================

AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
API_BASE = "https://api.mercadolibre.com"

# =====================================================
# FUNÇÕES
# =====================================================

def gerar_url_autorizacao():
    """Gera URL para usuário autorizar o app"""
    url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return url


def extrair_code_da_url(url_callback):
    """Extrai o code da URL de callback"""
    parsed = urlparse(url_callback)
    params = parse_qs(parsed.query)
    return params.get('code', [None])[0]


def obter_tokens(code):
    """Troca o code por access_token e refresh_token"""
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro: {response.status_code}")
        print(response.text)
        return None


def renovar_token(refresh_token):
    """Renova o access_token usando refresh_token"""
    data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token
    }
    
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao renovar: {response.status_code}")
        print(response.text)
        return None


def salvar_tokens(tokens):
    """Salva tokens em arquivo JSON"""
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)
    print(f"✅ Tokens salvos em {TOKENS_FILE}")


def carregar_tokens():
    """Carrega tokens do arquivo"""
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    return None


def get_access_token():
    """Retorna access_token válido, renovando se necessário"""
    tokens = carregar_tokens()
    
    if not tokens:
        print("❌ Nenhum token encontrado. Execute a autenticação primeiro.")
        return None
    
    # Testar se token ainda funciona
    headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
    test = requests.get(f"{API_BASE}/users/me", headers=headers)
    
    if test.status_code == 200:
        return tokens['access_token']
    
    # Token expirou, tentar renovar
    print("🔄 Renovando token...")
    novos_tokens = renovar_token(tokens['refresh_token'])
    
    if novos_tokens:
        salvar_tokens(novos_tokens)
        return novos_tokens['access_token']
    
    print("❌ Não foi possível renovar. Faça login novamente.")
    return None


# =====================================================
# FLUXO PRINCIPAL
# =====================================================

def autenticar():
    """Fluxo completo de autenticação"""
    
    print("=" * 60)
    print("🔐 AUTENTICAÇÃO MERCADO LIVRE - OAuth2")
    print("=" * 60)
    
    # Verificar se já tem token válido
    tokens = carregar_tokens()
    if tokens:
        print("\n📋 Tokens existentes encontrados. Testando...")
        token = get_access_token()
        if token:
            print("✅ Token válido! Não precisa autenticar novamente.")
            return token
        print("⚠️ Token expirado. Vamos renovar...")
    
    # Gerar URL
    url = gerar_url_autorizacao()
    
    print("\n📍 PASSO 1: Abra esta URL no navegador:")
    print("-" * 60)
    print(url)
    print("-" * 60)
    
    # Tentar abrir automaticamente
    try:
        print("\n🌐 Tentando abrir no navegador...")
        webbrowser.open(url)
    except:
        print("(Não foi possível abrir automaticamente)")
    
    print("\n📍 PASSO 2: Faça login com a conta do Mercado Livre")
    print("📍 PASSO 3: Clique em 'Autorizar'")
    print("📍 PASSO 4: Você será redirecionado para uma página")
    print("           (pode dar erro 404, é normal!)")
    print("\n📍 PASSO 5: Copie a URL COMPLETA da barra de endereço")
    print("           Ela vai ser algo como:")
    print("           https://dicas.emcasacomcecilia.com/callback?code=TG-xxx...")
    
    print("\n" + "=" * 60)
    url_callback = input("Cole a URL completa aqui: ").strip()
    
    if not url_callback:
        print("❌ URL vazia. Abortando.")
        return None
    
    # Extrair code
    code = extrair_code_da_url(url_callback)
    
    if not code:
        # Talvez colou só o code
        if url_callback.startswith('TG-'):
            code = url_callback
        else:
            print("❌ Não encontrei o code na URL.")
            print("   Certifique-se de copiar a URL completa.")
            return None
    
    print(f"\n🔑 Code extraído: {code[:20]}...")
    
    # Trocar por tokens
    print("🔄 Trocando code por access_token...")
    tokens = obter_tokens(code)
    
    if tokens:
        salvar_tokens(tokens)
        print("\n✅ AUTENTICAÇÃO CONCLUÍDA!")
        print(f"   Access Token: {tokens['access_token'][:20]}...")
        print(f"   Expira em: {tokens.get('expires_in', 'N/A')} segundos")
        return tokens['access_token']
    else:
        print("\n❌ Falha ao obter tokens.")
        return None


# =====================================================
# TESTE
# =====================================================

if __name__ == "__main__":
    token = autenticar()
    
    if token:
        print("\n" + "=" * 60)
        print("🧪 TESTANDO ACESSO À API...")
        print("=" * 60)
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Testar endpoint público
        response = requests.get(
            f"{API_BASE}/items/MLB37776701",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API funcionando!")
            print(f"   Produto: {data.get('title', 'N/A')[:50]}...")
            print(f"   Preço: R$ {data.get('price', 'N/A')}")
        else:
            print(f"\n⚠️ Status: {response.status_code}")
            print(response.text[:200])
