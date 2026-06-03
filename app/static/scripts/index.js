const sortLabels = {
    new: "New",
    old: "Old",
    views: "Views",
    likes: "Likes"
};
const timeframeLabels = {
    "24h": "Last 24 Hours",
    "7d": "Last 7 Days",
    "30d": "Last 30 Days",
    "1y": "Last 1 Year",
    all: "All Time"
};

function submitFilterForm() {
    const form = document.getElementById('filter-form');
    if (!form) return;
    // prefer requestSubmit when available (fires submit handlers properly)
    if (typeof form.requestSubmit === 'function') {
        form.requestSubmit();
    } else {
        form.dispatchEvent(new Event('submit', { cancelable: true }));
    }
}

function initSelectPickers() {
    if (!(window.jQuery && typeof jQuery().selectpicker === 'function')) return;
    $('.selectpicker').each(function () {
        const $sel = $(this);
        // Destroy any previous instance to avoid duplicate generated DOM
        try { $sel.selectpicker('destroy'); } catch (e) {}
        // Initialize new selectpicker
        try { $sel.selectpicker(); } catch (e) {}
    });
}

function updateUrlParam(key, value) {
    const url = new URL(window.location.href);

    url.searchParams.set(key, value);

    window.history.pushState(null, '', url.toString());
}

window.addEventListener('DOMContentLoaded', function() {
    const likedInput = document.getElementById('hidden-liked-input');
    const likedToggleBtn = document.getElementById('liked-clips-toggle');
    if (likedInput && likedToggleBtn && likedInput.value === '1') {
        const icon = likedToggleBtn.querySelector('i');
        icon.classList.remove('fa-regular');
        icon.classList.add('fa-solid');
    }

    const initialSort = document.getElementById('sort-input')?.value || 'views';
    const initialTimeframe = document.getElementById('timeframe-input')?.value || '7d';
    if (sortLabels[initialSort]) {
        document.getElementById('sortDropdown').innerText = sortLabels[initialSort];
    }
    if (timeframeLabels[initialTimeframe]) {
        document.getElementById('timeframeDropdown').innerText = timeframeLabels[initialTimeframe];
    }

    initSelectPickers();
});

document.body.addEventListener('htmx:afterSwap', function (evt) {
    initSelectPickers();
});

document.querySelectorAll('.sort-btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        const sort = btn.getAttribute('data-sort');
        document.getElementById('sort-input').value = sort;
        document.getElementById('sortDropdown').innerText = sortLabels[sort] || "Sort By";
        updateUrlParam('sort', sort);
        submitFilterForm();
    });
});
document.querySelectorAll('.timeframe-btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        const timeframe = btn.getAttribute('data-timeframe');
        document.getElementById('timeframe-input').value = timeframe;
        document.getElementById('timeframeDropdown').innerText = timeframeLabels[timeframe] || "Timeframe";
        updateUrlParam('timeframe', timeframe);
        submitFilterForm();
    });
});
const broadcastersSelect = document.getElementById('broadcasters-select');
if (broadcastersSelect) {
    broadcastersSelect.addEventListener('change', function() {
        const selected = Array.from(this.selectedOptions).map(opt => opt.value).join(',');
        document.getElementById('broadcasters-input').value = selected;
        updateUrlParam('broadcasters', selected);
        submitFilterForm();
    });
}

const likedToggleBtn = document.getElementById('liked-clips-toggle');
if (likedToggleBtn) {
    likedToggleBtn.addEventListener('click', function() {
        const likedInput = document.getElementById('hidden-liked-input');
        const icon = this.querySelector('i');
        const currentValue = likedInput.value;
        const newValue = currentValue === '1' ? '0' : '1';
        
        likedInput.value = newValue;
        
        if (newValue === '1') {
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
        } else {
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
        }
        
        updateUrlParam('liked', newValue);
        submitFilterForm();
    });
}

document.getElementById('apply-advanced-filters').addEventListener('click', function() {
    const categorySelect = document.getElementById('category-select');
    if (categorySelect) {
        const selectedCategory = categorySelect.value;
        document.getElementById('hidden-category-input').value = selectedCategory;
        updateUrlParam('category', selectedCategory);
    }
    const themesSelect = document.getElementById('themes-select');
    if (themesSelect) {
        const selectedThemes = Array.from(themesSelect.selectedOptions).map(opt => opt.value).join(',');
        document.getElementById('hidden-themes-input').value = selectedThemes;
        updateUrlParam('themes', selectedThemes);
    }
    const subjectsSelect = document.getElementById('subjects-select');
    if (subjectsSelect) {
        const selectedSubjects = Array.from(subjectsSelect.selectedOptions).map(opt => opt.value).join(',');
        document.getElementById('hidden-subjects-input').value = selectedSubjects;
        updateUrlParam('subjects', selectedSubjects);
    }
    const layoutSelect = document.getElementById('layout-select');
    if (layoutSelect) {
        const selectedLayout = layoutSelect.value;
        document.getElementById('hidden-layout-input').value = selectedLayout;
        updateUrlParam('layout', selectedLayout);
    }
    submitFilterForm();
    var modal = bootstrap.Modal.getInstance(document.getElementById('advancedFilterModal'));
    modal.hide();
});

document.getElementById('filter-btn').addEventListener('click', function() {
    const searchValue = document.querySelector('input[name="search"]').value;
    updateUrlParam('search', searchValue);
});

document.getElementById('clear-filters-btn').addEventListener('click', function() {
    document.getElementById('sort-input').value = 'views';
    document.getElementById('sortDropdown').innerText = sortLabels['views'];
    document.getElementById('timeframe-input').value = '7d';
    document.getElementById('timeframeDropdown').innerText = timeframeLabels['7d'];
    document.getElementById('broadcasters-input').value = '';

    document.getElementById('hidden-category-input').value = '';
    document.getElementById('hidden-themes-input').value = '';
    document.getElementById('hidden-subjects-input').value = '';
    document.getElementById('hidden-layout-input').value = '';
    
    const likedInput = document.getElementById('hidden-liked-input');
    if (likedInput) {
        likedInput.value = '0';
    }

    // Reset liked button icon if button exists
    const likedToggleBtn = document.getElementById('liked-clips-toggle');
    if (likedToggleBtn) {
        const likedIcon = likedToggleBtn.querySelector('i');
        likedIcon.classList.remove('fa-solid');
        likedIcon.classList.add('fa-regular');
    }

    if (window.jQuery && typeof jQuery().selectpicker === 'function') {
        try { $('#broadcasters-select').selectpicker('val', []); } catch(e) {}
        try { $('#category-select').selectpicker('val', ''); } catch(e) {}
        try { $('#themes-select').selectpicker('val', []); } catch(e) {}
        try { $('#subjects-select').selectpicker('val', []); } catch(e) {}
        try { $('#layout-select').selectpicker('val', ''); } catch(e) {}
        try { $('.selectpicker').selectpicker('refresh'); } catch(e) {}
    } else {
        ['broadcasters-select','category-select','themes-select','subjects-select','layout-select'].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            Array.from(el.options).forEach(opt => opt.selected = false);
            el.value = '';
        });
    }

    document.querySelector('input[name="search"]').value = '';

    window.history.replaceState(null, '', window.location.pathname);
    updateUrlParam('sort', 'views');
    updateUrlParam('timeframe', '7d');
    submitFilterForm();
});

document.body.addEventListener('showLoginMessage', function(evt) {
    var toastEl = document.getElementById('loginToast');
    var toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 4000
    });
    toast.show();
});