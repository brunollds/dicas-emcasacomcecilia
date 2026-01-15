// =====================================================
// PROMOÇÕES AO VIVO - Em Casa com Cecília
// Versão com popup estilo Promobit + Busca Unificada + Infinite Scroll
// =====================================================

// URLs dos dados
const PROMOCOES_URL = '/data/promocoes.json';
const PRODUCTS_URL = '/data/products.json';

// Controle de carregamento (Infinite Scroll)
let limiteExibicao = 20; 
const ITENS_POR_PAGINA = 20;
let observer; // Para o carregamento automático
let promosFiltradasAtuais = []; // Armazena a lista filtrada para o popup

// Elementos do DOM
const container = document.getElementById('promos-container');
const searchInput = document.getElementById('searchInput');
const filterButtons = document.querySelectorAll('.filter-btn');
const popupOverlay = document.getElementById('promoPopupOverlay');
const popupContent = document.getElementById('popupContent');
const popupClose = document.getElementById('popupClose');

// Estado
let todasPromocoes = [];
let todosProdutos = [];
let filtroAtual = 'todos';

// Mapeamento de categorias para nomes legíveis
const categoriasNomes = {
    'cozinha': 'Cozinha',
    'tecnologia': 'Tecnologia',
    'casa-inteligente': 'Casa Inteligente',
    'sala-de-estar': 'Sala de Estar',
    'lavanderia': 'Lavanderia',
    'banheiro': 'Banheiro',
    'alimentos': 'Alimentos & Bebidas',
    'outros': 'Outros'
};

// =====================================================
// CARREGAR DADOS
// =====================================================

const LIMITE_HORAS = 72;

function filtrarPromocoesRecentes(promocoes) {
    const agora = new Date();
    const limiteMs = LIMITE_HORAS * 60 * 60 * 1000;
    
    return promocoes.filter(promo => {
        if (!promo.timestamp) return false;
        const dataPromo = new Date(promo.timestamp);
        return (agora - dataPromo) <= limiteMs;
    });
}

