// NOTIFICATIONS
var notificationCloseButton = $('.notification .dismiss .close');
notificationCloseButton.click(function(){
    $(this).closest('.notification').hide();
    if ($('.notifications').children(':visible').length == 0) {
        $('.notifications').hide();
    }
});
