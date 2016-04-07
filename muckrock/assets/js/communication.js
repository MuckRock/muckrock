function showCommForm(id) {
    if (!id) {
        return;
    }
    var form = $(id);
    $('.options.dropdown').removeClass('visible');
    $('.communication-actions').show();
    form.addClass('visible').siblings().removeClass('visible');
    form.find('button.cancel').click(function(e){
        e.preventDefault();
        $(id).removeClass('visible');
        $('.communication-actions').hide();
    });
}

$('.communication-header').click(function(){
    $(this).closest('.communication').toggleClass('collapsed');
});

$('.communication-header .dropdown-list').click(function(event){
    // Prevent click from propagating up to the communication header.
    event.stopPropagation();
});

var actions = $('.communication-action').map(function() {
    return '#' + $(this).attr('id');
}).get();

// Bind to hashchange event
$(window).on('hashchange', function () {
    // check if the hash is a target
    var hash = location.hash;
    if (actions.indexOf(hash) !== -1) {
        showCommForm(hash);
    }
});

showCommForm(actions.indexOf(location.hash) !== -1 ? location.hash : '');
