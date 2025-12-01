import os
import json
import requests
import hashlib
from urllib.parse import urlparse, unquote
import re
import time

# --- Configuração ---
# Caminho para o arquivo JSON de entrada
input_json_path = 'products.json'
# Caminho para o arquivo JSON de saída (com caminhos atualizados)
output_json_path = 'products_updated.json'
# Diretório onde as imagens serão salvas (relativo ao local do script)
output_image_dir = os.path.join('images', 'products')
# Cabeçalho User-Agent para simular um navegador
request_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# Tempo de espera entre os downloads (em segundos) para evitar sobrecarregar o servidor
delay_between_requests = 0.5 # Meio segundo

# --- Funções Auxiliares ---

def generate_unique_filename(url):
    """
    Gera um nome de arquivo único baseado no hash MD5 da URL,
    preservando a extensão original do arquivo.
    """
    try:
        parsed_url = urlparse(url)
        # Decodifica caracteres especiais no caminho (ex: %20 -> espaço)
        path = unquote(parsed_url.path)
        # Extrai o nome do arquivo base do caminho
        base_filename = os.path.basename(path)
        # Remove parâmetros de query (ex: ?v=123) que podem estar no nome base
        base_filename = re.sub(r'\?.*$', '', base_filename)
        # Pega a extensão (incluindo o ponto, ex: .jpg, .png, .webp)
        _, extension = os.path.splitext(base_filename)

        # Se não houver extensão ou for muito curta, tenta adivinhar pelo Content-Type (se disponível)
        # (Implementação mais avançada poderia verificar o header Content-Type da resposta)
        # Fallback para .jpg se ainda assim não encontrar extensão
        if not extension or len(extension) < 3:
            extension = '.jpg' # Fallback padrão

        # Garante que a extensão esteja em minúsculas
        extension = extension.lower()

        # Gera um hash MD5 da URL completa para garantir unicidade
        unique_hash = hashlib.md5(url.encode('utf-8')).hexdigest()

        # Retorna o nome combinando hash e extensão
        return f"{unique_hash}{extension}"
    except Exception as e:
        print(f"  [AVISO] Erro ao gerar nome para URL '{url}': {e}. Usando fallback.")
        # Fallback muito simples em caso de erro inesperado no parsing
        unique_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return f"{unique_hash}.jpg"

def download_image(url, output_path):
    """
    Baixa uma imagem da URL fornecida e salva no caminho especificado.
    Retorna True se o download for bem-sucedido, False caso contrário.
    """
    try:
        # Faz a requisição GET com headers e timeout
        response = requests.get(url, headers=request_headers, timeout=20, stream=True)
        # Verifica se a requisição foi bem-sucedida (status code 2xx)
        response.raise_for_status()

        # Verifica o tipo de conteúdo (opcional, mas recomendado)
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            print(f"  [AVISO] URL não parece ser uma imagem ({content_type}): {url}")
            # Você pode decidir pular ou tentar salvar mesmo assim
            # return False # Descomente para pular se não for imagem

        # Salva o conteúdo da imagem no arquivo
        with open(output_path, 'wb') as img_file:
            for chunk in response.iter_content(chunk_size=8192):
                 if chunk: # Filtra chunks de keep-alive
                    img_file.write(chunk)
        # print(f"  [OK] Imagem salva: {os.path.basename(output_path)}")
        return True
    # Trata erros específicos de requisição
    except requests.exceptions.RequestException as e:
        print(f"  [ERRO] Falha ao baixar {url}: {e}")
        return False
    # Trata outros erros (ex: escrita de arquivo)
    except Exception as e:
        print(f"  [ERRO] Erro inesperado ao processar {url}: {e}")
        return False

# --- Lógica Principal ---

# Garante que o diretório de saída exista
os.makedirs(output_image_dir, exist_ok=True)
print(f"Diretório de imagens: {os.path.abspath(output_image_dir)}")

