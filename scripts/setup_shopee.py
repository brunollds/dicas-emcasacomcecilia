import asyncio
from playwright.async_api import async_playwright

async def setup_session():
    print("🚀 Abrindo navegador para configuração...")
    print("👉 Faça LOGIN na sua conta secundária.")
    print("👉 Navegue até qualquer produto para garantir que está carregando.")
    print("👉 Quando terminar e o produto estiver visível, FECHE a janela do navegador manualmente.")
    
    async with async_playwright() as p:
        # Cria uma pasta 'shopee_session' para salvar os cookies
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./shopee_session", 
            headless=False, # Abre visível para você mexer
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page = await browser.new_page()
        await page.goto("https://shopee.com.br/buyer/login")
        
        # O script vai ficar rodando até você fechar o navegador
        print("⏳ Aguardando você fechar o navegador...")
        try:
            await page.wait_for_event("close", timeout=0) 
        except:
            pass
            
    print("✅ Sessão salva na pasta './shopee_session'!")

if __name__ == "__main__":
    asyncio.run(setup_session())