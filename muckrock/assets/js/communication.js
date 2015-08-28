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
    $(this).closest('.dropdown').toggleClass('visible');
    return false;
});
