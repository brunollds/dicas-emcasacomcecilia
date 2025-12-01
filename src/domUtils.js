/**
 * domUtils.js - Funções de utilidade para manipulação do DOM
 * Versão: 1.1.0
 * Última atualização: 03/05/2023
 * Autor: Em Casa com Cecília
 * 
 * Este arquivo contém funções utilitárias para criar, manipular e exibir
 * elementos do DOM relacionados aos produtos na página.
 */

/**
 * Sanitiza uma URL para evitar injeção de código malicioso
 * @param {string} url - URL a ser sanitizada
 * @return {string} URL sanitizada ou # se inválida
 */
export function sanitizeUrl(url) {
    if (typeof url !== 'string') return '#';
    return url.trim();
}

/**
 * Sanitiza o caminho de uma imagem e fornece fallback quando necessário
 * @param {string} path - Caminho da imagem a ser sanitizado
 * @return {string} Caminho sanitizado ou imagem de fallback
 */
export function sanitizeImagePath(path) {
    if (typeof path !== 'string' || !path) return './images/fallback.png';
    if (path.startsWith('/')) {
        path = path.substring(1);
    }
    if (!path.startsWith('./') && !path.startsWith('http')) {
        return './' + path;
    }
    return path;
}

/**
 * Formata uma data no padrão YYYY-MM-DD para DD/MM/YYYY
 * @param {string} dateStr - String de data no formato YYYY-MM-DD
 * @return {string} Data formatada ou mensagem de erro
 */
export function formatDate(dateStr) {
    if (!dateStr || typeof dateStr !== 'string') return 'Data não disponível';
    try {
        const [year, month, day] = dateStr.split('-');
        return `${day}/${month}/${year}`;
    } catch (e) {
        console.error('Erro ao formatar data:', e);
        return 'Data não disponível';
    }
}

/**
 * Converte um slug de categoria para nome formatado
 * @param {string} category - Slug da categoria (ex: "casa-inteligente")
 * @return {string} Nome formatado da categoria (ex: "Casa Inteligente")
 */
