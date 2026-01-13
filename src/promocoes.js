// =====================================================
// PROMOÇÕES AO VIVO - Em Casa com Cecília
// Versão com popup estilo Promobit + Busca Unificada + Imagens
// =====================================================

// URLs dos dados
const PROMOCOES_URL = '/data/promocoes.json';
const PRODUCTS_URL = '/data/products.json';

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

async function carregarPromocoes() {
    try {
        // Carregar promoções
        const response = await fetch(PROMOCOES_URL);
        if (!response.ok) throw new Error('Erro ao carregar promoções');
        const data = await response.json();
        todasPromocoes = data.promocoes || [];
        todasPromocoes.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        // Carregar produtos (para busca unificada)
        try {
            const prodResponse = await fetch(PRODUCTS_URL);
            if (prodResponse.ok) {
                todosProdutos = await prodResponse.json();
            }
        } catch (e) {
            console.log('Products.json não disponível');
        }

        renderizarPromocoes();

    } catch (error) {
        console.error('Erro:', error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Erro ao carregar promoções.<br>Tente novamente mais tarde.</p>
            </div>
        `;
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
            if (!resultadosPorCategoria[cat]) {
                resultadosPorCategoria[cat] = 0;
            }
            resultadosPorCategoria[cat]++;
        }
    });
    
    return resultadosPorCategoria;
}

// =====================================================
// CRIAR HTML DO BOX "ENCONTRAMOS TAMBÉM EM..."
// =====================================================

function criarBoxResultadosCategorias(resultados) {
    const categorias = Object.entries(resultados);
    if (categorias.length === 0) return '';
    
    const linksHTML = categorias.map(([cat, count]) => {
        const nome = categoriasNomes[cat] || cat;
        return `<a href="/${cat}/" class="search-category-link">
            <i class="fas fa-arrow-right"></i>
            ${nome} <span>(${count} produto${count > 1 ? 's' : ''})</span>
        </a>`;
    }).join('');
    
    return `
        <div class="search-more-results">
            <div class="search-more-header">
                <i class="fas fa-box"></i>
                <span>Encontramos também em:</span>
            </div>
            <div class="search-more-links">
                ${linksHTML}
            </div>
        </div>
    `;
}

// =====================================================
// RENDERIZAR LISTA DE PROMOÇÕES
// =====================================================

function renderizarPromocoes() {
    const termoBusca = searchInput ? searchInput.value.toLowerCase().trim() : '';
    
    let promosFiltradas = todasPromocoes.filter(promo => {
        // Filtro por tipo
        if (filtroAtual === 'promo' && promo.tipo === 'cupom') return false;
        if (filtroAtual === 'cupom' && promo.tipo !== 'cupom') return false;

        // Filtro por busca
        if (termoBusca) {
            const texto = [
                promo.produto,
                promo.loja,
                promo.cupom,
                promo.info,
                promo.descricaoCupom,
                promo.codigoCupom
            ].filter(Boolean).join(' ').toLowerCase();
            
            return texto.includes(termoBusca);
        }

        return true;
    });

    // Buscar também em produtos se houver termo de busca
    const resultadosCategorias = termoBusca ? buscarEmProdutos(termoBusca) : {};
    const temResultadosCategorias = Object.keys(resultadosCategorias).length > 0;

    if (promosFiltradas.length === 0 && !temResultadosCategorias) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>${termoBusca ? 'Nenhuma promoção encontrada.' : 'Nenhuma promoção no momento.'}<br>Volte em breve!</p>
            </div>
        `;
        return;
    }

    // Montar HTML
    let html = '';
    
    if (promosFiltradas.length > 0) {
        html = promosFiltradas.map((promo, index) => criarCardHTML(promo, index)).join('');
    } else if (termoBusca) {
        html = `
            <div class="empty-state small">
                <i class="fas fa-search"></i>
                <p>Nenhuma promoção ativa para "${termoBusca}"</p>
            </div>
        `;
    }
    
    // Adicionar box de resultados em categorias
    if (temResultadosCategorias) {
        html += criarBoxResultadosCategorias(resultadosCategorias);
    }
    
    container.innerHTML = html;

    // Adicionar event listeners nos cards
    document.querySelectorAll('.promo-card').forEach(card => {
        card.addEventListener('click', () => {
            const index = parseInt(card.dataset.index);
            const promo = promosFiltradas[index];
            abrirPopup(promo);
        });
    });
}

// =====================================================
// CRIAR HTML DO CARD (COM SUPORTE A IMAGEM)
// =====================================================

function criarCardHTML(promo, index) {
    const storeClass = promo.loja.toLowerCase().replace(/\s+/g, '-');
    const tempoAtras = calcularTempoAtras(promo.timestamp);
    const isCupom = promo.tipo === 'cupom';

    // Verificar se tem imagem
    const temImagem = promo.imagem && promo.imagem.trim() !== '';
    
    // HTML da imagem ou ícone fallback
    const imagemHTML = temImagem 
        ? `<img src="${promo.imagem}" alt="${promo.produto || promo.descricaoCupom}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
           <i class="fas fa-${isCupom ? 'ticket-alt' : 'shopping-bag'}" style="display:none;"></i>`
        : `<i class="fas fa-${isCupom ? 'ticket-alt' : 'shopping-bag'}"></i>`;

    if (isCupom) {
        return `
            <article class="promo-card cupom-card" data-index="${index}">
                <div class="promo-image">
                    ${imagemHTML}
                </div>
                <div class="promo-info">
                    <span class="promo-store ${storeClass}">${promo.loja}</span>
                    <h3 class="promo-title">🏷️ ${promo.descricaoCupom}</h3>
                    <div class="promo-meta">
                        <span class="promo-time"><i class="far fa-clock"></i> ${tempoAtras}</span>
                    </div>
                </div>
                <button class="promo-btn cupom-btn">Ver Cupom</button>
            </article>
        `;
    }

    const temDesconto = promo.precoAntigo && promo.precoAntigo > promo.preco;
    const desconto = temDesconto ? Math.round((1 - promo.preco / promo.precoAntigo) * 100) : 0;

    return `
        <article class="promo-card ${promo.destaque ? 'destaque' : ''}" data-index="${index}">
            <div class="promo-image">
                ${imagemHTML}
            </div>
            <div class="promo-info">
                <span class="promo-store ${storeClass}">${promo.loja}</span>
                <h3 class="promo-title">${promo.destaque ? '🔥 ' : ''}${promo.produto}</h3>
                <div class="promo-meta">
                    <span class="promo-time"><i class="far fa-clock"></i> ${tempoAtras}</span>
                    ${promo.cupom ? '<span><i class="fas fa-tag"></i> Com cupom</span>' : ''}
                </div>
            </div>
            <div class="promo-pricing">
                <span class="promo-price">R$ ${promo.preco.toFixed(2).replace('.', ',')}</span>
                ${temDesconto ? `<span class="promo-old-price">R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}</span>` : ''}
                ${desconto > 0 ? `<span class="promo-discount">-${desconto}%</span>` : ''}
            </div>
            <button class="promo-btn">Ver Oferta</button>
        </article>
    `;
}

