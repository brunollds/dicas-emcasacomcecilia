"""
Teste rápido da API do Mercado Livre
Execute: python teste_ml.py
"""

from ml_api import processar_url_ml, extrair_id_produto, buscar_produto

print("=" * 60)
print("🧪 TESTE DA API DO MERCADO LIVRE")
print("=" * 60)

# URLs de teste (produtos Damie)
urls_teste = [
    "https://www.mercadolivre.com.br/poltrona-reclinavel-manual-massagem-aquecimento-damie-cinema/p/MLB37776701",
    "https://mercadolivre.com/sec/2zB1urD",  # short link
]

for url in urls_teste:
    print(f"\n📍 Testando: {url[:50]}...")
    print("-" * 50)
    
    # Extrair ID
    item_id = extrair_id_produto(url)
    print(f"   ID extraído: {item_id}")
    
    if item_id:
        dados = buscar_produto(item_id)
        
        if 'erro' not in dados:
            print(f"   ✅ Título: {dados['titulo'][:40]}...")
            print(f"   💰 Preço: R$ {dados['preco']}")
            print(f"   🖼️ Imagem: {dados['imagem'][:50]}...")
            print(f"   🚚 Frete grátis: {'Sim' if dados['frete_gratis'] else 'Não'}")
        else:
            print(f"   ❌ Erro: {dados['erro']}")
    else:
        print("   ❌ Não consegui extrair o ID")

print("\n" + "=" * 60)
print("✅ Teste concluído!")
print("=" * 60)