# Verifica se o arquivo JSON de entrada existe
if not os.path.exists(input_json_path):
    print(f"[FALHA] Arquivo de entrada '{input_json_path}' não encontrado.")
    exit() # Encerra o script se o JSON não existir

print(f"Carregando produtos de: {input_json_path}")
# Carrega o arquivo JSON com os produtos
try:
    with open(input_json_path, 'r', encoding='utf-8') as file:
        products_data = json.load(file)
except json.JSONDecodeError as e:
    print(f"[FALHA] Erro ao decodificar JSON em '{input_json_path}': {e}")
    exit()
except Exception as e:
    print(f"[FALHA] Erro ao ler arquivo '{input_json_path}': {e}")
    exit()

# Verifica se products_data é uma lista
if not isinstance(products_data, list):
    print(f"[FALHA] O conteúdo de '{input_json_path}' não é uma lista JSON.")
    exit()

print(f"Encontrados {len(products_data)} produtos. Iniciando download das imagens...")
updated_products = []
download_count = 0
error_count = 0

# Loop para baixar e salvar as imagens
# Iterar diretamente sobre a lista de produtos
for i, product in enumerate(products_data):
    # Verifica se o item atual é um dicionário (estrutura esperada do produto)
    if not isinstance(product, dict):
        print(f"[AVISO] Item {i+1} não é um dicionário, pulando.")
        updated_products.append(product) # Mantém o item original se não for um produto válido
        continue

    product_name = product.get("name", f"Produto {i+1}")
    image_url = product.get("image")
    print(f"\nProcessando {product_name}...")

    # Verifica se existe URL da imagem e se começa com http/https
    if image_url and isinstance(image_url, str) and image_url.strip().startswith(("http://", "https://")):
        image_url = image_url.strip() # Remove espaços em branco extras
        print(f"  URL: {image_url}")
        # Gera o nome do arquivo local
        local_filename = generate_unique_filename(image_url)
        # Monta o caminho completo para salvar a imagem
        local_image_path_full = os.path.join(output_image_dir, local_filename)
        # Define o caminho relativo para salvar no JSON (formato web)
        relative_image_path = f"/images/products/{local_filename}" # Caminho absoluto a partir da raiz do site

        # Tenta baixar a imagem
        if download_image(image_url, local_image_path_full):
            # Atualiza o caminho da imagem no dicionário do produto
            product['image'] = relative_image_path
            print(f"  [OK] Imagem salva como {local_filename}. Caminho atualizado para: {relative_image_path}")
            download_count += 1
        else:
            # Mantém a URL original no JSON em caso de erro no download
            print(f"  [FALHA] Download falhou. Mantendo URL original.")
            product['image'] = image_url # Garante que o campo 'image' ainda exista com a URL original
            error_count += 1

        # Pausa entre as requisições
        time.sleep(delay_between_requests)

    else:
        print(f"  [INFO] URL da imagem ausente, inválida ou já é local. Pulando download.")
        # Garante que o campo 'image' exista, mesmo que vazio ou inválido
        if 'image' not in product:
             product['image'] = None # Ou "" dependendo da sua preferência

    # Adiciona o produto (original ou modificado) à nova lista
    updated_products.append(product)

print("\n--- Resumo ---")
print(f"Produtos processados: {len(products_data)}")
print(f"Imagens baixadas com sucesso: {download_count}")
print(f"Erros de download: {error_count}")

# Salva a lista de produtos atualizada no novo arquivo JSON
try:
    with open(output_json_path, 'w', encoding='utf-8') as out_file:
        # Salva o JSON formatado (indent=4) e garantindo caracteres non-ASCII
        json.dump(updated_products, out_file, indent=4, ensure_ascii=False)
    print(f"\n✔️ Script finalizado. JSON atualizado salvo em: {output_json_path}")
except Exception as e:
    print(f"\n[FALHA] Erro ao salvar o JSON atualizado em '{output_json_path}': {e}")

