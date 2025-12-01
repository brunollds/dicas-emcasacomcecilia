import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
from datetime import datetime
from pathlib import Path
import argparse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("price_scraper.log"),
        logging.StreamHandler()
    ]
)

# Headers para simular um navegador e evitar bloqueios
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

# Configurações específicas para diferentes lojas
STORE_CONFIGS = {
    "Amazon": {
        "price_selectors": [
            "span.a-price-whole", 
            "span.a-offscreen",
            "span#priceblock_ourprice"
        ],
        "delay": (2, 5)  # Intervalo de delay em segundos (min, max)
    },
    "Mercado Livre": {
        "price_selectors": [
            "span.andes-money-amount__fraction",
            "span.price-tag-fraction"
        ],
        "decimal_selectors": [
            "span.andes-money-amount__cents",
            "span.price-tag-cents"
        ],
        "delay": (1, 3)
    },
    "Shopee": {
        "price_selectors": [
            "div.pqTWkA",
            "div._3n5NQx"
        ],
        "delay": (2, 4)
    },
    # Adicione mais configurações para outras lojas conforme necessário
    "default": {
        "price_selectors": ["span.price", "div.price", "p.price", ".product-price"],
        "delay": (1, 3)
    }
}

def get_random_user_agent():
    """Retorna um User-Agent aleatório"""
    return random.choice(USER_AGENTS)

def extract_price(html_content, store_name):
    """Extrai o preço do HTML baseado nas configurações da loja"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Obter configuração da loja ou usar configuração padrão
    store_config = STORE_CONFIGS.get(store_name, STORE_CONFIGS["default"])
    
    # Tentativa de extrair o preço usando os seletores configurados
    price_text = None
    decimal_text = "00"  # valor padrão para centavos
    
    # Tentar cada seletor até encontrar um preço
    for selector in store_config["price_selectors"]:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.text.strip()
            break
    
    # Se houver seletores específicos para decimais, tentar extraí-los
    if "decimal_selectors" in store_config and price_text:
        for selector in store_config["decimal_selectors"]:
            decimal_element = soup.select_one(selector)
            if decimal_element:
                decimal_text = decimal_element.text.strip()
                break
    
    # Se não encontrou preço por seletores específicos, tentar regex genérico
    if not price_text:
        price_pattern = r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)'
        matches = re.findall(price_pattern, html_content)
        if matches:
            price_text = matches[0]
    
    # Processar texto do preço encontrado
    if price_text:
        # Remover caracteres não numéricos
        price_text = re.sub(r'[^\d,.]', '', price_text)
        
        # Se temos um formato com vírgula (brasileiro), converter para ponto
        if ',' in price_text and '.' not in price_text:
            price_text = price_text.replace(',', '.')
        elif '.' in price_text and ',' in price_text:  # formato R$ 1.999,99
            price_text = price_text.replace('.', '').replace(',', '.')
        
        # Se temos apenas a parte inteira e uma parte decimal separada
        if ',' not in price_text and '.' not in price_text and decimal_text != "00":
            price_text = f"{price_text}.{decimal_text}"
            
        try:
            return float(price_text)
        except ValueError:
            logging.error(f"Não foi possível converter o preço '{price_text}' para float")
    
    return None

def scrape_price(url, store_name):
    """Acessa a URL e extrai o preço"""
    if not url.startswith(('http://', 'https://')):
        logging.warning(f"URL inválida: {url}")
        return None
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        # Adicionar delay para evitar bloqueios
        store_config = STORE_CONFIGS.get(store_name, STORE_CONFIGS["default"])
        delay = random.uniform(*store_config["delay"])
        time.sleep(delay)
        
        logging.info(f"Acessando {store_name}: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            price = extract_price(response.text, store_name)
            if price:
                logging.info(f"Preço extraído de {store_name}: R$ {price:.2f}")
                return price
            else:
                logging.warning(f"Não foi possível extrair o preço de {store_name} (URL: {url})")
        else:
            logging.error(f"Erro ao acessar {url}: Status code {response.status_code}")
    
    except requests.RequestException as e:
        logging.error(f"Erro na requisição para {url}: {e}")
    except Exception as e:
        logging.error(f"Erro desconhecido ao acessar {url}: {e}")
    
    return None

def load_products(json_file):
    """Carrega os produtos do arquivo JSON"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar JSON do arquivo {json_file}")
        return []
    except Exception as e:
        logging.error(f"Erro ao carregar o arquivo {json_file}: {e}")
        return []

