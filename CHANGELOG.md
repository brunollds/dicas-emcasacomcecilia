# Changelog

## Versão 1.1.3 (12/05/2025)

### Mudanças
- Compartilhamento simplificado: agora apenas copiar link e WhatsApp estão disponíveis nos cards de produto
- Cada card de produto gera um link único para compartilhamento
- Agora, ao acessar a URL com ?produto=nome-do-produto, o card correspondente é automaticamente aberto em destaque

## Versão 1.1.2 (11/05/2025)

### Correções
- Corrigido o problema com a seleção de categorias que não estava filtrando os produtos corretamente
- Corrigido o modo de destaque dos produtos que não estava funcionando ao clicar nos cards
- Melhorado o posicionamento do card em destaque, garantindo que apareça sobre o overlay com fundo desfocado
- Corrigido o problema com o botão de fechar no modo de destaque
- Resolvidos problemas de state management para garantir correta comunicação entre os componentes
- Corrigidos erros de referência a variáveis indefinidas

### Melhorias
- Adicionada funcionalidade de clonagem do produto no modo destaque para melhor visualização
- Melhorado o controle de z-index para garantir que elementos apareçam na ordem correta
- Otimizado o código para melhor performance e manutenibilidade
- Adicionada limpeza adequada de recursos ao fechar o modo destaque

## Versão 1.1.1 (05/05/2025)

### Adições
- Adicionado suporte a compartilhamento via Telegram
- Adicionados novos produtos na categoria "Tecnologia"

### Melhorias
- Otimizada a carga inicial de produtos
- Melhorada a experiência de usuário em dispositivos móveis

## Versão 1.1.0 (03/05/2025)

### Adições
- Lançamento inicial do site de Indicações de Produtos
- Sistema de busca e filtragem de produtos
- Organização por categorias
- Cards de produtos com preços comparativos
- Links de afiliados para compra
- Modo de destaque para visualização detalhada do produto
- Compartilhamento via WhatsApp, Twitter, Facebook e Pinterest

## [1.1.2] – 2025-05-03
### Added
- Criado um novo container results-header para organizar o contador e o seletor de ordenação
- Contador e o Seletor lado a lado
- Atualização da lista produtos JSON
- Melhorias no CSS da busca e head

### Changed
- Refatorada a inicialização de produtos com nova função `initializeProducts`
- Melhorada a estrutura de event listeners para melhor performance
- Implementado IntersectionObserver para animações de produtos
- Otimizado o gerenciamento de estado da aplicação

### Fixed
- Corrigido erro de inicialização da aplicação
- Resolvido problema com event listeners duplicados
- Melhorada a contagem e exibição de produtos
- Corrigida a estrutura de inicialização do DOM

## [1.1.1] – 2025-05-03
### Changed
- Corrigido comportamento do rodapé em mobile (>=768px e <480px).
- Ajustadas propriedades CSS de `.container` e `#products-list` para `position: static` e `z-index: auto`.
- Removido `flex-grow` do container para permitir fluxo normal do rodapé.

## [1.1.0] – 2023-05-03
### Added
- Navegação por categorias com botões no desktop e scroll natural no mobile.
- Redesign visual inspirado no Pelando.
- Delegação de eventos em `scripts.js` para cliques em categorias.
- Python scraper para atualização de preços (+ cron/Agendador + backup JSON).

### Fixed
- Sintaxe CSS (comentários malformados, regras vazias).
- Comentários `line-clamp` padronizados.
- Corrigido fechamento de cards destacados (`.remove()`).
- Melhorias na visibilidade da data de atualização. 