import os
import logging
import sys
import re
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.extractor import extract_metadata
from scripts.utils.converter import convert_link
from scripts.utils.image_generator import generate_social_art

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Divulgador Caseiro**\nMande um link para gerar o post.",
        parse_mode='Markdown'
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    url_match = re.search(r'(https?://[^\s]+)', user_text)
    if not url_match: return
    
    raw_url = url_match.group(1)
    status = await update.message.reply_text("🔎 **Analisando...**", parse_mode='Markdown')
    
    try:
        data = await extract_metadata(raw_url)
        
        if not data:
            await status.edit_text("❌ Erro ao ler produto.")
            return
        
        affiliate_link = convert_link(data['original_url'], data['store'])
        
        # --- LÓGICA DE PREÇOS E DESCONTO ---
        price = data['price']
        original = data.get('original_price', 0)
        
        price_line = f"💲 <b>R$ {price:.2f}</b>"
        
        if original > price:
            # Calcula porcentagem de desconto
            discount = int(((original - price) / original) * 100)
            price_line += f" ~De R$ {original:.2f}~ (-{discount}%)"
        
        # --- GERAÇÃO DA ARTE ---
        await status.edit_text("🎨 **Criando arte...**", parse_mode='Markdown')
        # Tenta gerar a arte. Se falhar (imagem None), retorna None.
        img_path = generate_social_art(data['image'], price, data['title'])
        
        # --- COPY NO SEU PADRÃO ---
        caption = f"""
🛒 <b>{data['title']}</b>

{price_line}
📦 Frete grátis (verifique regras)

👉 <a href="{affiliate_link}"><b>CLIQUE AQUI PARA COMPRAR</b></a>
        """.strip()
        
        # --- ENVIO ---
        if img_path and os.path.exists(img_path):
            await update.message.reply_photo(
                photo=open(img_path, 'rb'),
                caption=caption,
                parse_mode='HTML'
            )
            try: os.remove(img_path)
            except: pass
        else:
            # Se não tiver arte, manda só o texto
            await update.message.reply_text(caption, parse_mode='HTML', disable_web_page_preview=False)
        
        await status.delete()
        
    except Exception as e:
        logging.error(f"Erro: {e}")
        await status.edit_text(f"❌ Erro: {str(e)}")

if __name__ == '__main__':
    if not TOKEN: exit(1)
    print("🤖 Bot Iniciado!")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Entity("url"), handle_link))
    app.run_polling()