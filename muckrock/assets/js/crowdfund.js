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

    function crowdfundEmbed(event) {
        var trigger = $(this);
        var overlays = trigger.parents('.crowdfund').children('.overlay');
        var overlay = overlays.filter('.embed').addClass('visible');
        overlay.find('#hide-embed').click(()=>{
            overlay.removeClass('visible');
        });
    }

    function crowdfundShare(event) {
        var trigger = $(this);
        var overlays = trigger.parents('.crowdfund').children('.overlay');
        var overlay = overlays.filter('.share').addClass('visible');
        overlay.find('#hide-share').click(()=>{
            overlay.removeClass('visible');
        });
    }

    function closeCompleteOverlay(event) {
        var overlays = $(this).parents('.crowdfund').children('.overlay');
        overlays.filter('.complete').removeClass('visible');
    }

    $.fn.crowdfund = function() {
        $(this).find('.crowdfund-form').submit(crowdfundAjax);
        $(this).find('#show-embed').click(crowdfundEmbed);
        $(this).find('#show-share').click(crowdfundShare);
        $(this).find('#hide-complete').click(closeCompleteOverlay);
    };

})( jQuery );