def save_products(products, json_file, backup=True):
    """Salva os produtos no arquivo JSON com opção de backup"""
    if backup:
        # Criar backup antes de salvar
        backup_path = Path(f"{json_file}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        try:
            with open(json_file, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            logging.info(f"Backup criado em {backup_path}")
        except Exception as e:
            logging.warning(f"Não foi possível criar backup: {e}")
    
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        logging.info(f"Arquivo {json_file} atualizado com sucesso")
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo {json_file}: {e}")
        return False

def update_products_prices(products, dry_run=False):
    """Atualiza os preços dos produtos"""
    for i, product in enumerate(products):
        logging.info(f"Processando produto ({i+1}/{len(products)}): {product.get('name', 'Sem nome')}")
        
        # Verificar se o produto tem informações de preços
        if not product.get('prices'):
            logging.warning(f"Produto {product.get('name', 'Sem nome')} não tem informações de preço")
            continue
        
        updated = False
        old_prices = {}
        
        # Para cada loja, tentar atualizar o preço
        for store_name, store_info in product['prices'].items():
            if not store_info.get('link'):
                logging.warning(f"Link não encontrado para a loja {store_name}")
                continue
            
            # Guardar preço atual para comparação
            old_prices[store_name] = store_info.get('price')
            
            # Se não estamos em modo de simulação, fazer o scraping
            if not dry_run:
                new_price = scrape_price(store_info['link'], store_name)
                
                # Atualizar o preço se encontrado
                if new_price is not None:
                    store_info['price'] = new_price
                    product['date'] = datetime.now().strftime('%Y-%m-%d')
                    updated = True
                    
                    # Registrar alteração de preço
                    old_price = old_prices[store_name]
                    if old_price:
                        diff = new_price - old_price
                        diff_percent = (diff / old_price) * 100 if old_price else 0
                        logging.info(f"Preço alterado em {store_name}: R$ {old_price:.2f} -> R$ {new_price:.2f} ({diff_percent:+.2f}%)")
        
        if updated:
            # Calcular menor preço para atualizar no atributo data-lowest-price
            lowest_price = float('inf')
            for store_info in product['prices'].values():
                price = store_info.get('price', 0)
                if price and price < lowest_price:
                    lowest_price = price
            
            # Adicionar uma flag para indicar que o preço foi atualizado
            product['price_updated'] = True
            
            logging.info(f"Produto {product.get('name', 'Sem nome')} atualizado com sucesso")
    
    return products

def main():
    parser = argparse.ArgumentParser(description='Atualiza preços de produtos em arquivo JSON')
    parser.add_argument('--input', '-i', default='data/products.json', help='Arquivo JSON de entrada')
    parser.add_argument('--output', '-o', help='Arquivo JSON de saída (padrão: mesmo que entrada)')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Executa sem fazer alterações reais')
    parser.add_argument('--no-backup', '-n', action='store_true', help='Não cria arquivo de backup')
    
    args = parser.parse_args()
    
    input_file = args.input
    output_file = args.output or input_file
    dry_run = args.dry_run
    create_backup = not args.no_backup
    
    if dry_run:
        logging.info("Modo de simulação ativado, nenhuma alteração será salva")
    
    # Carregar produtos
    logging.info(f"Carregando produtos de {input_file}")
    products = load_products(input_file)
    
    if not products:
        logging.error("Nenhum produto encontrado ou erro ao carregar o arquivo")
        return
    
    logging.info(f"Encontrados {len(products)} produtos para processamento")
    
    # Atualizar preços
    updated_products = update_products_prices(products, dry_run)
    
    # Salvar alterações, se não estiver em modo de simulação
    if not dry_run:
        if save_products(updated_products, output_file, create_backup):
            logging.info(f"Todos os produtos foram processados e salvos em {output_file}")
        else:
            logging.error("Erro ao salvar as alterações")
    else:
        logging.info("Simulação concluída, nenhuma alteração foi salva")

if __name__ == "__main__":
    main()