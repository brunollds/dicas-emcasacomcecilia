from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

def generate_social_art(product_image_source, price, title):
    # --- PROTEÇÃO CONTRA IMAGEM VAZIA ---
    if not product_image_source:
        print("⚠️ Nenhuma imagem fornecida para a arte.")
        return None
    
    output_path = "temp_story.png"
    template_path = "assets/template_story.png"
    
    # Cria base roxa se não tiver template
    if os.path.exists(template_path):
        base = Image.open(template_path).convert("RGBA")
    else:
        base = Image.new('RGBA', (1080, 1920), (75, 0, 130, 255))

    # Carrega Imagem do Produto
    product_img = None
    try:
        if product_image_source.startswith("local:"):
            local_path = product_image_source.split("local:")[1]
            if os.path.exists(local_path):
                product_img = Image.open(local_path).convert("RGBA")
                # Opcional: deletar o print depois de usar
                # try: os.remove(local_path)
                # except: pass
        elif product_image_source.startswith("http"):
            response = requests.get(product_image_source, timeout=10)
            product_img = Image.open(BytesIO(response.content)).convert("RGBA")
        
        if product_img:
            # Redimensiona
            product_img.thumbnail((800, 800))
            # Centraliza
            bg_w, bg_h = base.size
            img_w, img_h = product_img.size
            offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2 - 100)
            base.paste(product_img, offset, product_img)
    except Exception as e:
        print(f"❌ Erro ao processar imagem da arte: {e}")
        return None

    # Adiciona Preço
    draw = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("arial.ttf", 100)
    except:
        font = ImageFont.load_default()

    text = f"R$ {price:.2f}"
    # Ajuste a posição conforme seu template
    draw.text((100, 1400), text, font=font, fill="white")
    
    base.save(output_path)
    return output_path