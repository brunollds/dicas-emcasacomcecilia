// =====================================================
// PROMOÇÕES AO VIVO - Em Casa com Cecília
// Versão com popup estilo Promobit + Busca Unificada
// =====================================================

// URLs dos dados
const PROMOCOES_URL = '/data/promocoes.json';
const PRODUCTS_URL = '/data/products.json';

// No topo do arquivo, logo abaixo das URLs das APIs
let limiteExibicao = 20; 
const ITENS_POR_PAGINA = 20;
let observer; // Para o carregamento automático

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

// Limite de tempo para promoções (72 horas)
const LIMITE_HORAS = 72;

function filtrarPromocoesRecentes(promocoes) {
    const agora = new Date();
    const limiteMs = LIMITE_HORAS * 60 * 60 * 1000; // 72h em millisegundos
    
    return promocoes.filter(promo => {
        if (!promo.timestamp) return false;
        const dataPromo = new Date(promo.timestamp);
        return (agora - dataPromo) <= limiteMs;
    });
}

async function carregarPromocoes() {
    try {
        // Carregar promoções
        const response = await fetch(PROMOCOES_URL);
        if (!response.ok) throw new Error('Erro ao carregar promoções');
        const data = await response.json();
        
        // Filtrar apenas promoções das últimas 72h
        todasPromocoes = filtrarPromocoesRecentes(data.promocoes || []);
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

function renderizarPromocoes(resetar = true) {
    if (resetar) {
        limiteExibicao = ITENS_POR_PAGINA;
        container.innerHTML = ''; // Limpa a lista apenas no início
    }

    const termoBusca = searchInput ? searchInput.value.toLowerCase().trim() : '';
    
    let promosFiltradas = todasPromocoes.filter(promo => {
        if (filtroAtual === 'promo' && promo.tipo === 'cupom') return false;
        if (filtroAtual === 'cupom' && promo.tipo !== 'cupom') return false;
        if (termoBusca) {
            const texto = [promo.produto, promo.loja, promo.cupom, promo.info].filter(Boolean).join(' ').toLowerCase();
            return texto.includes(termoBusca);
        }
        return true;
    });

    const totalDisponivel = promosFiltradas.length;
    const listaParaExibir = promosFiltradas.slice(container.children.length, limiteExibicao);

    if (promosFiltradas.length === 0) {
        container.innerHTML = `<div class="empty-state"><p>Nenhuma promoção encontrada.</p></div>`;
        return;
    }

    // Adiciona apenas os novos cards sem apagar os antigos
    listaParaExibir.forEach((promo, index) => {
        // O index real para o clique deve considerar o que já estava na tela
        const realIndex = container.querySelectorAll('.promo-card').length; 
        const cardHTML = criarCardHTML(promo, realIndex);
        container.insertAdjacentHTML('beforeend', cardHTML);
    });

    // Remove sentinela antigo e adiciona novo se houver mais itens
    const antigoSentinela = document.getElementById('sentinela');
    if (antigoSentinela) antigoSentinela.remove();

    if (limiteExibicao < totalDisponivel) {
        container.insertAdjacentHTML('beforeend', `<div id="sentinela" style="height: 50px; width: 100%;"></div>`);
        ativarCarregamentoAutomatico();
    }

    // Configura os eventos de clique em TODOS os cards atuais
    configurarEventos(promosFiltradas);
}

function ativarCarregamentoAutomatico() {
    const sentinela = document.getElementById('sentinela');
    if (!sentinela) return;

    if (observer) observer.disconnect();

    observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            limiteExibicao += ITENS_POR_PAGINA;
            renderizarPromocoes(false); // Chama sem resetar para apenas "acrescentar"
        }
    }, { rootMargin: '300px' });

    observer.observe(sentinela);
}

function configurarEventos(listaFiltrada) {
    document.querySelectorAll('.promo-card').forEach((card, idx) => {
        card.onclick = () => {
            // Usa a lista filtrada completa para achar o item correto pelo index do card
            abrirPopup(listaFiltrada[idx]);
        };
    });
}

// 3. Adicione esta nova função para detectar o fim da página
function ativarCarregamentoAutomatico() {
    const sentinela = document.getElementById('sentinela');
    if (!sentinela) return;

    if (observer) observer.disconnect();

    observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            limiteExibicao += ITENS_POR_PAGINA;
            renderizarPromocoes();
        }
    }, { rootMargin: '200px' }); // Começa a carregar 200px antes de chegar no fim

    observer.observe(sentinela);
}

// 4. Ajuste sua função configurarEventos para lidar com os cliques
function configurarEventos(listaAtual) {
    document.querySelectorAll('.promo-card').forEach(card => {
        card.onclick = () => {
            const index = parseInt(card.dataset.index);
            abrirPopup(listaAtual[index]);
        };
    });
}

// Função para reatribuir cliques após renderizar
function configurarEventosCards(listaAtual) {
    // Cliques nos Cards para abrir Popup
    document.querySelectorAll('.promo-card').forEach(card => {
        card.addEventListener('click', () => {
            const index = parseInt(card.dataset.index);
            abrirPopup(listaAtual[index]);
        });
    });

    // Clique no botão "Carregar Mais"
    const btn = document.getElementById('btnCarregarMais');
    if (btn) {
        btn.addEventListener('click', () => {
            limiteExibicao += ITENS_POR_PAGINA;
            renderizarPromocoes();
        });
    }
}

// =====================================================
// CRIAR HTML DO CARD (COMPACTO)
// =====================================================

