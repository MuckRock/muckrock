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
    const inverseOrder = (orderBy == 'desc') ? 'asc' : 'desc';
    $('.sortable th').filter((index, element) => {
      return $(element).data('sort') == sortBy;
    }).data('order', inverseOrder).addClass('sorted-by').addClass(orderBy);
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

// Prevent the active element in a list section from trigger a load on touch
$('.list__sections .current-tab a').on('click', function(e){
    e.preventDefault();
});

$(document).ready(() => {
  tableHeadSortIndicator();
  $('.sortable th').click(sortListByHeader);
  $('table.cardtable').cardtable();
});
