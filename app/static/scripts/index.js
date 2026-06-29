const sortLabels = {
    new: "New",
    old: "Old",
    views: "Views",
    likes: "Likes"
};

const DateTime = window.luxon?.DateTime;

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
        'Last 24 Hours': [DateTime.now().minus({ hours: 24 }), DateTime.now()],
        'Last 7 Days': [DateTime.now().minus({ days: 6 }), DateTime.now()],
        'Last 30 Days': [DateTime.now().minus({ days: 29 }), DateTime.now()],
        'Last 1 Year': [DateTime.now().minus({ years: 1 }), DateTime.now()],
        'All Time': [DateTime.fromISO('2000-01-01'), DateTime.now()]
    };
    
    for (const [name, [rangeStart, rangeEnd]] of Object.entries(ranges)) {
        if (startDate.toFormat('yyyy-MM-dd') === rangeStart.toFormat('yyyy-MM-dd') && 
            endDate.toFormat('yyyy-MM-dd') === rangeEnd.toFormat('yyyy-MM-dd')) {
            return name;
        }
    }
    return null;
}

function initDaterangepicker() {
    if (typeof DateRangePicker === 'undefined' || typeof DateRangePicker.daterangepicker !== 'function') return;
    const daterangeInput = document.getElementById('daterange');
    if (!daterangeInput) return;

    const existingPicker = DateRangePicker.getDateRangePicker(daterangeInput);
    if (existingPicker && typeof existingPicker.remove === 'function') {
        existingPicker.remove();
    }

    const defaultStartDate = DateTime.now().minus({ days: 6 });
    const defaultEndDate = DateTime.now();

    const urlParams = new URLSearchParams(window.location.search);
    const timeframeParam = urlParams.get('timeframe');

    let startDate = defaultStartDate;
    let endDate = defaultEndDate;
    let displayText = 'Last 7 Days';

    const timeframeDisplayMap = {
        '24h': 'Last 24 Hours',
        '7d': 'Last 7 Days',
        '30d': 'Last 30 Days',
        '1y': 'Last 1 Year',
        'all': 'All Time'
    };

    const timeframeRangeMap = {
        '24h': [DateTime.now().minus({ hours: 24 }), DateTime.now()],
        '7d': [DateTime.now().minus({ days: 6 }), DateTime.now()],
        '30d': [DateTime.now().minus({ days: 29 }), DateTime.now()],
        '1y': [DateTime.now().minus({ years: 1 }), DateTime.now()],
        'all': [DateTime.fromISO('2000-01-01'), DateTime.now()]
    };

    if (timeframeParam) {
        if (timeframeParam.startsWith('custom:')) {
            try {
                const dateRange = timeframeParam.substring(7);
                const [start, end] = dateRange.split('|');
                const parsedStart = DateTime.fromISO(start);
                const parsedEnd = DateTime.fromISO(end);
                if (parsedStart.isValid && parsedEnd.isValid) {
                    startDate = parsedStart;
                    endDate = parsedEnd;
                    displayText = startDate.toFormat('yyyy-MM-dd') + ' - ' + endDate.toFormat('yyyy-MM-dd');
                }
            } catch (e) {}
        } else if (timeframeDisplayMap[timeframeParam]) {
            const range = timeframeRangeMap[timeframeParam];
            startDate = range[0];
            endDate = range[1];
            displayText = timeframeDisplayMap[timeframeParam];
        }
    }

    const options = {
        startDate,
        endDate,
        showDropdowns: true,
        ranges: {
            'Last 24 Hours': [DateTime.now().minus({ hours: 24 }), DateTime.now()],
            'Last 7 Days': [DateTime.now().minus({ days: 6 }), DateTime.now()],
            'Last 30 Days': [DateTime.now().minus({ days: 29 }), DateTime.now()],
            'Last 1 Year': [DateTime.now().minus({ years: 1 }), DateTime.now()],
            'All Time': [DateTime.fromISO('2000-01-01'), DateTime.now()]
        },
        locale: {
            format: 'yyyy-MM-dd',
            separator: ' - ',
            applyLabel: 'Apply',
            cancelLabel: 'Cancel',
            fromLabel: 'From',
            toLabel: 'To',
            customRangeLabel: 'Custom',
            weekLabel: 'W',
            daysOfWeek: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
            monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
            firstDay: 1
        },
        alwaysShowCalendars: true,
        autoUpdateInput: false
    };

    DateRangePicker.daterangepicker(daterangeInput, options);
    const pickerInput = DateRangePicker.getDateRangePicker(daterangeInput) ? daterangeInput : null;
    if (!pickerInput) return;

    daterangeInput.value = displayText;

    let lastAppliedStartDate = startDate;
    let lastAppliedEndDate = endDate;
    let lastAppliedDisplayText = displayText;

    const applyHandler = (ev) => {
        const picker = ev.picker || DateRangePicker.getDateRangePicker(daterangeInput);
        if (!picker) return;

        const predefinedName = getPredefinedRangeName(picker.startDate, picker.endDate);
        const newDisplayText = predefinedName || picker.startDate.toFormat('yyyy-MM-dd') + ' - ' + picker.endDate.toFormat('yyyy-MM-dd');
        daterangeInput.value = newDisplayText;
        lastAppliedStartDate = picker.startDate;
        lastAppliedEndDate = picker.endDate;
        lastAppliedDisplayText = newDisplayText;

        const timeframeMap = {
            'Last 24 Hours': '24h',
            'Last 7 Days': '7d',
            'Last 30 Days': '30d',
            'Last 1 Year': '1y',
            'All Time': 'all'
        };

        const timeframeValue = predefinedName ? timeframeMap[predefinedName] : 'custom:' + picker.startDate.toFormat('yyyy-MM-dd') + '|' + picker.endDate.toFormat('yyyy-MM-dd');
        document.getElementById('timeframe-input').value = timeframeValue;
        updateUrlParam('timeframe', timeframeValue);
        submitFilterForm();
    };

    const cancelHandler = () => {
        daterangeInput.value = lastAppliedDisplayText;
    };

    daterangeInput.addEventListener('apply', applyHandler);
    daterangeInput.addEventListener('cancel', cancelHandler);
    daterangeInput.addEventListener('hide', cancelHandler);
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
    initDaterangepicker();

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