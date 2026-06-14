const sortLabels = {
    new: "New",
    old: "Old",
    views: "Views",
    likes: "Likes"
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

function getPredefinedRangeName(startDate, endDate) {
    // Check against predefined ranges
    const ranges = {
        'Last 24 Hours': [moment().subtract(24, 'hours'), moment()],
        'Last 7 Days': [moment().subtract(6, 'days'), moment()],
        'Last 30 Days': [moment().subtract(29, 'days'), moment()],
        'Last 1 Year': [moment().subtract(1, 'year'), moment()],
        'All Time': [moment('2000-01-01'), moment()]
    };
    
    for (const [name, [rangeStart, rangeEnd]] of Object.entries(ranges)) {
        if (startDate.format('YYYY-MM-DD') === rangeStart.format('YYYY-MM-DD') && 
            endDate.format('YYYY-MM-DD') === rangeEnd.format('YYYY-MM-DD')) {
            return name;
        }
    }
    return null;
}

function initDaterangepicker() {
    if (!(window.jQuery && typeof jQuery().daterangepicker === 'function')) return;
    const daterangeInput = $('#daterange');
    if (daterangeInput.length === 0) return;
    
    // Define default date range (last 7 days)
    const defaultStartDate = moment().subtract(6, 'days');
    const defaultEndDate = moment();
    
    // Check URL params for existing timeframe
    const urlParams = new URLSearchParams(window.location.search);
    const timeframeParam = urlParams.get('timeframe');
    
    let startDate = defaultStartDate;
    let endDate = defaultEndDate;
    let displayText = 'Last 7 Days'; // Default display
    
    // Map timeframe values to display names
    const timeframeDisplayMap = {
        '24h': 'Last 24 Hours',
        '7d': 'Last 7 Days',
        '30d': 'Last 30 Days',
        '1y': 'Last 1 Year',
        'all': 'All Time'
    };
    
    // Map timeframe values to date ranges
    const timeframeRangeMap = {
        '24h': [moment().subtract(24, 'hours'), moment()],
        '7d': [moment().subtract(6, 'days'), moment()],
        '30d': [moment().subtract(29, 'days'), moment()],
        '1y': [moment().subtract(1, 'year'), moment()],
        'all': [moment('2000-01-01'), moment()]
    };
    
    // Restore from timeframe param if present
    if (timeframeParam) {
        if (timeframeParam.startsWith('custom:')) {
            // Handle custom date range: custom:YYYY-MM-DD|YYYY-MM-DD
            try {
                const dateRange = timeframeParam.substring(7); // Skip 'custom:'
                const [start, end] = dateRange.split('|');
                const parsedStart = moment(start, 'YYYY-MM-DD');
                const parsedEnd = moment(end, 'YYYY-MM-DD');
                if (parsedStart.isValid() && parsedEnd.isValid()) {
                    startDate = parsedStart;
                    endDate = parsedEnd;
                    displayText = startDate.format('YYYY-MM-DD') + ' - ' + endDate.format('YYYY-MM-DD');
                }
            } catch (e) {}
        } else if (timeframeDisplayMap[timeframeParam]) {
            // Handle predefined ranges
            const range = timeframeRangeMap[timeframeParam];
            startDate = range[0];
            endDate = range[1];
            displayText = timeframeDisplayMap[timeframeParam];
        }
    }
    
    // Destroy previous instance if it exists
    try {
        daterangeInput.data('daterangepicker').remove();
    } catch (e) {}
    
    daterangeInput.daterangepicker({
        "startDate": startDate,
        "endDate": endDate,
        "showDropdowns": true,
        ranges: {
            'Last 24 Hours': [moment().subtract(24, 'hours'), moment()],
            'Last 7 Days': [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'Last 1 Year': [moment().subtract(1, 'year'), moment()],
            'All Time': [moment('2000-01-01'), moment()]
        },
        "locale": {
            "format": "YYYY-MM-DD",
            "separator": " - ",
            "applyLabel": "Apply",
            "cancelLabel": "Cancel",
            "fromLabel": "From",
            "toLabel": "To",
            "customRangeLabel": "Custom",
            "weekLabel": "W",
            "daysOfWeek": ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"],
            "monthNames": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
            "firstDay": 1
        },
        "alwaysShowCalendars": true
    });
    
    // Set initial display text
    daterangeInput.val(displayText);
    
    // Store the current state for cancel handler
    let lastAppliedStartDate = startDate.clone();
    let lastAppliedEndDate = endDate.clone();
    let lastAppliedDisplayText = displayText;
    
    // Update hidden input and URL when date range is changed
    daterangeInput.on('apply.daterangepicker', function(ev, picker) {
        // Check if it's a predefined range or custom
        const predefinedName = getPredefinedRangeName(picker.startDate, picker.endDate);
        const displayText = predefinedName || picker.startDate.format('YYYY-MM-DD') + ' - ' + picker.endDate.format('YYYY-MM-DD');
        daterangeInput.val(displayText);
        
        // Store the applied state
        lastAppliedStartDate = picker.startDate.clone();
        lastAppliedEndDate = picker.endDate.clone();
        lastAppliedDisplayText = displayText;
        
        // Map predefined ranges to timeframe values
        const timeframeMap = {
            'Last 24 Hours': '24h',
            'Last 7 Days': '7d',
            'Last 30 Days': '30d',
            'Last 1 Year': '1y',
            'All Time': 'all'
        };
        
        let timeframeValue;
        if (predefinedName) {
            timeframeValue = timeframeMap[predefinedName];
        } else {
            // Custom range: encode as custom:YYYY-MM-DD|YYYY-MM-DD
            timeframeValue = 'custom:' + picker.startDate.format('YYYY-MM-DD') + '|' + picker.endDate.format('YYYY-MM-DD');
        }
        document.getElementById('timeframe-input').value = timeframeValue;
        updateUrlParam('timeframe', timeframeValue);
        
        submitFilterForm();
    });
    
    // Restore state when cancel is clicked or when the picker is hidden without applying
    daterangeInput.on('cancel.daterangepicker', function(ev, picker) {
        picker.setStartDate(lastAppliedStartDate);
        picker.setEndDate(lastAppliedEndDate);
        daterangeInput.val(lastAppliedDisplayText);
    });
    daterangeInput.on('hide.daterangepicker', function(ev, picker) {
        picker.setStartDate(lastAppliedStartDate);
        picker.setEndDate(lastAppliedEndDate);
        daterangeInput.val(lastAppliedDisplayText);
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
    if (sortLabels[initialSort]) {
        document.getElementById('sortDropdown').innerText = sortLabels[initialSort];
    }

    initSelectPickers();
    initDaterangepicker();
});

document.body.addEventListener('htmx:afterSwap', function (evt) {
    initSelectPickers();
    initDaterangepicker();
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

    // Reset daterange picker to default
    if (window.jQuery && typeof jQuery().daterangepicker === 'function') {
        try { $('#daterange').data('daterangepicker').remove(); } catch(e) {}
        initDaterangepicker();
    }

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