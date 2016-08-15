/* list.js
**
** This handles the logic for displaying an UP or DOWN arrow on a list,
** depending on how it is sorted.
** It examines the query arguments to figure out where and how to place the arrow.
*/

function identifySortable() {
    $('.list-table-head th').each(function(){
        var sort = $(this).data('sort');
        if (typeof(sort) != "undefined") {
            $(this).addClass('sortable');
        }
    });
}

function tableHeadSortIndicator() {
    var sort = $('thead').data('activeSort');
    var order = $('thead').data('activeOrder');
    if (typeof(sort) != "undefined") {
        // find the right title and add the right arrow to it
        var arrow = (order == 'desc') ? '&#x25B2;' : '&#x25BC;';
        var inverseOrder = (order == 'desc') ? 'asc' : 'desc';
        $('th').each(function(){
            if ($(this).data('sort') == sort) {
                $(this).prepend('<span class="arrow">' + arrow + '</span>')
                       .data('order', inverseOrder)
                       .addClass('sorted_by');
            }
        });
    }
}

function sortListByHeader() {
    var sort = $(this).data('sort');
    var order = $(this).data('order');
    if (typeof(sort) != "undefined") {
        if (!order) {
            order = 'asc';
        }
        var existing = window.location.search;
        // check for existing sort and remove it if it exists
        // there will always be "?" or "&" before "sort"
        var existingSort = existing.indexOf('sort');
        if (existingSort > 0) {
            existing = existing.substring(0, existingSort - 1);
        }
        // add new sort and order
        // if adding to a filter use "&", otherwise use "?"
        var newSearch = existing.length > 0 ? existing + "&" : existing + "?";
        newSearch += "sort=" + sort;
        newSearch += "&order=" + order;
        window.location = window.location.origin + window.location.pathname + newSearch;
    }
}

identifySortable();
tableHeadSortIndicator();
$('.list-table-head th').click(sortListByHeader);

$('#list-filters-toggle').change(function(){
    var label = $('#list-filters-toggle-label')[0];
    if (this.checked) {
        label.innerText = 'Hide';
    } else {
        label.innerText = 'Show';
    }
});