async function carregarPromocoes() {
    try {
        const response = await fetch(PROMOCOES_URL);
        if (!response.ok) throw new Error('Erro ao carregar promoções');
        const data = await response.json();
        
        todasPromocoes = filtrarPromocoesRecentes(data.promocoes || []);
        todasPromocoes.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        try {
            const prodResponse = await fetch(PRODUCTS_URL);
            if (prodResponse.ok) {
                todosProdutos = await prodResponse.json();
            }
        } catch (e) {
            console.log('Products.json não disponível');
        }

        renderizarPromocoes(true); // Inicializa a lista

    } catch (error) {
        console.error('Erro:', error);
        container.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Erro ao carregar promoções.</p></div>`;
    }
}

// =====================================================
// BUSCAR EM PRODUTOS (CATEGORIAS)
// =====================================================

function buscarEmProdutos(termo) {
    if (!termo || todosProdutos.length === 0) return {};
    const termoLower = termo.toLowerCase();
    const resultadosPorCategoria = {};
    
    todosProdutos.forEach(produto => {
        const textosProduto = [produto.name].filter(Boolean).join(' ').toLowerCase();
        if (textosProduto.includes(termoLower)) {
            const cat = produto.category;
            resultadosPorCategoria[cat] = (resultadosPorCategoria[cat] || 0) + 1;
        }
    });
    return resultadosPorCategoria;
}

function criarBoxResultadosCategorias(resultados) {
    const categorias = Object.entries(resultados);
    if (categorias.length === 0) return '';
    
    const linksHTML = categorias.map(([cat, count]) => {
        const nome = categoriasNomes[cat] || cat;
        return `<a href="/${cat}/" class="search-category-link"><i class="fas fa-arrow-right"></i>${nome} <span>(${count} produto${count > 1 ? 's' : ''})</span></a>`;
    }).join('');
    
    return `<div class="search-more-results"><div class="search-more-header"><i class="fas fa-box"></i><span>Encontramos também em:</span></div><div class="search-more-links">${linksHTML}</div></div>`;
}

// =====================================================
// RENDERIZAR LISTA DE PROMOÇÕES (COM INFINITE SCROLL)
// =====================================================

function renderizarPromocoes(resetar = true) {
    if (resetar) {
        limiteExibicao = ITENS_POR_PAGINA;
        container.innerHTML = ''; 
    }

    const termoBusca = searchInput ? searchInput.value.toLowerCase().trim() : '';
    
    // Filtra a lista completa
    promosFiltradasAtuais = todasPromocoes.filter(promo => {
        if (filtroAtual === 'promo' && promo.tipo === 'cupom') return false;
        if (filtroAtual === 'cupom' && promo.tipo !== 'cupom') return false;
        if (termoBusca) {
            const texto = [promo.produto, promo.loja, promo.cupom, promo.info, promo.descricaoCupom, promo.codigoCupom].filter(Boolean).join(' ').toLowerCase();
            return texto.includes(termoBusca);
        }
        return true;
    });

    // Pega a fatia para exibir agora
    const listaParaExibirNow = promosFiltradasAtuais.slice(container.querySelectorAll('.promo-card').length, limiteExibicao);

    if (promosFiltradasAtuais.length === 0) {
        const resultadosCategorias = termoBusca ? buscarEmProdutos(termoBusca) : {};
        if (Object.keys(resultadosCategorias).length > 0) {
            container.innerHTML = criarBoxResultadosCategorias(resultadosCategorias);
        } else {
            container.innerHTML = `<div class="empty-state"><i class="fas fa-search"></i><p>Nenhuma promoção encontrada.</p></div>`;
        }
        return;
    }

    // Adiciona os cards novos
    listaParaExibirNow.forEach((promo) => {
        const cardHTML = criarCardHTML(promo);
        container.insertAdjacentHTML('beforeend', cardHTML);
    });

    // Gerencia o ponto de parada (sentinela) para carregar mais
    const antigoSentinela = document.getElementById('sentinela');
    if (antigoSentinela) antigoSentinela.remove();

    if (limiteExibicao < promosFiltradasAtuais.length) {
        container.insertAdjacentHTML('beforeend', `<div id="sentinela" style="height: 50px; width: 100%;"></div>`);
        ativarCarregamentoAutomatico();
    }

    // Adiciona a busca unificada no final apenas se a lista filtrada acabou
    if (termoBusca && limiteExibicao >= promosFiltradasAtuais.length) {
        const resultadosCategorias = buscarEmProdutos(termoBusca);
        if (Object.keys(resultadosCategorias).length > 0) {
            container.insertAdjacentHTML('beforeend', criarBoxResultadosCategorias(resultadosCategorias));
        }
    }

    vincularCliques();
}

function ativarCarregamentoAutomatico() {
    const sentinela = document.getElementById('sentinela');
    if (!sentinela) return;

    if (observer) observer.disconnect();
    observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            limiteExibicao += ITENS_POR_PAGINA;
            renderizarPromocoes(false); 
        }
    }, { rootMargin: '300px' });
    observer.observe(sentinela);
}

function vincularCliques() {
    document.querySelectorAll('.promo-card').forEach(card => {
        card.onclick = () => {
            // Descobre o índice real do item clicado na lista filtrada atual
            const todosCards = Array.from(container.querySelectorAll('.promo-card'));
            const idx = todosCards.indexOf(card);
            abrirPopup(promosFiltradasAtuais[idx]);
        };
    });
}

// =====================================================
// CRIAR HTML DO CARD
// =====================================================

function criarCardHTML(promo) {
    const storeClass = promo.loja.toLowerCase().replace(/\s+/g, '-');
    const tempoAtras = calcularTempoAtras(promo.timestamp);
    const isCupom = promo.tipo === 'cupom';

    const imagemHTML = promo.imagem 
        ? `<img src="${promo.imagem}" alt="${promo.produto}" onerror="this.parentElement.innerHTML='<i class=\'fas fa-shopping-bag\'></i>'">`
        : `<i class="fas fa-shopping-bag"></i>`;

    if (isCupom) {
        return `<article class="promo-card cupom-card"><div class="promo-image"><i class="fas fa-ticket-alt"></i></div><div class="promo-info"><span class="promo-store ${storeClass}">${promo.loja}</span><h3 class="promo-title">🏷️ ${promo.descricaoCupom}</h3><div class="promo-meta"><span class="promo-time"><i class="far fa-clock"></i> ${tempoAtras}</span></div></div><button class="promo-btn cupom-btn">Ver Cupom</button></article>`;
    }

    const precoValido = typeof promo.preco === 'number' && promo.preco > 0;
    const precoFormatado = precoValido ? `R$ ${promo.preco.toFixed(2).replace('.', ',')}` : 'Ver na loja';
    const temDesconto = precoValido && promo.precoAntigo && promo.precoAntigo > promo.preco;
    const precoAntigoFormatado = temDesconto ? `R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}` : '';
    const desconto = temDesconto ? Math.round((1 - promo.preco / promo.precoAntigo) * 100) : 0;

    return `<article class="promo-card ${promo.destaque ? 'destaque' : ''}"><div class="promo-image">${imagemHTML}</div><div class="promo-info"><span class="promo-store ${storeClass}">${promo.loja}</span><h3 class="promo-title">${promo.destaque ? '🔥 ' : ''}${promo.produto}</h3><div class="promo-meta"><span class="promo-time"><i class="far fa-clock"></i> ${tempoAtras}</span>${promo.cupom ? '<span><i class="fas fa-tag"></i> Com cupom</span>' : ''}</div></div><div class="promo-pricing"><span class="promo-price">${precoFormatado}</span>${temDesconto ? `<span class="promo-old-price">${precoAntigoFormatado}</span>` : ''}${desconto > 0 ? `<span class="promo-discount">-${desconto}%</span>` : ''}</div><button class="promo-btn">Ver Oferta</button></article>`;
}

// =====================================================
// POPUP E FUNÇÕES DE AÇÃO (WhatsApp, Cópia, etc)
// =====================================================

function abrirPopup(promo) {
    if (!promo) return;
    const isCupom = promo.tipo === 'cupom';
    const storeClass = promo.loja.toLowerCase().replace(/\s+/g, '-');
    const imagemHTML = promo.imagem ? `<div class="popup-product-img"><img src="${promo.imagem}" alt="${promo.produto}"></div>` : '';

    let html = '';
    if (isCupom) {
        html = `<div class="popup-header"><span class="popup-store ${storeClass}">${promo.loja}</span><h3 class="popup-title">🏷️ ${promo.descricaoCupom}</h3></div><div class="popup-cupom"><p class="popup-cupom-label">Use o cupom abaixo:</p><div class="popup-cupom-code"><code>${promo.codigoCupom}</code><button class="popup-cupom-copy" onclick="copiarCupom('${promo.codigoCupom}')"><i class="fas fa-copy"></i> Copiar</button></div></div><a href="${promo.link}" target="_blank" class="popup-cta" onclick="fecharPopup()"><i class="fas fa-external-link-alt"></i> IR PARA ${promo.loja.toUpperCase()}</a><div class="popup-share"><button class="popup-share-btn" onclick="copiarLink('${promo.link}')"><i class="fas fa-link"></i> Copiar link</button><button class="popup-share-btn whatsapp" onclick="compartilharWhatsApp('cupom', ${JSON.stringify(promo).replace(/'/g, "\\'")})"><i class="fab fa-whatsapp"></i> Compartilhar</button></div>`;
    } else {
        const precoValido = typeof promo.preco === 'number';
        const precoDisplay = precoValido ? `R$ ${promo.preco.toFixed(2).replace('.', ',')}` : 'Consulte o preço';
        const temDesconto = precoValido && promo.precoAntigo && promo.precoAntigo > promo.preco;
        const desconto = temDesconto ? Math.round((1 - promo.preco / promo.precoAntigo) * 100) : 0;

        html = `<div class="popup-header"><span class="popup-store ${storeClass}">${promo.loja}</span><h3 class="popup-title">${promo.produto}</h3></div>${imagemHTML}<div class="popup-price-section"><span class="popup-price">${precoDisplay}</span>${temDesconto ? `<span class="popup-old-price">R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}</span>` : ''}${desconto > 0 ? `<div class="popup-discount">-${desconto}% de desconto</div>` : ''}</div>${promo.cupom ? `<div class="popup-cupom"><p class="popup-cupom-label">Use o cupom para garantir o desconto:</p><div class="popup-cupom-code"><code>${promo.cupom}</code><button class="popup-cupom-copy" onclick="copiarCupom('${promo.cupom}')"><i class="fas fa-copy"></i> Copiar</button></div></div>` : ''}${promo.info ? `<div class="popup-info"><i class="fas fa-info-circle"></i> ${promo.info}</div>` : ''}<a href="${promo.link}" target="_blank" class="popup-cta" onclick="fecharPopup()"><i class="fas fa-shopping-cart"></i> APROVEITAR OFERTA</a><div class="popup-share"><button class="popup-share-btn" onclick="copiarLink('${promo.link}')"><i class="fas fa-link"></i> Copiar link</button><button class="popup-share-btn whatsapp" onclick="compartilharWhatsApp('promo', ${JSON.stringify(promo).replace(/'/g, "\\'")})"><i class="fab fa-whatsapp"></i> Compartilhar</button></div>`;
    }

    popupContent.innerHTML = html;
    popupOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function fecharPopup() {
    popupOverlay.classList.remove('active');
    document.body.style.overflow = '';
}

