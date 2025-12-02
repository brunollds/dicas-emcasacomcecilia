// Carrega promoções do arquivo local
const PROMOCOES_URL = '/data/promocoes.json';
const LIMITE_INICIAL = 5;

let todasPromocoes = [];
let mostrandoTodas = false;

export async function carregarPromocoes() {
    const container = document.getElementById('promocoes-container');
    if (!container) return;

    try {
        const response = await fetch(PROMOCOES_URL);
        if (!response.ok) throw new Error('Erro ao carregar');

        const data = await response.json();
        todasPromocoes = data.promocoes || [];
        todasPromocoes.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        renderizarPromocoes();

    } catch (error) {
        console.error('Erro:', error);
        container.innerHTML = `
            <div class="promo-empty">
                <p>Nenhuma promoção no momento.</p>
            </div>
        `;
    }
}

function renderizarPromocoes() {
    const container = document.getElementById('promocoes-container');
    if (!container) return;

    if (todasPromocoes.length === 0) {
        container.innerHTML = `
            <div class="promo-empty">
                <p>Nenhuma promoção no momento. Volte em breve!</p>
            </div>
        `;
        return;
    }

    const promosMostrar = mostrandoTodas 
        ? todasPromocoes 
        : todasPromocoes.slice(0, LIMITE_INICIAL);

    let html = promosMostrar.map(promo => criarCardHTML(promo)).join('');

    if (!mostrandoTodas && todasPromocoes.length > LIMITE_INICIAL) {
        html += `
            <div class="ver-mais-container">
                <button class="btn-ver-mais" onclick="window.mostrarTodasPromocoes()">
                    Ver mais ${todasPromocoes.length - LIMITE_INICIAL} promoções
                </button>
            </div>
        `;
    }

    container.innerHTML = html;
}

function criarCardHTML(promo) {
    const storeClass = promo.loja.toLowerCase().replace(/\s+/g, '-');
    const tempoAtras = calcularTempoAtras(promo.timestamp);
    const isCupom = promo.tipo === 'cupom';

    if (isCupom) {
        const textoWhatsApp = `🏷️ CUPOM ${promo.loja.toUpperCase()}\n\n${promo.descricaoCupom}\n\n🏷️ Cupom: ${promo.codigoCupom}\n\n👉 ${promo.link}`;

        return `
            <article class="promo-card">
                <div class="promo-header">
                    <span class="store-badge ${storeClass}">${promo.loja}</span>
                    <span class="promo-time">${tempoAtras}</span>
                </div>
                <h3 class="promo-title" style="color: #ffc800;">🏷️ CUPOM</h3>
                <p style="color: #e0e0e0; margin-bottom: 15px;">${promo.descricaoCupom}</p>
                <div class="promo-cupom" onclick="copiarCupom('${promo.codigoCupom}')">
                    <code>${promo.codigoCupom}</code>
                    <span style="font-size: 0.8rem; opacity: 0.7;">📋 copiar</span>
                </div>
                <div class="promo-actions">
                    <a href="${promo.link}" target="_blank" class="btn-comprar" style="background: linear-gradient(90deg, #ffc800, #ffdb4d); color: #000;">
                        USAR CUPOM
                    </a>
                    <button class="btn-share" onclick="compartilharWhatsApp(\`${textoWhatsApp.replace(/`/g, "'")}\`)">
                        <i class="fab fa-whatsapp"></i>
                    </button>
                </div>
            </article>
        `;
    }

    const temDesconto = promo.precoAntigo && promo.precoAntigo > promo.preco;
    const desconto = temDesconto ? Math.round((1 - promo.preco / promo.precoAntigo) * 100) : 0;

    let textoWhatsApp = `🛒 ${promo.loja.toUpperCase()}\n\n${promo.produto}\n\n💲 R$ ${promo.preco.toFixed(2).replace('.', ',')}`;
    if (temDesconto) {
        textoWhatsApp += ` (era R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')} = -${desconto}%)`;
    }
    if (promo.info) textoWhatsApp += `\n${promo.info}`;
    if (promo.cupom) textoWhatsApp += `\n🏷️ Cupom: ${promo.cupom}`;
    textoWhatsApp += `\n\n👉 ${promo.link}`;

    return `
        <article class="promo-card ${promo.destaque ? 'destaque' : ''}">
            <div class="promo-header">
                <span class="store-badge ${storeClass}">${promo.loja}</span>
                <span class="promo-time">${tempoAtras}</span>
            </div>
            <h3 class="promo-title">${promo.destaque ? '🔥 ' : ''}${promo.produto}</h3>
            <div class="promo-price">
                <span class="price-current">R$ ${promo.preco.toFixed(2).replace('.', ',')}</span>
                ${temDesconto ? `<span class="price-old">R$ ${promo.precoAntigo.toFixed(2).replace('.', ',')}</span>` : ''}
                ${desconto > 0 ? `<span class="price-discount">-${desconto}%</span>` : ''}
            </div>
            ${promo.info ? `<p class="promo-info">${promo.info}</p>` : ''}
            ${promo.cupom ? `
                <div class="promo-cupom" onclick="copiarCupom('${promo.cupom}')">
                    <span>🏷️ Cupom:</span>
                    <code>${promo.cupom}</code>
                </div>
            ` : ''}
            <div class="promo-actions">
                <a href="${promo.link}" target="_blank" class="btn-comprar">
                    ⚡ APROVEITAR OFERTA
                </a>
                <button class="btn-share" onclick="compartilharWhatsApp(\`${textoWhatsApp.replace(/`/g, "'")}\`)">
                    <i class="fab fa-whatsapp"></i>
                </button>
            </div>
        </article>
    `;
}

function calcularTempoAtras(timestamp) {
    const agora = new Date();
    const data = new Date(timestamp);
    const diffMs = agora - data;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHoras = Math.floor(diffMin / 60);

    if (diffMin < 1) return 'Agora';
    if (diffMin < 60) return `Há ${diffMin} min`;
    if (diffHoras < 24) return `Há ${diffHoras}h`;
    return `Há ${Math.floor(diffHoras / 24)} dias`;
}

window.copiarCupom = function(cupom) {
    navigator.clipboard.writeText(cupom);
    alert('Cupom copiado: ' + cupom);
};

window.compartilharWhatsApp = function(texto) {
    const url = 'https://api.whatsapp.com/send?text=' + encodeURIComponent(texto);
    window.open(url, '_blank');
};

window.mostrarTodasPromocoes = function() {
    mostrandoTodas = true;
    renderizarPromocoes();
};