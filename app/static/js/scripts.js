// Scripts personalizados para o sistema de finanças pessoais

document.addEventListener('DOMContentLoaded', function() {
    // Inicializa tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Função para formatar valores monetários
    window.formatCurrency = function(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    };
    
    // Atualiza o select de categorias com base no tipo de transação
    const transactionTypeSelect = document.getElementById('transactionType');
    if (transactionTypeSelect) {
        transactionTypeSelect.addEventListener('change', function() {
            updateCategoryOptions(this.value);
        });
        
        // Inicializa as categorias com base no tipo selecionado
        if (transactionTypeSelect.value) {
            updateCategoryOptions(transactionTypeSelect.value);
        }
    }
    
    function updateCategoryOptions(transactionType) {
        const categorySelect = document.getElementById('categorySelect');
        if (!categorySelect) return;
        
        // Fazer uma chamada AJAX para buscar as categorias filtradas
        fetch(`/transactions/categories/${transactionType}`)
            .then(response => response.json())
            .then(data => {
                // Limpa as opções atuais
                categorySelect.innerHTML = '';
                
                // Adiciona as novas opções
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    categorySelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Erro ao carregar categorias:', error);
            });
    }
});