function calcularTempoAtras(timestamp) {
    const agora = new Date();
    const data = new Date(timestamp);
    const diffMs = agora - data;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHoras = Math.floor(diffMin / 60);
    if (diffMin < 1) return 'Agora';
    if (diffMin < 60) return `${diffMin} min`;
    if (diffHoras < 24) return `${diffHoras}h`;
    return `${Math.floor(diffHoras / 24)} dias`;
}

function mostrarToast(mensagem) {
    const existente = document.querySelector('.toast');
    if (existente) existente.remove();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = mensagem;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

// Ações globais (window)
window.copiarCupom = (cupom) => {
    navigator.clipboard.writeText(cupom).then(() => mostrarToast('✅ Cupom copiado: ' + cupom));
};
window.copiarLink = (link) => {
    navigator.clipboard.writeText(link).then(() => mostrarToast('✅ Link copiado!'));
};
window.compartilharWhatsApp = (tipo, promo) => {
    let texto = '';
    if (tipo === 'cupom') {
        texto = `🔥 CUPOM ${promo.loja.toUpperCase()}\n\n${promo.descricaoCupom}\n\n🎟️ Cupom: ${promo.codigoCupom}\n\n👉 ${promo.link}`;
    } else {
        texto = `🔥 ${promo.produto}\n\n💲 *R$ ${promo.preco.toFixed(2).replace('.', ',')}*`;
        if (promo.precoAntigo && promo.precoAntigo > promo.preco) {
            texto += ` ~De R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}~`;
        }
        if (promo.info) texto += `\n${promo.info}`;
        if (promo.cupom) texto += `\n\n🎟️ Cupom: ${promo.cupom}`;
        texto += `\n\n👉 ${promo.link}`;
    }
    window.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(texto), '_blank');
};
window.fecharPopup = fecharPopup;

// =====================================================
// EVENTOS E INICIALIZAÇÃO
// =====================================================

if (popupClose) popupClose.onclick = fecharPopup;
if (popupOverlay) popupOverlay.onclick = (e) => { if (e.target === popupOverlay) fecharPopup(); };
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fecharPopup(); });

if (searchInput) {
    searchInput.oninput = () => renderizarPromocoes(true);
}

if (filterButtons) {
    filterButtons.forEach(btn => {
        btn.onclick = () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filtroAtual = btn.dataset.filter;
            renderizarPromocoes(true);
        };
    });
}

carregarPromocoes();
setInterval(carregarPromocoes, 120000); 