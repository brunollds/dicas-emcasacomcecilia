# Changelog

## [2.0.0] - 2026-01-08 - Refatoração do Pipeline de Coleta

### ✨ Adicionado (Novos Coletores)
- **Playwright Engine:** Substituída a coleta baseada em HTTP/Next.js por navegação real (Headless/Headful Browser) para contornar bloqueios de Cloudflare e renderização dinâmica.
- **Pelando Collector (`pelando_playwright.py`):**
  - Implementado "Smart Scroll" para carregar ofertas via AJAX.
  - Lógica de "Melhor Link Vence" para capturar títulos corretos e ignorar thumbnails.
- **Promobit Collector (`promobit_playwright.py`):**
  - Coleta via DOM (Visual) para garantir paridade com o que o usuário vê.
  - Limpeza automática de títulos (remove nome da loja e badges).
  - Reconstrução de URLs relativas.
- **Gatry Collector (`gatry_playwright.py`):**
  - Implementado clique físico via JavaScript no botão "Carregar mais" (bypass de proteção).
  - Estratégia de coleta acumulativa (salva o que vê mesmo se travar).

### 🛠️ Melhorias (Processamento de Dados)
- **Unificador Universal V4 (`unify.py`):**
  - Normalização agnóstica de chaves (`url` vs `link`, `title` vs `offerTitle`).
  - Geração de IDs globais únicos (ex: `gatry-12345`).
  - Correção de URLs incompletas do Promobit.
- **Histórico de Preços V2 (`price_history.py`):**
  - Migração de chave baseada em slug para chave baseada em ID único.
  - Cálculo de estatísticas: Menor preço histórico, Média e Máxima.
- **Ranking (`rank.py`):**
  - Sistema de pontuação (Score) baseado em palavras-chave e histórico.
  - Blocklist para remover acessórios indesejados (capas, películas).

### 🐛 Correções
- Corrigido bug onde o Gatry retornava 0 itens devido a falha no seletor de clique.
- Corrigido bug onde o Promobit retornava 0 itens devido à falta da chave `url` no JSON original.