// =====================================================
// POPUP (COM SUPORTE A IMAGEM)
// =====================================================

function abrirPopup(promo) {
    const isCupom = promo.tipo === 'cupom';
    const storeClass = promo.loja.toLowerCase().replace(/\s+/g, '-');
    const temImagem = promo.imagem && promo.imagem.trim() !== '';
    
    let html = '';

    if (isCupom) {
        // Popup de CUPOM
        html = `
            ${temImagem ? `<div class="popup-image"><img src="${promo.imagem}" alt="${promo.descricaoCupom}"></div>` : ''}
            <div class="popup-header">
                <span class="popup-store ${storeClass}">${promo.loja}</span>
                <h3 class="popup-title">🏷️ ${promo.descricaoCupom}</h3>
            </div>
            
            <div class="popup-cupom">
                <p class="popup-cupom-label">Use o cupom abaixo:</p>
                <div class="popup-cupom-code">
                    <code>${promo.codigoCupom}</code>
                    <button class="popup-cupom-copy" onclick="copiarCupom('${promo.codigoCupom}')">
                        <i class="fas fa-copy"></i> Copiar
                    </button>
                </div>
            </div>
            
            <a href="${promo.link}" target="_blank" rel="noopener" class="popup-cta" onclick="fecharPopup()">
                <i class="fas fa-external-link-alt"></i>
                IR PARA ${promo.loja.toUpperCase()}
            </a>
            
            <div class="popup-share">
                <button class="popup-share-btn" onclick="copiarLink('${promo.link}')">
                    <i class="fas fa-link"></i> Copiar link
                </button>
                <button class="popup-share-btn whatsapp" onclick="compartilharWhatsApp('cupom', ${JSON.stringify(promo).replace(/'/g, "\\'")})">
                    <i class="fab fa-whatsapp"></i> Compartilhar
                </button>
            </div>
        `;
    } else {
        // Popup de PROMOÇÃO
        const temDesconto = promo.precoAntigo && promo.precoAntigo > promo.preco;
        const desconto = temDesconto ? Math.round((1 - promo.preco / promo.precoAntigo) * 100) : 0;

        html = `
            ${temImagem ? `<div class="popup-image"><img src="${promo.imagem}" alt="${promo.produto}"></div>` : ''}
            <div class="popup-header">
                <span class="popup-store ${storeClass}">${promo.loja}</span>
                <h3 class="popup-title">${promo.produto}</h3>
            </div>
            
            <div class="popup-price-section">
                <span class="popup-price">R$ ${promo.preco.toFixed(2).replace('.', ',')}</span>
                ${temDesconto ? `<span class="popup-old-price">R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}</span>` : ''}
                ${desconto > 0 ? `<div class="popup-discount">-${desconto}% de desconto</div>` : ''}
            </div>
            
            ${promo.cupom ? `
                <div class="popup-cupom">
                    <p class="popup-cupom-label">Use o cupom para garantir o desconto:</p>
                    <div class="popup-cupom-code">
                        <code>${promo.cupom}</code>
                        <button class="popup-cupom-copy" onclick="copiarCupom('${promo.cupom}')">
                            <i class="fas fa-copy"></i> Copiar
                        </button>
                    </div>
                </div>
            ` : ''}
            
            ${promo.info ? `
                <div class="popup-info">
                    <i class="fas fa-info-circle"></i>
                    ${promo.info}
                </div>
            ` : ''}
            
            <a href="${promo.link}" target="_blank" rel="noopener" class="popup-cta" onclick="fecharPopup()">
                <i class="fas fa-shopping-cart"></i>
                APROVEITAR OFERTA
            </a>
            
            <div class="popup-share">
                <button class="popup-share-btn" onclick="copiarLink('${promo.link}')">
                    <i class="fas fa-link"></i> Copiar link
                </button>
                <button class="popup-share-btn whatsapp" onclick="compartilharWhatsApp('promo', ${JSON.stringify(promo).replace(/'/g, "\\'")})">
                    <i class="fab fa-whatsapp"></i> Compartilhar
                </button>
            </div>
        `;
    }

    popupContent.innerHTML = html;
    popupOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function fecharPopup() {
    popupOverlay.classList.remove('active');
    document.body.style.overflow = '';
}

