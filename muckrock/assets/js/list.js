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
        $('th:icontains(' + sort + ')')
            .prepend('<span class="arrow">' + arrow + '</span>')
            .data('order', inverseOrder)
            .addClass('sorted_by');
    }
}

var sortListByHeader = function() {
    var sort = $(this).data('sort');
    var order = $(this).data('order');
    if (!!sort) {
        if (!order) {
            order = 'asc';
        }
        var sort_url = '?sort=' + sort + '&order=' + order + '{{ filter_url|safe }}';
        window.location = window.location.origin + window.location.pathname + sort_url;
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
