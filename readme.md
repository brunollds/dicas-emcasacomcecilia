# 📦 Projeto Dicas

Pipeline editorial para **coleta, curadoria e publicação de promoções**, com decisão final **humana** e foco em **preço real**, não apenas na fonte.

--

## 🎯 Objetivo

Criar um sistema confiável para:

- Coletar promoções automaticamente de múltiplos sites
- Normalizar e deduplicar dados
- Avaliar se o preço realmente é uma boa oferta
- Permitir curadoria humana antes da publicação
- Publicar no site e apoiar postagem manual no WhatsApp

> 🔑 **Princípio central:** nenhuma promoção é publicada automaticamente sem validação humana, por causa de links afiliados e critérios editoriais.

---

## 🧠 Filosofia Editorial

- **Fonte não importa** (Pelando, Gatry, Promobit, etc.)
- **Loja não tem peso diferenciado**
- **Preço é o fator principal**
- Histórico local é mais importante que preço “de tabela”
- Link afiliado **sempre manual**
- Publicação é uma decisão editorial, não algorítmica

---

## 🏗️ Arquitetura Geral

O projeto é dividido em 4 camadas:

1. **Ingestão** – coleta de dados
2. **Processamento editorial** – normalização, ranking, histórico
3. **Curadoria humana** – CLI + Admin HTML
4. **Publicação** – site estático

---

## 1️⃣ Ingestão de Dados

📁 `scripts/collectors/`

- Implementado em **Python + Playwright**
- Usa DOM real (não APIs públicas)
- Compatível com sites com JS pesado

### Fontes integradas

- Pelando
- Gatry
- Promobit
- Gafanho

📦 Saída:
```
data/raw/*.json
```

---

## 2️⃣ Normalização e Deduplicação

📁 `scripts/normalizers/`

Responsável por:

- Padronizar campos
- Unificar todas as fontes
- Eliminar duplicatas entre sites

### Campos normalizados

- `id`
- `title`
- `price`
- `price_text`
- `store`
- `url`

📦 Saída:
```
data/inbox/unified.json
```

---

## 3️⃣ Histórico de Preços

📁 `scripts/history/price_history.py`

Função:

- Criar histórico **local** de preços
- Registrar recorrência
- Calcular mínimo e média

📦 Dados:
```
data/history/prices.json
```

> Não depende de Google Shopping, Edge ou APIs externas.

---

## 4️⃣ Ranking Editorial

📁 `scripts/ranking/rank.py`

Características:

- Fonte e loja não alteram score
- Score baseado em:
  - Preço
  - Recorrência
  - Histórico local
  - Categoria (leve)

📦 Saída:
```
data/inbox/ranked.json
```

---

## 5️⃣ Limiar Editorial (Gate)

📁 `scripts/editorial/apply_threshold.py`

Separa automaticamente:

- **Rascunhos** → vão para avaliação humana
- **Rejeitados** → descartados

📦 Saídas:
```
data/inbox/rascunhos.json
data/inbox/rejeitados.json
```

⏱️ Política opcional:
- Rascunhos expiram após 24h para evitar acúmulo

---

## 6️⃣ CLI Editorial

📁 `scripts/editorial/cli.py`

Funções:

- Listar promoções ranqueadas
- Aprovar ou descartar
- Preparar itens para publicação

> ⚠️ CLI **não publica automaticamente**.

---

## 7️⃣ Admin HTML (Curadoria Humana)

📄 `admin.html`

Papel central do projeto.

### Funções

- Visualizar promoções
- Editar título, preço e texto
- Copiar conteúdo para WhatsApp
- Controlar o que já foi publicado

### Regras importantes

- ❌ Não publica sem link
- 🔗 Link afiliado **sempre manual**
- 🧭 Rascunho deve abrir a página do produto

Tecnologia:
- HTML + CSS + JS puro
- Sem frameworks
- Executado via:
```bash
python -m http.server
```

---

## 8️⃣ Publicação

📁 `public/`

### Arquivo central
```
public/data/products.json
```

- Fonte única do site público
- Atualizado pelo admin

### CI/CD

📁 `.github/workflows/`

- Publicação automática do site
- Atualizações de preço

---

## 🧰 Tecnologias Utilizadas

### Backend
- Python 3.13
- Playwright
- JSON como datastore

### Frontend
- HTML estático
- CSS puro
- JavaScript vanilla

### Infra
- GitHub Actions
- Site estático

---

## 🚧 Limitações Conhecidas

- WhatsApp não permite automação direta
- Admin HTML é legado e sensível a mudanças
- UI não é reativa (decisão consciente)

---

## 📍 Próximos Passos Seguros

- Integrar rascunhos no admin **sem quebrar tabs existentes**
- Criar adaptador JS isolado para rascunhos
- Automatizar Telegram (opcional)

---

## ✍️ Nota Final

Este projeto **não é um bot de spam**.

É uma **ferramenta editorial**, onde automação serve para **reduzir esforço**, não para substituir decisão humana.

---

📌 Mantido com foco em controle, clareza e sustentabilidade editorial.


## 🚀 Como Rodar o Pipeline de Coleta (Modo 2.0)

Este projeto utiliza **Python + Playwright** para coletar ofertas. É necessário instalar as dependências antes.

### Pré-requisitos
```bash
pip install playwright
playwright install chromium

