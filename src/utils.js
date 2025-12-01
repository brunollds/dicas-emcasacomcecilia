/**
 * utils.js - Funções de utilidade gerais
 * Versão: 1.1.0
 * Última atualização: 03/05/2023
 * Autor: Em Casa com Cecília
 * 
 * Funções de utilidade gerais para o site, incluindo debounce e eventos simulados.
 */

/**
 * Função de debouncing para limitar chamadas frequentes
 * Evita que uma função seja chamada várias vezes em um curto período de tempo
 * Útil para eventos como digitação na barra de pesquisa
 * 
 * @param {Function} func - Função a ser executada após o delay
 * @param {number} delay - Tempo de espera em milissegundos
 * @return {Function} Função com debounce aplicado
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        const context = this;
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(context, args), delay);
    };
}

/**
 * Função para simular clique em eventos de teclado
 * Usada para melhorar a acessibilidade, permitindo que usuários 
 * usem Enter ou Espaço para interagir com elementos clicáveis
 * 
 * @param {HTMLElement} element - Elemento a receber o clique simulado
 */
function simulateClick(element) {
    element.click();
}