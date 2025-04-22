// Sidebar toggle
const hamBurger = document.querySelector(".toggle-btn");
const sidebar = document.querySelector("#sidebar");

// Check localStorage for the sidebar state
document.addEventListener("DOMContentLoaded", function () {
  const isExpanded = localStorage.getItem("sidebar-expanded");

  // Disable transition for page load
  sidebar.style.transition = "none";

  // Apply the saved state
  if (isExpanded === "true") {
    sidebar.classList.add("expand");
  } else {
    sidebar.classList.remove("expand");
  }

  // Re-enable the transition after a short delay
  setTimeout(function() {
    sidebar.style.transition = "";
  }, 10); // small delay to ensure transition is applied after load

  addPagination();
});

// Toggle sidebar and save the state to localStorage
hamBurger.addEventListener("click", function () {
  sidebar.classList.toggle("expand");

  // Save the current state in localStorage
  const isExpanded = sidebar.classList.contains("expand");
  localStorage.setItem("sidebar-expanded", isExpanded);
});

// Check localStorage for any previously expanded element
document.addEventListener('DOMContentLoaded', function () {
  const sidebarDropdowns = document.querySelectorAll('.sidebar-dropdown');

  const expandedDropdownId = localStorage.getItem('expandedDropdown');

  // Loop through each dropdown element
  sidebarDropdowns.forEach(function (dropdown) {
      // If the stored dropdown ID matches the current dropdown, expand it
      if (dropdown.id === expandedDropdownId) {
          dropdown.classList.add('show');
      }

      // Add event listener to track when a dropdown is expanded or collapsed
      dropdown.addEventListener('shown.bs.collapse', function () {
          // Save the expanded dropdown's ID in localStorage
          localStorage.setItem('expandedDropdown', dropdown.id);
      });

      dropdown.addEventListener('hidden.bs.collapse', function () {
          // If the dropdown is collapsed, remove it from localStorage
          localStorage.removeItem('expandedDropdown');
      });
  });
});

// unfinished function to update tables without page refresh
async function loadTable() {
  const response = await fetch('/load_table', {
    method: 'POST',
    headers: {'Content-Type': 'application/json;'},
  })
  const data = await response.json();
  console.log(data);
}

function addPagination() {
  const paginationTop = document.getElementById('tablePaginationTop');
  const paginationBottom = document.getElementById('tablePaginationBottom');

  // Copy the content from paginationTop to paginationBottom
  paginationBottom.innerHTML = paginationTop.innerHTML;
  };

// Update the filter button link as the search input is updated
// Also allows for "clicking" the search button by pressing enter
document.addEventListener('DOMContentLoaded', function () {
  let table_search_input = document.getElementById('table-search');
  let filter_button = document.getElementById('filterButton');

  // Set the input value to the current search parameter value on page load
  let currentHref = filter_button.getAttribute('href');
  let searchParamMatch = currentHref.match(/search=([^&]*)/);
  if (searchParamMatch) {
    table_search_input.value = searchParamMatch[1];
  }

  table_search_input.oninput = function () {
    let href = filter_button.getAttribute('href');
    let newSearchValue = table_search_input.value;

    // Use regex to replace the search parameter value
    let updatedHref = href.replace(/(search=)[^&]*/, `$1${newSearchValue}`);

    filter_button.setAttribute('href', updatedHref);
  }

  table_search_input.addEventListener('keypress', function (event) {
    if (event.key === 'Enter') {
      filter_button.click();
    }
  });
});