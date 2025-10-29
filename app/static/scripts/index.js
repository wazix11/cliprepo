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

window.addEventListener('DOMContentLoaded', function() {
    const initialSort = "{{ sort|default('') }}";
    const initialTimeframe = "{{ timeframe|default('') }}";
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
        submitFilterForm();
    });
});
document.querySelectorAll('.timeframe-btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        const timeframe = btn.getAttribute('data-timeframe');
        document.getElementById('timeframe-input').value = timeframe;
        document.getElementById('timeframeDropdown').innerText = timeframeLabels[timeframe] || "Timeframe";
        submitFilterForm();
    });
});

document.getElementById('apply-advanced-filters').addEventListener('click', function() {
    document.getElementById('hidden-category-input').value = document.getElementById('category-select').value;
    document.getElementById('hidden-themes-input').value = Array.from(document.getElementById('themes-select').selectedOptions).map(opt => opt.value).join(',');
    document.getElementById('hidden-subjects-input').value = Array.from(document.getElementById('subjects-select').selectedOptions).map(opt => opt.value).join(',');
    document.getElementById('hidden-layout-input').value = document.getElementById('layout-select').value;
    submitFilterForm();
    var modal = bootstrap.Modal.getInstance(document.getElementById('advancedFilterModal'));
    modal.hide();
});

document.getElementById('clear-filters-btn').addEventListener('click', function() {
    document.getElementById('sort-input').value = 'views';
    document.getElementById('sortDropdown').innerText = sortLabels['views'];
    document.getElementById('timeframe-input').value = '7d';
    document.getElementById('timeframeDropdown').innerText = timeframeLabels['7d'];

    document.getElementById('hidden-category-input').value = '';
    document.getElementById('hidden-themes-input').value = '';
    document.getElementById('hidden-subjects-input').value = '';
    document.getElementById('hidden-layout-input').value = '';

    if (window.jQuery && typeof jQuery().selectpicker === 'function') {
        try { $('#category-select').selectpicker('val', ''); } catch(e) {}
        try { $('#themes-select').selectpicker('val', []); } catch(e) {}
        try { $('#subjects-select').selectpicker('val', []); } catch(e) {}
        try { $('#layout-select').selectpicker('val', ''); } catch(e) {}
        try { $('.selectpicker').selectpicker('refresh'); } catch(e) {}
    } else {
        ['category-select','themes-select','subjects-select','layout-select'].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            Array.from(el.options).forEach(opt => opt.selected = false);
            el.value = '';
        });
    }

    document.querySelector('input[name="search"]').value = '';
    submitFilterForm();
});