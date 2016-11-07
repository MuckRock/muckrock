/* list.js
**
** This handles the logic for displaying an UP or DOWN arrow on a list,
** depending on how it is sorted.
** It examines the query arguments to figure out where and how to place the arrow.
*/

function tableHeadSortIndicator() {
  const sortBy = $('.sortable').data('sortBy');
  const orderBy = $('.sortable').data('orderBy');
  if (typeof(sortBy) != "undefined") {
    // find the right title and add the right arrow to it
    const arrowSymbol = (orderBy == 'desc') ? '&#x25B2;' : '&#x25BC;';
    const arrowElement = $('<span class="arrow">' + arrowSymbol + '</span>');
    const inverseOrder = (orderBy == 'desc') ? 'asc' : 'desc';
    $('.sortable th').filter((index, element) => {
      return $(element).data('sort') == sortBy;
    }).prepend(arrowElement).data('order', inverseOrder).addClass('sorted-by');
  }
}

function sortListByHeader() {
  const sort = $(this).data('sort');
  let order = $(this).data('order');
  if (typeof(sort) != "undefined") {
    order = typeof(order) == "undefined" ? 'asc' : order;
    let existing = window.location.search;
    // check for existing sort and remove it if it exists
    // there will always be "?" or "&" before "sort"
    const existingSort = existing.indexOf('sort');
    if (existingSort > 0) {
      existing = existing.substring(0, existingSort - 1);
    }
    // add new sort and order
    // if adding to a filter use "&", otherwise use "?"
    let newSearch = existing.length > 0 ? existing + "&" : existing + "?";
    newSearch += "sort=" + sort;
    newSearch += "&order=" + order;
    window.location = window.location.origin + window.location.pathname + newSearch;
  }
}

const toolbar = $('.toolbar :button, .toolbar :input');
function disableToolbar() {
    toolbar.attr('disabled', true).closest('.field').addClass('disabled');
}
function enableToolbar() {
    toolbar.attr('disabled', false).closest('.field').removeClass('disabled');
}
$('th input:checkbox').change(function(){
    var table = $(this).closest('table');
    var headerCheckbox = $(this);
    var bodyCheckboxes = $(table).find('td input:checkbox');
    var checked = headerCheckbox.checked;
    bodyCheckboxes.each(function(){
        this.checked = checked;
    });
    if (checked) {
        enableToolbar();
    } else {
        disableToolbar();
    }
});
$('td input:checkbox').change(function(){
    var table = $(this).closest('table');
    var headerCheckbox = $(table).find('th input:checkbox');
    var bodyCheckboxes = $(table).find('td input:checkbox');
    var checkedBoxes = bodyCheckboxes.filter(':checked');
    if (checkedBoxes.length == bodyCheckboxes.length) {
        headerCheckbox[0].indeterminate = false;
        headerCheckbox[0].checked = true;
    } else {
        headerCheckbox[0].indeterminate = true;
    }
    if (checkedBoxes.length == 0) {
        headerCheckbox[0].indeterminate = false;
        headerCheckbox[0].checked = false;
        disableToolbar();
    } else {
        enableToolbar();
    }
});

$(document).ready(() => {
  tableHeadSortIndicator();
  disableToolbar();
  $('.sortable th').click(sortListByHeader);
});
