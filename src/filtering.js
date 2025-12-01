/**
 * filtering.js - Funções de filtragem e ordenação de produtos
 * Versão: 1.1.0
 * Última atualização: 03/05/2023
 * Autor: Em Casa com Cecília
 * 
 * Este arquivo contém funções para filtrar e ordenar produtos
 * com base em categorias, termos de busca e critérios de ordenação.
 */

/**
 * Filtra uma lista de produtos com base na categoria e termo de busca
 * @param {Array} products - Lista de elementos DOM representando produtos
 * @param {string} category - Categoria para filtrar ('all' para todas)
 * @param {string} searchTerm - Termo de busca para filtrar produtos
 * @return {Array} Lista filtrada de produtos
 */
export function filterProducts(products, category, searchTerm) {
    return products.filter(product => {
        const matchesCategory = category === 'all' || product.dataset.category === category;
        const matchesSearch = !searchTerm || 
            product.querySelector('h3').textContent.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesCategory && matchesSearch;
    });
}

/**
 * Ordena uma lista de produtos conforme critério especificado
 * @param {Array} products - Lista de elementos DOM representando produtos
 * @param {string} sortValue - Critério de ordenação (atualmente não utilizado)
 * @return {Array} Lista ordenada de produtos
 */
export function sortProducts(products, sortValue) {
    // Retorna uma cópia para evitar mutação do array original
    return [...products];
}