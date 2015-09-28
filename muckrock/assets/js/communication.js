function showCommForm(selector) {
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

$('.communication-header').find('a').click(function(){
    window.location.href = $(this).attr('href');
    return false;
});

$('.communication-header').find('.dropdown-list').click(function(){
    return false;
});

$('.communication .options .svgIcon').click(function(){
    var thisDropdown = $(this).closest('.options.dropdown');
    var thisDropdownMenu = $(thisDropdown).find('.dropdown-list');
    var allOtherCommunications = $(thisDropdown).closest('.communication').siblings();
    var allOtherDropdowns = $(allOtherCommunications).find('.options.dropdown');
    $(allOtherDropdowns).removeClass('visible');
    $(thisDropdown).toggleClass('visible');
    $(document).click(function(e){
        $(thisDropdown).removeClass('visible');
    });
    return false;
});