export function getCategoryName(category) {
    if (category === 'all') return 'Todas as Categorias';
    return category
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

export function createProductElement(product) {
    console.log("Criando elemento para produto:", product.name);
    
    const article = document.createElement('article');
    article.classList.add('product');
    article.setAttribute('data-category', product.category || 'outros');
    article.setAttribute('data-date', product.date || '1970-01-01');
    article.setAttribute('data-product-name', product.name || 'produto-sem-nome');
    
    let lowestPrice = Infinity;
    if (product.prices && Object.keys(product.prices).length > 0) {
        for (const store in product.prices) {
            const price = parseFloat(product.prices[store].price || 0);
            if (price > 0 && price < lowestPrice) {
                lowestPrice = price;
            }
        }
    }
    article.setAttribute('data-lowest-price', isFinite(lowestPrice) ? lowestPrice : 0);

    const closeBtn = document.createElement('button');
    closeBtn.classList.add('close-highlight-btn');
    closeBtn.innerHTML = '✕';
    closeBtn.setAttribute('aria-label', 'Fechar destaque do produto');
    article.appendChild(closeBtn);

    const metaDiv = document.createElement('div');
    metaDiv.classList.add('product-meta');

    const categoryTag = document.createElement('div');
    categoryTag.classList.add('category-tag');
    categoryTag.textContent = getCategoryName(product.category || 'outros');
    categoryTag.setAttribute('data-category', product.category || 'outros');
    metaDiv.appendChild(categoryTag);

    const dateUpdated = document.createElement('div');
    dateUpdated.classList.add('date-updated');
    dateUpdated.textContent = `Atualizado em: ${formatDate(product.date)}`;
    metaDiv.appendChild(dateUpdated);

    article.appendChild(metaDiv);

    const topDiv = document.createElement('div');
    topDiv.classList.add('product-top');

    const imageDiv = document.createElement('div');
    imageDiv.classList.add('product-image');
    const img = document.createElement('img');
    img.src = sanitizeImagePath(product.image);
    img.alt = `Imagem do produto: ${product.name || 'Produto sem nome'}`;
    img.width = 120;
    img.height = 90;
    img.setAttribute('loading', 'lazy');
    img.onerror = function() { 
        console.log(`Erro ao carregar imagem: ${product.image}`); 
        this.src = './images/fallback.png'; 
        this.alt = 'Imagem não disponível'; 
    };
    imageDiv.appendChild(img);
    topDiv.appendChild(imageDiv);

    const detailsDiv = document.createElement('div');
    detailsDiv.classList.add('product-details');

    const h3 = document.createElement('h3');
    h3.textContent = product.name || 'Produto sem nome';
    detailsDiv.appendChild(h3);

    const pricesDiv = document.createElement('div');
    pricesDiv.classList.add('prices');
    
    console.log(`Preços para ${product.name}:`, product.prices);
    
    if (product.prices && Object.keys(product.prices).length > 0) {
        for (const [store, info] of Object.entries(product.prices)) {
            const a = document.createElement('a');
            a.href = sanitizeUrl(info.link);
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.classList.add('affiliate-link');
            a.setAttribute('data-store', store);
            a.setAttribute('data-product', product.name || 'produto');
            a.setAttribute('aria-label', `Comprar ${product.name || 'produto'} na ${store} por R$ ${(info.price || 0).toFixed(2)}`);

            const logoImg = document.createElement('img');
            logoImg.src = sanitizeImagePath(info.logo);
            logoImg.alt = `Logo da loja ${store}`;
            logoImg.classList.add('store-logo');
            logoImg.width = 20;
            logoImg.height = 20;
            logoImg.setAttribute('loading', 'lazy');
            logoImg.onerror = function() { 
                console.log(`Erro ao carregar logo da loja: ${this.src}`);
                this.src = './images/fallback.png';
                this.style.display = 'inline-block';
                this.alt = 'Logo não disponível'; 
            };
            a.appendChild(logoImg);
            logoImg.style.display = 'inline-block';
            logoImg.style.visibility = 'visible';
            logoImg.crossOrigin = 'anonymous';

            const priceSpan = document.createElement('span');
            priceSpan.textContent = ` R$ ${(info.price || 0).toFixed(2)}`;
            a.appendChild(priceSpan);
            
            pricesDiv.appendChild(a);
            
            console.log(`Adicionado preço da loja ${store}: R$ ${(info.price || 0).toFixed(2)}`);
        }

        const prices = [...pricesDiv.querySelectorAll('a')];
        if (prices.length > 0) {
            if (prices.length === 1) {
                prices[0].classList.add('lowest-price');
                
                // Adicionar o ícone "+" após o preço mais baixo
                const plusIcon = document.createElement('div');
                plusIcon.classList.add('plus-icon');
                plusIcon.setAttribute('aria-label', 'Ver mais opções');
                plusIcon.innerHTML = '<i class="fa-solid fa-square-plus"></i>';
                prices[0].parentNode.insertBefore(plusIcon, prices[0].nextSibling);
            } else {
                let menor = prices.reduce((prev, cur) => {
                    const pricePrev = parseFloat(cur.textContent.replace(/[^\d,]/g, '').replace(',', '.'));
                    const priceCur = parseFloat(prev.textContent.replace(/[^\d,]/g, '').replace(',', '.'));
                    return pricePrev < priceCur ? cur : prev;
                });
                menor.classList.add('lowest-price');
                
                // Adicionar o ícone "+" após o preço mais baixo
                const plusIcon = document.createElement('div');
                plusIcon.classList.add('plus-icon');
                plusIcon.setAttribute('aria-label', 'Ver mais opções');
                plusIcon.innerHTML = '<i class="fa-solid fa-square-plus"></i>';
                menor.parentNode.insertBefore(plusIcon, menor.nextSibling);
            }
        }

    } else {
        console.warn(`Produto ${product.name} não tem preços definidos`);
        const noPrice = document.createElement('p');
        noPrice.textContent = 'Preços não disponíveis';
        noPrice.style.color = '#a0a0a0';
        pricesDiv.appendChild(noPrice);
    }
    
    detailsDiv.appendChild(pricesDiv);

    const linksDiv = document.createElement('div');
    linksDiv.classList.add('links');
    if (product.links?.youtube) {
        const a = document.createElement('a');
        a.href = sanitizeUrl(product.links.youtube);
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.classList.add('youtube-icon', 'youtube-link');
        a.setAttribute('data-product', product.name || 'produto');
        a.setAttribute('aria-label', 'Vídeo no YouTube');

        // Substituir a imagem do YouTube por ícone do Font Awesome
        const youtubeIcon = document.createElement('i');
        youtubeIcon.classList.add('fa-brands', 'fa-square-youtube');
        a.appendChild(youtubeIcon);

        const youtubeText = document.createElement('span');
        youtubeText.textContent = 'YouTube';
        a.appendChild(youtubeText);
        
        linksDiv.appendChild(a);
    }
    if (product.links?.review) {
        const a = document.createElement('a');
        a.href = sanitizeUrl(product.links.review);
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.classList.add('review-link');
        a.setAttribute('data-product', product.name || 'produto');
        a.setAttribute('aria-label', 'Review do produto');

        const reviewIcon = document.createElement('img');
        reviewIcon.src = './images/logos/review.png';
        reviewIcon.alt = 'Ícone de Review';
        reviewIcon.classList.add('review-logo');
        reviewIcon.width = 16;
        reviewIcon.height = 16;
        reviewIcon.setAttribute('loading', 'lazy');
        reviewIcon.onerror = function() { 
            this.src = './images/fallback.png'; 
            this.alt = 'Ícone de Review não disponível'; 
        };
        a.appendChild(reviewIcon);

        const reviewText = document.createElement('span');
        reviewText.textContent = 'Review';
        a.appendChild(reviewText);
        
        linksDiv.appendChild(a);
    }
    detailsDiv.appendChild(linksDiv);

    const shareDiv = document.createElement('div');
    shareDiv.classList.add('share-actions');
    // Gerar link único do produto
    const productSlug = encodeURIComponent((product.name || 'produto').toLowerCase().replace(/\s+/g, '-'));
    const productUrl = `${window.location.origin}${window.location.pathname}?produto=${productSlug}`;
    shareDiv.innerHTML = `
        <span>Compartilhe:</span>
        <button class="copy-link-btn" aria-label="Copiar link do produto" data-share-url="${productUrl}"><i class="fa-solid fa-link"></i></button>
        <a class="whatsapp-share-btn" aria-label="Enviar pelo WhatsApp" target="_blank" rel="noopener noreferrer" data-share-url="${productUrl}"><i class="fa-brands fa-whatsapp"></i></a>
    `;
    detailsDiv.appendChild(shareDiv);

    topDiv.appendChild(detailsDiv);
    article.appendChild(topDiv);

    return article;
}

export function manageProductVisibility(productsToShow, container) {
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }
    
    productsToShow.forEach(product => {
        const clone = product.cloneNode(true);
        clone.style.display = 'flex';
        container.appendChild(clone);
    });
}