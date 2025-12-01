/**
 * stateManager.js - Gerenciamento de estado da aplicação
 * Versão: 1.1.2
 * Última atualização: 11/05/2025
 * Autor: Em Casa com Cecília
 * 
 * Este arquivo contém funções para gerenciar o estado global da aplicação,
 * incluindo seleção de categorias, termos de busca e opções de ordenação.
 */

/**
 * Inicializa o estado da aplicação com valores padrão
 * @param {Object} elements - Referências aos elementos DOM importantes
 * @return {Object} Objeto de estado inicial
 */
export function initializeState(elements) {
        console.log('Inicializando estado...');
        const state = {
            selectedCategory: 'all',
            searchTerm: '',
        sortValue: 'default',
            elements: elements
        };

        // Verificar se os elementos existem antes de atribuir valores
        if (elements.searchInput) {
            elements.searchInput.value = state.searchTerm;
        } else {
            console.warn('Elemento searchInput não encontrado');
        }

        return state;
    }

/**
 * Atualiza o estado com novos valores
 * @param {Object} state - Estado atual
 * @param {Object} updates - Objeto com valores a serem atualizados
 * @return {Object} Novo objeto de estado
 */
    export function updateState(state, updates) {
        console.log('Atualizando estado:', updates);
        const newState = { ...state, ...updates };

        // Atualizar o valor do input de busca se o searchTerm mudar
        if (updates.searchTerm !== undefined && state.elements.searchInput) {
            state.elements.searchInput.value = updates.searchTerm;
        }

        return newState;
    }