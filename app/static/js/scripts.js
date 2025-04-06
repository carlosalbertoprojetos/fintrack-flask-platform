// // Scripts personalizados para o sistema de finanças pessoais

// document.addEventListener('DOMContentLoaded', function () {
//     // Inicializa tooltips do Bootstrap
//     var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
//     var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
//         return new bootstrap.Tooltip(tooltipTriggerEl);
//     });

//     // Função para formatar valores monetários
//     window.formatCurrency = function (value) {
//         return new Intl.NumberFormat('pt-BR', {
//             style: 'currency',
//             currency: 'BRL'
//         }).format(value);
//     };

//     const transactionTypeSelect = document.getElementById('transactionType');
//     const categorySelect = document.getElementById('categorySelect');
//     const expenseSelect = document.getElementById('expenseSelect');

//     if (transactionTypeSelect) {
//         transactionTypeSelect.addEventListener('change', function () {
//             updateCategoryOptions(this.value);
//         });

//         // Inicializa categorias ao carregar
//         if (transactionTypeSelect.value) {
//             updateCategoryOptions(transactionTypeSelect.value);
//         }
//     }

//     if (categorySelect) {
//         categorySelect.addEventListener('change', function () {
//             if (this.value) {
//                 updateExpenseOptions(this.value);
//             } else {
//                 expenseSelect.innerHTML = '<option value="">Selecione uma despesa</option>';
//             }
//         });

//         // Inicializa despesas ao carregar (caso edição)
//         const preselectedCategory = categorySelect.getAttribute('data-preselected');
//         if (preselectedCategory) {
//             updateExpenseOptions(preselectedCategory);
//         }
//     }

//     function updateCategoryOptions(transactionType) {
//         if (!categorySelect) return;

//         fetch(`/transactions/get_categories/${transactionType}`)
//             .then(response => response.json())
//             .then(data => {
//                 categorySelect.innerHTML = '<option value="">Selecione uma categoria</option>';

//                 data.categories.forEach(category => {
//                     const option = document.createElement('option');
//                     option.value = category.id;
//                     option.textContent = category.name;
//                     categorySelect.appendChild(option);
//                 });

//                 // Limpa as despesas após troca de categoria
//                 if (expenseSelect) {
//                     expenseSelect.innerHTML = '<option value="">Selecione uma despesa</option>';
//                 }
//             })
//             .catch(error => {
//                 console.error('Erro ao carregar categorias:', error);
//             });
//     }

//     function updateExpenseOptions(categoryId) {
//         if (!expenseSelect) return;

//         fetch(`/transactions/get_expenses/${categoryId}`)
//             .then(response => response.json())
//             .then(data => {
//                 expenseSelect.innerHTML = '<option value="">Selecione uma despesa</option>';

//                 data.forEach(expense => {
//                     const option = document.createElement('option');
//                     option.value = expense.id;
//                     option.textContent = expense.name;
//                     expenseSelect.appendChild(option);
//                 });
//             })
//             .catch(error => {
//                 console.error('Erro ao carregar despesas:', error);
//             });
//     }
// });
