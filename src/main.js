/**
 * scripts.js - Script principal do site de showcase de produtos
 * Versão: 1.1.2
 * Última atualização: 11/05/2025
 * Autor: Em Casa com Cecília
 * 
 * Este arquivo contém a lógica principal do site, incluindo:
 * - Carregamento de dados de produtos
 * - Filtragem e exibição de produtos
 * - Funcionalidade de pesquisa
 * - Interatividade dos cards de produtos
 * - Navegação por categorias
 * - Detecção de bloqueadores de anúncios
 */

import { carregarPromocoes } from './promocoes.js';
import { createProductElement, manageProductVisibility, getCategoryName } from './domUtils.js';
import { filterProducts, sortProducts } from './filtering.js';
import { initializeState, updateState } from './stateManager.js';

// Correção para problemas de carregamento de imagens em navegadores específicos
if (navigator.userAgent.indexOf('Chrome') > -1 || navigator.userAgent.indexOf('Opera') > -1) {
    window.addEventListener('load', () => {
        document.querySelectorAll('.store-logo, .youtube-logo, .review-logo').forEach(img => {
            const currentSrc = img.src;
            img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
            setTimeout(() => { img.src = currentSrc + '?v=' + Date.now(); }, 10);
        });
    });
}

// Solução específica para o Microsoft Edge
if (navigator.userAgent.indexOf('Edg') > -1) {
    document.documentElement.classList.add('edge-browser');
    const style = document.createElement('style');
    style.textContent = `
        .edge-browser .store-logo, 
        .edge-browser .youtube-logo, 
        .edge-browser .review-logo {
            opacity: 1 !important;
            visibility: visible !important;
            display: inline-block !important;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Função de debounce para limitar a frequência de execução de uma função
 * @param {Function} func - Função a ser executada após o delay
 * @param {number} wait - Tempo de espera em milissegundos
 * @return {Function} Função com debounce aplicado
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function initializeProducts() {
    try {
        const products = await loadProductsData();
        if (!products || products.length === 0) {
            console.error('Nenhum produto encontrado');
            return;
        }

        const container = document.getElementById('products-list');
        if (!container) {
            console.error('Container de produtos não encontrado');
            return;
        }

        // Limpar container existente
        container.innerHTML = '';

        // Criar elementos para cada produto
        products.forEach(product => {
            const productElement = createProductElement(product);
            container.appendChild(productElement);
            
            // Adicionar evento de clique
            productElement.addEventListener('click', function(e) {
                if (!e.target.closest('a') && !e.target.closest('button')) {
                    handleProductClick(this);
                }
            });
        });

        // Inicializar observador de interseção
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });

        // Observar cada produto
        document.querySelectorAll('.product').forEach(product => {
            observer.observe(product);
        });

        // Atualizar contagem de produtos
        updateProductCount(products.length);
        
        // Inicializar os elementos de produto para uso em updateProducts
        window.productElements = Array.from(document.querySelectorAll('.product'));

    } catch (error) {
        console.error('Erro ao inicializar produtos:', error);
    }
}

// Função auxiliar para atualizar a contagem de produtos
function updateProductCount(count) {
    const countElement = document.getElementById('results-count');
    if (countElement) {
        countElement.textContent = `${count} produtos encontrados`;
    }
}

// Após a definição de initializeProducts e antes do DOMContentLoaded
function highlightProductFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get('produto');
    if (!slug) return;
    // Procurar o card pelo slug do nome
    const allProducts = document.querySelectorAll('.product');
    for (const product of allProducts) {
        const name = (product.getAttribute('data-product-name') || '').toLowerCase().replace(/\s+/g, '-');
        if (encodeURIComponent(name) === slug) {
            // Scroll até o card (opcional)
            product.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Destacar o card
            setTimeout(() => handleProductClick(product), 300);
            break;
        }
    }
}

// Inicialização da aplicação
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Definir elementos globais para acesso em todas as funções
        window.elements = {
        searchInput: document.getElementById('omnisearch'),
        clearSearchBtn: document.getElementById('clear-search'),
            categoryLinks: document.querySelectorAll('.category-links a'),
            prevCategoryBtn: document.querySelector('.prev-category-btn'),
            nextCategoryBtn: document.querySelector('.next-category-btn'),
            productsList: document.getElementById('products-list'),
        resultsCount: document.getElementById('results-count'),
        noResults: document.getElementById('no-results'),
        noResultsMessage: document.getElementById('no-results-message'),
            categorySuggestions: document.getElementById('category-suggestions')
        };

        // Inicializar estado global
        window.state = initializeState(window.elements);
        
        // Inicializar produtos
        window.productElements = [];
        await initializeProducts();
        // Inicializar produtos
        
        
        // Carregar promoções ao vivo
        carregarPromocoes();
        
       
        // Chamar highlightProductFromUrl após os produtos serem carregados
        highlightProductFromUrl();

        // Configurar event listeners
        if (window.elements.searchInput) {
            window.elements.searchInput.addEventListener('input', debounce((e) => {
                handleSearch(e.target.value, window.state);
            }, 300));
        }

        if (window.elements.clearSearchBtn) {
            window.elements.clearSearchBtn.addEventListener('click', () => {
                window.elements.searchInput.value = '';
                handleSearch('', window.state);
            });
        }

        // Event listeners para categorias
        window.elements.categoryLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                handleCategoryClick(e.target, window.state);
            });
        });

        // Event listeners para navegação de categorias
        if (window.elements.prevCategoryBtn) {
            window.elements.prevCategoryBtn.addEventListener('click', () => {
                handleCategoryNavigation('prev', window.state);
            });
        }

        if (window.elements.nextCategoryBtn) {
            window.elements.nextCategoryBtn.addEventListener('click', () => {
                handleCategoryNavigation('next', window.state);
            });
        }

        // Atualizar visibilidade dos botões de navegação
        updateButtonVisibility();

    } catch (error) {
        console.error('Erro ao inicializar a aplicação:', error);
    }
});

function handleCategoryClick(target, state) {
    const category = target.getAttribute('data-category');
    if (!category) return;
    
    console.log('Categoria clicada:', category);
    
    // Atualizar a categoria selecionada no estado
    window.state.selectedCategory = category;
    
    // Atualizar a classe ativa no menu de categorias
    window.elements.categoryLinks.forEach(link => {
        link.classList.remove('active');
    });
    target.classList.add('active');
    
    // Atualizar a lista de produtos
    updateProducts();
}

function handleProductClick(product) {
    console.log('Produto clicado:', product);
    
    closeHighlight();
    
    const overlay = document.createElement('div');
    overlay.classList.add('product-overlay');
    overlay.classList.add('active');
    document.body.appendChild(overlay);

    const clone = product.cloneNode(true);
    clone.classList.add('highlighted');
    document.body.appendChild(clone);
    
    document.body.style.overflow = 'hidden';
    
    overlay.addEventListener('click', closeHighlight);
    
    const closeBtn = clone.querySelector('.close-highlight-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeHighlight();
        });
    }

    // Compartilhamento: apenas copiar link e WhatsApp
    const copyLinkBtn = clone.querySelector('.copy-link-btn');
    const whatsappBtn = clone.querySelector('.whatsapp-share-btn');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const shareUrl = this.getAttribute('data-share-url');
            navigator.clipboard.writeText(shareUrl).then(() => {
                alert('Link copiado para a área de transferência!');
            }).catch(err => {
                console.error('Erro ao copiar o link:', err);
                alert('Erro ao copiar o link. Tente novamente.');
            });
        });
    }
    if (whatsappBtn) {
        whatsappBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const shareUrl = this.getAttribute('data-share-url');
            const productName = clone.getAttribute('data-product-name') || 'Produto';
            const whatsappMessage = `Confira este produto: ${productName} - ${shareUrl}`;
            window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(whatsappMessage)}`,'_blank');
        });
    }
}

