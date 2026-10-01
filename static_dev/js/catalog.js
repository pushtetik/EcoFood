document.addEventListener('DOMContentLoaded', function() {
    console.log('Catalog script loaded');
    
    // Элементы DOM
    const searchInput = document.getElementById('searchInput');
    const categoryCheckboxes = document.querySelectorAll('.category-checkbox');
    const mobileCategoryCheckboxes = document.querySelectorAll('.mobile-category-checkbox');
    const sortSelect = document.getElementById('sortSelect');
    const productsGrid = document.getElementById('productsGrid');
    const productCards = document.querySelectorAll('.product-card');
    const noProductsMessage = document.getElementById('noProductsMessage');
    const mobileCategoriesToggle = document.getElementById('mobileCategoriesToggle');
    const mobileCategoriesContent = document.getElementById('mobileCategoriesContent');
    
    // Элемент для отображения количества товаров
    const productsCountElement = document.querySelector('.filters-topbar h5');
    
    // Сохраняем исходный порядок товаров
    const originalOrder = Array.from(productCards);
    let currentOrder = Array.from(productCards);
    
    // Инициализация
    initMobileCategories();
    initEventListeners();
    filterProducts();
    
    // Функция инициализации мобильных категорий
    function initMobileCategories() {
        // Переключение мобильных категорий
        if (mobileCategoriesToggle) {
            mobileCategoriesToggle.addEventListener('click', function() {
                this.classList.toggle('active');
                mobileCategoriesContent.classList.toggle('show');
            });
        }
        
        // Обработка выбора категорий на мобильных
        const mobileCategoryItems = document.querySelectorAll('.mobile-category-item');
        mobileCategoryItems.forEach(item => {
            const checkbox = item.querySelector('.mobile-category-checkbox');
            const label = item.querySelector('.mobile-category-label');
            
            // Обработка клика на весь элемент
            item.addEventListener('click', function(e) {
                if (e.target.type === 'checkbox' || e.target.tagName === 'INPUT') return;
                
                checkbox.checked = !checkbox.checked;
                updateCategorySelection(this, checkbox.checked);
                
                // Синхронизируем с десктопными чекбоксами
                syncWithDesktopCategories(checkbox.value, checkbox.checked);
                
                // Фильтруем товары
                filterProducts();
            });
            
            // Обработка клика на чекбокс
            checkbox.addEventListener('change', function() {
                updateCategorySelection(item, this.checked);
                
                // Синхронизируем с десктопными чекбоксами
                syncWithDesktopCategories(this.value, this.checked);
                
                // Фильтруем товары
                filterProducts();
            });
            
            // Обработка клика на label
            label.addEventListener('click', function(e) {
                e.preventDefault();
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            });
        });
    }
    
    // Функция инициализации обработчиков событий
    function initEventListeners() {
        // Обработчик для чекбокса "Все категории"
        const allCategoryCheckbox = document.getElementById('category-all');
        if (allCategoryCheckbox) {
            allCategoryCheckbox.addEventListener('change', function() {
                const isChecked = this.checked;
                
                // Устанавливаем состояние для всех десктопных чекбоксов категорий
                categoryCheckboxes.forEach(checkbox => {
                    if (checkbox.id !== 'category-all') {
                        checkbox.checked = isChecked;
                    }
                });
                
                // Синхронизируем с мобильными чекбоксами
                mobileCategoryCheckboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                    const mobileItem = checkbox.closest('.mobile-category-item');
                    if (mobileItem) {
                        updateCategorySelection(mobileItem, isChecked);
                    }
                });
                
                filterProducts();
            });
        }
        
        // Обработчики для отдельных десктопных категорий
        categoryCheckboxes.forEach(checkbox => {
            if (checkbox.id !== 'category-all') {
                checkbox.addEventListener('change', function() {
                    // Синхронизируем с мобильными чекбоксами
                    const mobileCheckbox = document.querySelector(`.mobile-category-checkbox[value="${this.value}"]`);
                    if (mobileCheckbox) {
                        const mobileItem = mobileCheckbox.closest('.mobile-category-item');
                        mobileCheckbox.checked = this.checked;
                        updateCategorySelection(mobileItem, this.checked);
                    }
                    
                    updateAllCategoriesCheckbox();
                    filterProducts();
                });
            }
        });
        
        // Обработчики для поиска и сортировки
        if (searchInput) searchInput.addEventListener('input', filterProducts);
        if (sortSelect) sortSelect.addEventListener('change', filterProducts);
    }
    
    // Функция обновления визуального состояния категории
    function updateCategorySelection(item, isChecked) {
        if (!item) return;
        
        if (isChecked) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    }
    
    // Функция синхронизации с десктопными категориями
    function syncWithDesktopCategories(categoryValue, isChecked) {
        const desktopCheckbox = document.getElementById(`category-${categoryValue}`);
        if (desktopCheckbox) {
            desktopCheckbox.checked = isChecked;
        }
        updateAllCategoriesCheckbox();
    }
    
    // Функция обновления чекбокса "Все категории"
    function updateAllCategoriesCheckbox() {
        const allCategoryCheckbox = document.getElementById('category-all');
        const allMobileCategoryCheckbox = document.getElementById('mobile-category-all');
        
        if (!allCategoryCheckbox || !allMobileCategoryCheckbox) return;
        
        // Проверяем десктопные чекбоксы
        const otherCheckboxes = Array.from(categoryCheckboxes).filter(cb => cb.id !== 'category-all');
        const allChecked = otherCheckboxes.every(cb => cb.checked);
        const anyChecked = otherCheckboxes.some(cb => cb.checked);
        
        // Обновляем десктопный чекбокс "Все категории"
        if (allChecked) {
            allCategoryCheckbox.checked = true;
            allCategoryCheckbox.indeterminate = false;
        } else if (anyChecked) {
            allCategoryCheckbox.checked = false;
            allCategoryCheckbox.indeterminate = true;
        } else {
            allCategoryCheckbox.checked = false;
            allCategoryCheckbox.indeterminate = false;
        }
        
        // Обновляем мобильный чекбокс "Все категории"
        const mobileCheckboxes = document.querySelectorAll('.mobile-category-checkbox');
        if (mobileCheckboxes.length > 0 && allMobileCategoryCheckbox) {
            let allMobileChecked = true;
            mobileCheckboxes.forEach(cb => {
                if (cb.value !== 'all' && !cb.checked) {
                    allMobileChecked = false;
                }
            });
            
            allMobileCategoryCheckbox.checked = allMobileChecked;
            const allMobileItem = allMobileCategoryCheckbox.closest('.mobile-category-item');
            updateCategorySelection(allMobileItem, allMobileChecked);
        }
    }
    
    // Функция получения выбранных категорий
    function getSelectedCategories() {
        const allCategoryChecked = document.getElementById('category-all')?.checked;
        
        if (allCategoryChecked) {
            return [];
        }
        
        return Array.from(categoryCheckboxes)
            .filter(cb => cb.checked && cb.id !== 'category-all')
            .map(cb => cb.value);
    }
    
    // Основная функция фильтрации
    function filterProducts() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const selectedCategories = getSelectedCategories();
        const sortValue = sortSelect ? sortSelect.value : 'default';
        
        console.log('Filtering products:', { searchTerm, selectedCategories, sortValue });
        
        // Фильтруем карточки
        let filteredCards = Array.from(productCards).filter(card => {
            const productName = card.getAttribute('data-name');
            const productCategory = card.getAttribute('data-category');
            
            // Проверка поискового запроса
            const matchesSearch = searchTerm === '' || 
                                productName.includes(searchTerm);
            
            // Проверка категории
            const matchesCategory = selectedCategories.length === 0 || 
                                  selectedCategories.includes(productCategory);
            
            return matchesSearch && matchesCategory;
        });
        
        console.log('Filtered cards count:', filteredCards.length);
        
        // Сортируем отфильтрованные карточки
        sortFilteredProducts(filteredCards, sortValue);
        
        // Обновляем отображение
        updateVisibleProducts(filteredCards);
        
        // Показываем/скрываем сообщение "нет товаров"
        if (noProductsMessage && productsGrid) {
            if (filteredCards.length === 0) {
                noProductsMessage.classList.remove('d-none');
                productsGrid.classList.add('d-none');
            } else {
                noProductsMessage.classList.add('d-none');
                productsGrid.classList.remove('d-none');
            }
        }
    }
    
    // Функция обновления видимых товаров (показывает все)
    function updateVisibleProducts(filteredCards) {
        // Сначала скрываем все товары
        productCards.forEach(card => {
            card.style.display = 'none';
        });
        
        // Показываем все отфильтрованные карточки
        filteredCards.forEach(card => {
            card.style.display = 'flex';
        });
        
        // Обновляем общий счетчик
        if (productsCountElement) {
            productsCountElement.textContent = `Товары (${filteredCards.length})`;
        }
    }
    
    // Функция сортировки отфильтрованных товаров
    function sortFilteredProducts(filteredCards, sortValue) {
        if (sortValue === 'default') {
            // Восстанавливаем исходный порядок из оригинального массива
            const sortedCards = [];
            
            // Проходим по исходному порядку и добавляем только отфильтрованные карточки
            originalOrder.forEach(card => {
                if (filteredCards.includes(card)) {
                    sortedCards.push(card);
                }
            });
            
            filteredCards = sortedCards;
        } else {
            // Сортируем по выбранному критерию
            filteredCards.sort((a, b) => {
                const aName = a.getAttribute('data-name');
                const bName = b.getAttribute('data-name');
                const aPrice = parseFloat(a.getAttribute('data-price'));
                const bPrice = parseFloat(b.getAttribute('data-price'));
                
                switch (sortValue) {
                    case 'price-asc':
                        return aPrice - bPrice;
                    case 'price-desc':
                        return bPrice - aPrice;
                    case 'name-asc':
                        return aName.localeCompare(bName, 'ru');
                    case 'name-desc':
                        return bName.localeCompare(aName, 'ru');
                    default:
                        return 0;
                }
            });
        }
        
        // Обновляем DOM с новым порядком
        if (productsGrid) {
            filteredCards.forEach(card => {
                productsGrid.appendChild(card);
            });
        }
        
        // Обновляем текущий порядок
        currentOrder = filteredCards;
    }
    
    // Инициализация начального состояния
    setTimeout(() => {
        console.log('Initial catalog state loaded');
        // Показываем все товары при загрузке
        updateVisibleProducts(Array.from(productCards));
    }, 100);
});