function criarCardHTML(promo, index) {
    const storeClass = promo.loja.toLowerCase().replace(/\s+/g, '-');
    const tempoAtras = calcularTempoAtras(promo.timestamp);
    const isCupom = promo.tipo === 'cupom';

    // HTML da Imagem: Usa a imagem salva ou um ícone de sacola como reserva
    const imagemHTML = promo.imagem 
        ? `<img src="${promo.imagem}" alt="${promo.produto}" onerror="this.parentElement.innerHTML='<i class=\'fas fa-shopping-bag\'></i>'">`
        : `<i class="fas fa-shopping-bag"></i>`;

    if (isCupom) {
        return `
            <article class="promo-card cupom-card" data-index="${index}">
                <div class="promo-image"><i class="fas fa-ticket-alt"></i></div>
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

    // Formatação segura de preços (evita o erro toFixed)
    const precoValido = typeof promo.preco === 'number' && promo.preco > 0;
    const precoFormatado = precoValido ? `R$ ${promo.preco.toFixed(2).replace('.', ',')}` : 'Ver na loja';
    
    const temDesconto = precoValido && promo.precoAntigo && promo.precoAntigo > promo.preco;
    const precoAntigoFormatado = temDesconto ? `R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}` : '';
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
                <span class="promo-price">${precoFormatado}</span>
                ${temDesconto ? `<span class="promo-old-price">${precoAntigoFormatado}</span>` : ''}
                ${desconto > 0 ? `<span class="promo-discount">-${desconto}%</span>` : ''}
            </div>
            <button class="promo-btn">Ver Oferta</button>
        </article>
    `;
}

// =====================================================
// POPUP
// =====================================================

function abrirPopup(promo) {
    const isCupom = promo.tipo === 'cupom';
    const storeClass = promo.loja.toLowerCase().replace(/\s+/g, '-');
    
    // HTML da Imagem para o Popup
    const imagemHTML = promo.imagem 
        ? `<div class="popup-product-img"><img src="${promo.imagem}" alt="${promo.produto}"></div>`
        : '';

    let html = '';

    if (isCupom) {
        // ... (Mantenha o código de cupom igual ou adicione a imagem se desejar)
        html = `
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
                <i class="fas fa-external-link-alt"></i> IR PARA ${promo.loja.toUpperCase()}
            </a>
            <div class="popup-share">
                <button class="popup-share-btn" onclick="copiarLink('${promo.link}')"><i class="fas fa-link"></i> Copiar link</button>
                <button class="popup-share-btn whatsapp" onclick="compartilharWhatsApp('cupom', ${JSON.stringify(promo).replace(/'/g, "\\'")})"><i class="fab fa-whatsapp"></i> Compartilhar</button>
            </div>
        `;
    } else {
        // Popup de PROMOÇÃO com segurança de preço e IMAGEM
        const precoValido = typeof promo.preco === 'number';
        const precoDisplay = precoValido ? `R$ ${promo.preco.toFixed(2).replace('.', ',')}` : 'Consulte o preço';
        const temDesconto = precoValido && promo.precoAntigo && promo.precoAntigo > promo.preco;
        const desconto = temDesconto ? Math.round((1 - promo.preco / promo.precoAntigo) * 100) : 0;

        html = `
            <div class="popup-header">
                <span class="popup-store ${storeClass}">${promo.loja}</span>
                <h3 class="popup-title">${promo.produto}</h3>
            </div>
            
            ${imagemHTML}

            <div class="popup-price-section">
                <span class="popup-price">${precoDisplay}</span>
                ${temDesconto ? `<span class="popup-old-price">R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}</span>` : ''}
                ${desconto > 0 ? `<div class="popup-discount">-${desconto}% de desconto</div>` : ''}
            </div>
            
            ${promo.cupom ? `
                <div class="popup-cupom">
                    <p class="popup-cupom-label">Use o cupom para garantir o desconto:</p>
                    <div class="popup-cupom-code">
                        <code>${promo.cupom}</code>
                        <button class="popup-cupom-copy" onclick="copiarCupom('${promo.cupom}')"><i class="fas fa-copy"></i> Copiar</button>
                    </div>
                </div>
            ` : ''}
            
            ${promo.info ? `<div class="popup-info"><i class="fas fa-info-circle"></i> ${promo.info}</div>` : ''}
            
            <a href="${promo.link}" target="_blank" rel="noopener" class="popup-cta" onclick="fecharPopup()">
                <i class="fas fa-shopping-cart"></i> APROVEITAR OFERTA
            </a>
            
            <div class="popup-share">
                <button class="popup-share-btn" onclick="copiarLink('${promo.link}')"><i class="fas fa-link"></i> Copiar link</button>
                <button class="popup-share-btn whatsapp" onclick="compartilharWhatsApp('promo', ${JSON.stringify(promo).replace(/'/g, "\\'")})"><i class="fab fa-whatsapp"></i> Compartilhar</button>
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
        // Título com emoji 🔥 (sem nome da loja)
        texto = `🔥 ${promo.produto}\n\n`;
        
        // Preço atual em negrito
        texto += `💲 *R$ ${promo.preco.toFixed(2).replace('.', ',')}*`;
        
        // Preço antigo riscado (se houver)
        if (promo.precoAntigo && promo.precoAntigo > promo.preco) {
            const desconto = Math.round((1 - promo.preco / promo.precoAntigo) * 100);
            texto += ` ~De R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}~ (-${desconto}%)`;
        }
        
        // Info extra (parcelamento, frete, etc)
        if (promo.info) {
            texto += `\n${promo.info}`;
        }
        
        // Cupom (se houver)
        if (promo.cupom) {
            texto += `\n\n🎟️ Cupom: ${promo.cupom}`;
        }
        
        // Link
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

