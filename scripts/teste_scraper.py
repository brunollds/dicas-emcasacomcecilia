"""
Teste rápido do ML Scraper
"""

from ml_scraper import buscar_produto_ml, processar_url_ml

print("=" * 60)
print("🧪 TESTE DO SCRAPER DO MERCADO LIVRE")
print("=" * 60)

# Teste 1: URL completa
print("\n📍 Teste 1: URL completa")
print("-" * 50)
url = "https://www.mercadolivre.com.br/poltrona-reclinavel-manual-massagem-aquecimento-damie-cinema/p/MLB37776701"
resultado = processar_url_ml(url)

if resultado and resultado.get('preco'):
    print("\n✅ Scraper funcionando!")
else:
    print("\n❌ Falha no teste")

# Teste 2: Só o ID
print("\n📍 Teste 2: Só o ID")
print("-" * 50)
resultado2 = processar_url_ml("MLB37776701")

if resultado2 and resultado2.get('preco'):
    print("\n✅ Busca por ID funcionando!")
else:
    print("\n⚠️ Busca por ID não funcionou (normal em alguns casos)")

print("\n" + "=" * 60)