// =====================================================
// FUNÇÕES AUXILIARES
// =====================================================

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
    // Remover toast existente
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

// Funções globais
window.copiarCupom = function(cupom) {
    navigator.clipboard.writeText(cupom).then(() => {
        mostrarToast('✅ Cupom copiado: ' + cupom);
    }).catch(() => {
        mostrarToast('❌ Erro ao copiar');
    });
};

window.copiarLink = function(link) {
    navigator.clipboard.writeText(link).then(() => {
        mostrarToast('✅ Link copiado!');
    }).catch(() => {
        mostrarToast('❌ Erro ao copiar');
    });
};

window.compartilharWhatsApp = function(tipo, promo) {
    let texto = '';
    
    if (tipo === 'cupom') {
        // Formato para cupom
        texto = `🔥 CUPOM ${promo.loja.toUpperCase()}\n\n`;
        texto += `${promo.descricaoCupom}\n\n`;
        texto += `🎟️ Cupom: ${promo.codigoCupom}\n\n`;
        texto += `👉 ${promo.link}`;
    } else {
        // Formato para promoção
        texto = `🔥 ${promo.produto}\n\n`;
        texto += `💲 *R$ ${promo.preco.toFixed(2).replace('.', ',')}*`;
        
        if (promo.precoAntigo && promo.precoAntigo > promo.preco) {
            const desconto = Math.round((1 - promo.preco / promo.precoAntigo) * 100);
            texto += ` ~De R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}~ (-${desconto}%)`;
        }
        
        if (promo.info) {
            texto += `\n${promo.info}`;
        }
        
        if (promo.cupom) {
            texto += `\n\n🎟️ Cupom: ${promo.cupom}`;
        }
        
        texto += `\n\n👉 ${promo.link}`;
    }

    const url = 'https://api.whatsapp.com/send?text=' + encodeURIComponent(texto);
    window.open(url, '_blank');
};

window.fecharPopup = fecharPopup;

// =====================================================
// EVENT LISTENERS
// =====================================================

// Fechar popup
if (popupClose) {
    popupClose.addEventListener('click', fecharPopup);
}

if (popupOverlay) {
    popupOverlay.addEventListener('click', (e) => {
        if (e.target === popupOverlay) fecharPopup();
    });
}

// Fechar com ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') fecharPopup();
});

// Busca
if (searchInput) {
    searchInput.addEventListener('input', () => {
        renderizarPromocoes();
    });
}

// Filtros
if (filterButtons) {
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filtroAtual = btn.dataset.filter;
            renderizarPromocoes();
        });
    });
}

// =====================================================
// INICIALIZAÇÃO
// =====================================================

// Carregar promoções
carregarPromocoes();

// Atualizar a cada 2 minutos
setInterval(carregarPromocoes, 120000);
