(function( $ ){

    var $crowdfund, $overlays, email;

    function gaEvent(category, action) {
        if (typeof(ga) != "undefined") {
            ga('send', 'event', category, action, window.location.pathname);
        }
    }

    function crowdfundAjax(event) {
        // Transform the form's data into a dictionary
        var form = $(this);
        var fields = form.serializeArray();
        var data = {};
        $(fields).map(function(index, field) {
            data[field.name] = field.value;
        });
        email = data['stripe_email'];
        // track this event using Google Analytics
        gaEvent('Crowdfund', 'Donation');
        // submit the form via AJAX
        $.ajax({
            url: form.attr('action'),
            type: form.attr('method'),
            data: data,
            beforeSend: showLoadingOverlay,
            error: showErrorOverlay,
            success: showSuccessOverlay,
            dataType: 'json'
        });
        // prevent the form from submitting itself
        event.preventDefault();
        return false;
    }

    function showOverlay(selector) {
        return $overlays.removeClass('visible').filter(selector).addClass('visible');
    }

    function showLoadingOverlay() {
        showOverlay('.pending');
    }

    function showErrorOverlay(response) {
        showOverlay('.error');
        var data = JSON.parse(response.responseText);
        $('#error-details').text(data.error);
    }

    function showSuccessOverlay(response) {
        var completeOverlay = showOverlay('.complete');
        $('.newsletter-widget #id_email').val(email);
        var nextStep;
        if (response.authenticated === false) {
            nextStep = 'Stay updated on our projects, reporting, and new requests by subscribing to our newsletter.';
        }
        else if (response.registered === true) {
            gaEvent('Account', 'Registration');
            nextStep = 'Welcome to MuckRock! Check your email to verify your address and set up your password.';
        }
        completeOverlay.find('#complete-next-steps').text(nextStep);
        $crowdfund.find('.donate button').attr('disabled', true);
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
