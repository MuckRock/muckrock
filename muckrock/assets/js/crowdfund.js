(function( $ ){

    var $crowdfund, $overlays;

    function crowdfundAjax(event) {
        // Transform the form's data into a dictionary
        var form = $(this);
        var fields = form.serializeArray();
        var data = {};
        $(fields).map(function(index, field) {
            data[field.name] = field.value;
        });
        var email = data['stripe_email'];
        // track this event using Google Analytics
        if (typeof(ga) != "undefined") {
            ga('send', 'event', 'Crowdfund', 'Donation', window.location.pathname);
        }
        // bind AJAX events to the form to hide and show overlays
        $(document).ajaxStart(function(){
            $overlays.filter('.pending').addClass('visible');
        }).ajaxError(function(){
            $overlays.removeClass('visible').filter('.error').addClass('visible');
            $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
        }).ajaxComplete(function(){
            $overlays.removeClass('visible').filter('.complete').addClass('visible');
            $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
        });
        // submit the form via AJAX
        $.ajax({
            url: form.attr('action'),
            type: form.attr('method'),
            data: data,
            success: null,
            dataType: 'json'
        });
        // prevent the form from submitting itself
        event.preventDefault();
        return false;
    }

    function crowdfundEmbed() {
        $overlays.filter('.embed').addClass('visible').find('textarea').select();
    }

    function crowdfundShare() {
        $overlays.filter('.share').addClass('visible');
    }

    function crowdfundLogin() {
        $overlays.filter('.login').addClass('visible');
    }

    function toggleAccount() {
        var account = $crowdfund.find('.anonymity__account');
        var checkbox = $crowdfund.find('.anonymity #id_show');
        if (checkbox.is(':checked')) {
            account.show();
        } else {
            account.hide();
        }
    }

    function closeOverlay() {
        $overlays.removeClass('visible');
    }

    $.fn.crowdfund = function() {
        $crowdfund = $(this);
        $overlays = $crowdfund.children('.overlay');
        $crowdfund.find('.crowdfund-form').submit(crowdfundAjax);
        $crowdfund.find('#show-embed').click(crowdfundEmbed);
        $crowdfund.find('#show-share').click(crowdfundShare);
        $crowdfund.find('#show-login').click(crowdfundLogin);
        $crowdfund.find('.close').click(closeOverlay);
        $crowdfund.find('#id_show').change(toggleAccount);
        toggleAccount();
    };

})( jQuery );