function updateButtonVisibility() {
    const container = window.elements.categoryLinks;
            const scrollLeft = container.scrollLeft;
            const scrollWidth = container.scrollWidth;
            const clientWidth = container.clientWidth;
    const isMobile = window.innerWidth <= 768;
    
    if (!isMobile) {
        window.elements.prevCategoryBtn.style.display = scrollLeft > 10 ? 'flex' : 'none';
        window.elements.nextCategoryBtn.style.display = 
            scrollLeft + clientWidth < scrollWidth - 10 ? 'flex' : 'none';
    }
    }

    function updateProducts() {
        console.log('Atualizando produtos...');
    console.log('Categoria selecionada:', window.state.selectedCategory);
    console.log('Termo de busca:', window.state.searchTerm);

    // Obter todos os produtos
    const allProducts = document.querySelectorAll('.product');
    window.productElements = Array.from(allProducts);
    
    // Filtrar produtos por categoria e termo de busca
    const matchedProductsInCategory = window.productElements.filter(product => {
        const productCategory = product.getAttribute('data-category');
        const productName = product.querySelector('h3').textContent.toLowerCase();
        
        const matchesCategory = window.state.selectedCategory === 'all' || 
                               productCategory === window.state.selectedCategory;
        const matchesSearch = !window.state.searchTerm || 
                             productName.includes(window.state.searchTerm.toLowerCase());
        
        return matchesCategory && matchesSearch;
    });
    
    // Filtrar produtos que correspondem ao termo de busca em qualquer categoria
    const matchedProductsOverall = window.productElements.filter(product => {
        const productName = product.querySelector('h3').textContent.toLowerCase();
        return !window.state.searchTerm || productName.includes(window.state.searchTerm.toLowerCase());
    });

        console.log('Produtos na categoria filtrada:', matchedProductsInCategory.length);
        console.log('Produtos totais com termo de busca:', matchedProductsOverall.length);

    // Mostrar produtos filtrados
    window.productElements.forEach(product => {
        product.style.display = 'none';
    });
    
    matchedProductsInCategory.forEach(product => {
        product.style.display = 'flex';
    });

    // Atualizar contagem de resultados
    const visibleCountInCategory = matchedProductsInCategory.length;
    const categoryName = getCategoryName(window.state.selectedCategory);
    window.elements.resultsCount.textContent = 
        `Encontrados: ${visibleCountInCategory} produto${visibleCountInCategory !== 1 ? 's' : ''} na categoria "${categoryName}"`;

    // Mostrar mensagem de "nenhum resultado" se necessário
    if (visibleCountInCategory === 0 && window.state.searchTerm) {
            if (matchedProductsOverall.length > 0) {
            window.elements.noResultsMessage.textContent = 
                `Não encontramos "${window.state.searchTerm}" na categoria "${categoryName}".`;
            window.elements.categorySuggestions.innerHTML = 
                '<p class="other-category-message">Encontramos os seguintes itens em outras categorias:</p>';
            
                const suggestionsList = document.createElement('div');
                suggestionsList.classList.add('suggestions-list');
            
            // Mostrar produtos de outras categorias que correspondem à busca
            const productsOutsideCategory = matchedProductsOverall.filter(
                product => !matchedProductsInCategory.includes(product)
            );
            
            productsOutsideCategory.forEach(product => {
                const clone = product.cloneNode(true);
                clone.style.display = 'flex';
                suggestionsList.appendChild(clone);
            });
            
            window.elements.categorySuggestions.appendChild(suggestionsList);
            window.elements.noResults.classList.add('visible');
        } else {
            window.elements.noResultsMessage.textContent = 
                `Nenhum produto encontrado para "${window.state.searchTerm}".`;
            window.elements.categorySuggestions.innerHTML = '';
            window.elements.noResults.classList.add('visible');
        }
    } else if (visibleCountInCategory === 0 && window.state.selectedCategory !== 'all') {
        window.elements.noResultsMessage.textContent = 
            `Nenhum produto encontrado na categoria "${categoryName}".`;
        window.elements.categorySuggestions.innerHTML = '';
        window.elements.noResults.classList.add('visible');
    } else {
        window.elements.noResults.classList.remove('visible');
        window.elements.categorySuggestions.innerHTML = '';
                }

    // Adicionar evento de clique aos produtos
    document.querySelectorAll('.product').forEach(product => {
        // Remover handler existente se houver
        if (product._clickHandler) {
            product.removeEventListener('click', product._clickHandler);
        }
        
        // Criar novo handler de clique
        product._clickHandler = function(e) {
            // Verificar se o clique não foi em um link ou botão
            if (!e.target.closest('a') && !e.target.closest('button')) {
                handleProductClick(product);
            }
        };
        
        // Adicionar o handler de clique
        product.addEventListener('click', product._clickHandler);
    });
}

