function updateUrlParam(key, value) {
    const url = new URL(window.location.href);

    url.searchParams.set(key, value);

    window.history.pushState(null, '', url.toString());
}

window.addEventListener('DOMContentLoaded', function() {
    const likedInput = document.getElementById('clip-queue-liked-input');
    const likedToggleBtn = document.getElementById('clip-queue-liked-toggle');
    if (likedInput && likedToggleBtn && likedInput.value === '1') {
        const icon = likedToggleBtn.querySelector('i');
        icon.classList.remove('fa-regular');
        icon.classList.add('fa-solid');
    }
});

document.getElementById('clip-queue-liked-toggle')?.addEventListener('click', function(e) {
    e.preventDefault();
    const input = document.getElementById('clip-queue-liked-input');
    const icon = this.querySelector('i');
    input.value = input.value === '1' ? '0' : '1';
    icon.classList.toggle('fa-regular');
    icon.classList.toggle('fa-solid');
});

document.getElementById('clip-queue-apply-filters-btn')?.addEventListener('click', function() {
    const sort = document.getElementById('sort-select')?.value || 'views';
    updateUrlParam('sort', sort);
    const timeframe = document.getElementById('timeframe-select')?.value || '7d';
    updateUrlParam('timeframe', timeframe);
    const broadcastersSelect = document.getElementById('broadcasters-select');
    if (broadcastersSelect) {
        const selectedBroadcasters = Array.from(broadcastersSelect.selectedOptions).map(opt => opt.value).join(',');
        updateUrlParam('broadcasters', selectedBroadcasters);
    }
    const categorySelect = document.getElementById('category-select');
    if (categorySelect) {
        const selectedCategory = categorySelect.value;
        updateUrlParam('category', selectedCategory);
    }
    const themesSelect = document.getElementById('themes-select');
    if (themesSelect) {
        const selectedThemes = Array.from(themesSelect.selectedOptions).map(opt => opt.value).join(',');
        updateUrlParam('themes', selectedThemes);
    }
    const subjectsSelect = document.getElementById('subjects-select');
    if (subjectsSelect) {
        const selectedSubjects = Array.from(subjectsSelect.selectedOptions).map(opt => opt.value).join(',');
        updateUrlParam('subjects', selectedSubjects);
    }
    const layoutSelect = document.getElementById('layout-select');
    if (layoutSelect) {
        const selectedLayout = layoutSelect.value;
        updateUrlParam('layout', selectedLayout);
    }
    const searchValue = document.querySelector('input[name="search"]')?.value || '';
    updateUrlParam('search', searchValue);
    const likedInput = document.getElementById('clip-queue-liked-input');
    const likedValue = likedInput ? likedInput.value : '0';
    updateUrlParam('liked', likedValue);
});