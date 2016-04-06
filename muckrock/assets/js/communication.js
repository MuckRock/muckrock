export function showCommForm(selector) {
    $('.options.dropdown').removeClass('visible');
    $('.communication-actions').show();
    $(selector).addClass('visible').siblings().removeClass('visible');
    $(selector).find('button.cancel').click(function(e){
        e.preventDefault();
        $(selector).removeClass('visible');
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
