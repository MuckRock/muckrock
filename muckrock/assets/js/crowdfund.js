(function( $ ){

    function crowdfundAjax(event) {
        // get the form and the widget state overlays
        var form = $(this);
        var overlays = form.parents('.crowdfund').children('.overlay');

        var fields = form.serializeArray();
        var data = {};
        $(fields).map(function(index, field) {
            data[field.name] = field.value;
        });

        // track this event using Google Analytics
        if (typeof(ga) != "undefined") {
            ga('send', 'event', 'Crowdfund', 'Donation', window.location.pathname);
        }

        $(document).ajaxStart(function(){
            overlays.filter('.pending').addClass('visible');
        }).ajaxError(function(){
            overlays.filter('.pending').removeClass('visible');
            overlays.filter('.error').addClass('visible');
            $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
        }).ajaxComplete(function(){
            overlays.filter('.pending').removeClass('visible');
            overlays.filter('.complete').addClass('visible');
            $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
        });

        $.ajax({
            url: form.attr('action'),
            type: form.attr('method'),
            data: data,
            success: null,
            dataType: 'json'
        });

        event.preventDefault();
        return false;
    }

    $.fn.crowdfund = function() {
        $(this).submit(crowdfundAjax);
    };

})( jQuery );
