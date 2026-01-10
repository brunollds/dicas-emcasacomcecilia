# 📦 Projeto Dicas (Modo 2.0)

Pipeline de Engenharia de Dados para **coleta, curadoria e publicação de promoções**.
Focado em **preço real**, histórico confiável e decisão final **humana**.

> 🚀 **Versão 2.0:** Migração completa para **Python + Playwright** com estratégias de *Smart Scroll* e *DOM Extraction* para contornar bloqueios modernos.

---

## 🎯 Objetivo
Criar um sistema de "Radar de Ofertas" que:
1.  **Coleta** dados de múltiplas fontes (Pelando, Promobit, Gatry, Gafanho).
2.  **Normaliza** os dados em um formato universal.
3.  **Analisa** o histórico local para detectar descontos reais.
4.  **Entrega** rascunhos prontos para um **Painel Admin**, onde um humano decide o que publicar.

> 🔑 **Princípio Central:** Nenhuma promoção vai pro ar sem aprovação humana (para inserção de link afiliado e validação editorial).

---

## 🏗️ Arquitetura do Pipeline

O fluxo de dados segue o caminho: **Raw -> Inbox -> History -> Ranking -> Admin**.

### 1️⃣ Coleta (Ingestão)
📁 `scripts/collectors/`
Scripts robustos em **Playwright** que simulam navegação real.
- **Estratégia:** "Smart Scroll" (rola a página até atingir meta de itens) + extração via DOM.
- **Fontes:**
  - `pelando_playwright.py`: Aba Recentes (Infinite Scroll).
  - `promobit_playwright.py`: Limpeza de títulos e URLs.
  - `gatry_playwright.py`: Clique físico no botão "Carregar mais" via JS.
  - `gafanho_playwright.py`: Injeção no escopo Angular.
- **Saída:** `data/raw/*.json`

### 2️⃣ Normalização (Unificação V4)
📁 `scripts/normalizers/unify.py`
Transforma dados caóticos em um padrão limpo.
- Resolve conflitos de chaves (`url` vs `link`, `title` vs `name`).
- Gera **IDs Universais** (ex: `gatry-12345`) para evitar duplicatas.
- Reconstrói URLs relativas e corrige preços.
- **Saída:** `data/inbox/unified.json`

### 3️⃣ Inteligência (Histórico e Ranking)
📁 `scripts/history/price_history.py`
- Mantém um banco de dados local (`prices.json`) com a evolução de preço de cada ID.
- Calcula: Mínimo Histórico, Média e Máxima.

📁 `scripts/ranking/rank.py`
- Aplica pontuação (Score 0-100) baseada em:
  - Palavras-chave (ex: "RTX", "iPhone" ganham pontos).
  - Menor preço histórico (Super bônus).
  - Blocklist (ex: "capinha", "curso" são banidos).
- **Saída:** `data/inbox/ranked.json`

### 4️⃣ Curadoria (Admin)
📁 `admin.html` (Frontend) + `data/inbox/rascunhos.json` (Dados)
- O script `apply_threshold.py` gera o arquivo de rascunhos.
- O Admin lê esse arquivo e exibe cards prontos.
- **Ação Humana:** Clicar em "Usar", inserir link afiliado e publicar.

---

## 🚀 Como Rodar

### Pré-requisitos
```bash
pip install playwright
playwright install chromium
