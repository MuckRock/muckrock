var identifySortable = function() {
    $('.list-table-head th').each(function(){
        if (!!$(this).data('sort')) {
            $(this).addClass('sortable');
        }
    });
}

var tableHeadSortIndicator = function() {
    var sort = urlParam('sort');
    if (!!sort) {
        // find the right title and add the right arrow to it
        var order = urlParam('order');
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

var sortListByHeader = function() {
    var sort = $(this).data('sort');
    var order = $(this).data('order');
    if (!!sort) {
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
        // check for filter
        var filterExists = false;
        if (existing.length > 0) {
            filterExists = true;
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