function closeHighlight() {
    // Remover overlay
    const overlay = document.querySelector('.product-overlay');
    if (overlay) {
        overlay.remove();
    }
    
    // Remover produto destacado
    const highlighted = document.querySelector('.product.highlighted');
    if (highlighted) {
        highlighted.remove();
    }
    
    // Restaurar scroll do body
    document.body.style.overflow = '';
}

function handleSearch(term, state) {
    window.state.searchTerm = term;
    updateProducts();
}

function handleCategoryNavigation(direction, state) {
    const container = window.elements.categoryLinks;
    const scrollAmount = 200;

    if (direction === 'prev') {
        container.scrollBy({
            left: -scrollAmount,
            behavior: 'smooth'
        });
    } else if (direction === 'next') {
        container.scrollBy({
            left: scrollAmount,
            behavior: 'smooth'
        });
    }

    updateButtonVisibility();
}

function handleCopyLink(e) {
    e.preventDefault();
    const shareUrl = e.target.getAttribute('href');
                    navigator.clipboard.writeText(shareUrl).then(() => {
                        alert('Link copiado para a área de transferência!');
                    }).catch(err => {
                        console.error('Erro ao copiar o link:', err);
                        alert('Erro ao copiar o link. Tente novamente.');
                    });
}

function handleWhatsAppShare(e) {
    e.preventDefault();
    const shareUrl = e.target.getAttribute('href');
    const productName = e.target.getAttribute('data-product-name');
                const whatsappMessage = `Confira este produto: ${productName} - ${shareUrl}`;
    const whatsappBtn = e.target;
                whatsappBtn.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(whatsappMessage)}`;
}

function handleTwitterShare(e) {
    e.preventDefault();
    const shareUrl = e.target.getAttribute('href');
    const productName = e.target.getAttribute('data-product-name');
    const twitterMessage = `Confira este produto: ${productName} - ${shareUrl}`;
    const twitterBtn = e.target;
    twitterBtn.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(twitterMessage)}`;
}

