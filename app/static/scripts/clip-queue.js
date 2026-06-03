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
    const timeframe = document.getElementById('timeframe-select')?.value || '7d';
    const selectedBroadcasters = Array.from(document.getElementById('broadcasters-select').selectedOptions).map(opt => opt.value).join(',');
    const selectedCategory = document.getElementById('category-select').value;
    const selectedThemes = Array.from(document.getElementById('themes-select').selectedOptions).map(opt => opt.value).join(',');
    const selectedSubjects = Array.from(document.getElementById('subjects-select').selectedOptions).map(opt => opt.value).join(',');
    const selectedLayout = document.getElementById('layout-select').value;
    const searchValue = document.querySelector('input[name="search"]')?.value || '';
    const likedInput = document.getElementById('clip-queue-liked-input');
    const likedValue = likedInput ? likedInput.value : '0';
    updateUrlParam('sort', sort);
    updateUrlParam('timeframe', timeframe);
    updateUrlParam('broadcasters', selectedBroadcasters);
    updateUrlParam('category', selectedCategory);
    updateUrlParam('themes', selectedThemes);
    updateUrlParam('subjects', selectedSubjects);
    updateUrlParam('layout', selectedLayout);
    updateUrlParam('search', searchValue);
    updateUrlParam('liked', likedValue);
});