function handleFacebookShare(e) {
    e.preventDefault();
    const shareUrl = e.target.getAttribute('href');
    const productName = e.target.getAttribute('data-product-name');
    const facebookMessage = `Confira este produto: ${productName} - ${shareUrl}`;
    const facebookBtn = e.target;
    facebookBtn.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}&quote=${encodeURIComponent(facebookMessage)}`;
}

function handlePinterestShare(e) {
    e.preventDefault();
    const shareUrl = e.target.getAttribute('href');
    const productName = e.target.getAttribute('data-product-name');
    const pinterestMessage = `Confira este produto: ${productName} - ${shareUrl}`;
    const pinterestBtn = e.target;
    pinterestBtn.href = `https://pinterest.com/pin/create/button/?url=${encodeURIComponent(shareUrl)}&description=${encodeURIComponent(pinterestMessage)}`;
}

function handleTelegramShare(e) {
    e.preventDefault();
    const shareUrl = e.target.getAttribute('href');
    const productName = e.target.getAttribute('data-product-name');
    const telegramMessage = `Confira este produto: ${productName} - ${shareUrl}`;
    const telegramBtn = e.target;
    telegramBtn.href = `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(telegramMessage)}`;
    }

    async function loadProductsData() {
        const possiblePaths = [
            'data/products.json',
            '/data/products.json',
            './data/products.json',
            '../data/products.json',
        ];

        let data = null;
        let lastError = null;

        for (const path of possiblePaths) {
            try {
                console.log(`Tentando carregar produtos de ${path}...`);
                const response = await fetch(path, { cache: 'no-store' });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                data = await response.json();
                console.log(`Produtos carregados com sucesso de ${path}`);
                break;
            } catch (error) {
                console.warn(`Erro ao carregar de ${path}:`, error.message);
                lastError = error;
            }
        }

        if (data) {
            return data;
        } else {
            console.error('Falha ao carregar produtos de todos os caminhos testados:', lastError?.message || 'Erro desconhecido');
            console.log('Usando produtos de exemplo para debug.');
            return [
                {
                    name: "Produto de exemplo para debug",
                    category: "outros",
                    date: "2025-04-01",
                    image: "images/fallback.png",
                    prices: {
                        "Amazon": {
                            price: 99.90,
                            link: "https://amazon.com.br",
                            logo: "images/logos/amazon.png"
                        },
                        "Mercado Livre": {
                            price: 89.90,
                            link: "https://mercadolivre.com.br",
                            logo: "images/logos/ML.png"
                        }
                    },
                    links: {
                        youtube: "https://youtube.com",
                        review: "https://emcasacomcecilia.com"
                    }
                },
                {
                    name: "Outro produto de exemplo",
                    category: "cozinha",
                    date: "2025-04-10",
                    image: "images/fallback.png",
                    prices: {
                        "Shopee": {
                            price: 79.90,
                            link: "https://shopee.com.br",
                            logo: "images/logos/shopee.png"
                        }
                    }
                }
            ];
        }
    }

// Export functions for testing
export {
    handleProductClick,
    updateButtonVisibility
};