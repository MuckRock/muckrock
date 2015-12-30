//
// Provides interface logic for the crowdfunding payment form
// Depends on Stripe Checkout
//

var form = '.crowdfund-form';
var amount = 'input[name=amount]';
var button = '.crowdfund-form #crowdfund-button';
var prettyInput = 'input[name=pretty-input]';

function submitForm(form) {

    // track this event using Google Analytics
    ga('send', 'event', 'Crowdfund', 'Donation', window.location.pathname);

    var c = $(form).parents('.crowdfund');
    var pendingOverlay = $(c).children('.pending.overlay');
    var completeOverlay = $(c).children('.complete.overlay');
    var errorOverlay = $(c).children('.error.overlay');

    var formFields = $(form).serializeArray();
    var data = {};
    for (var i = 0; i < formFields.length; i++) {
        var field = formFields[i];
        data[field.name] = field.value;
    }

    $(document).ajaxStart(function(){
        $(pendingOverlay).addClass('visible');
    }).ajaxError(function(){
        $(pendingOverlay).removeClass('visible');
        $(errorOverlay).addClass('visible');
        $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
    }).ajaxComplete(function(e){
        $(pendingOverlay).removeClass('visible');
        $(completeOverlay).addClass('visible');
        $(document).off('ajaxStart').off('ajaxError').off('ajaxComplete');
    });

    $.ajax({
        url: $(form).attr('action'),
        type: 'post',
        data: data,
        success: null,
        dataType: 'json'
    });
}

// Stripe (should figure out how to divorce this from the file)
function checkoutCrowdfund(crowdfund) {
    // Passes in the button that was clicked
    var b = $(crowdfund).find(button);
    var a = $(crowdfund).find(amount).val();
    if (!a) {
        return false;
    }
    var f = $(crowdfund).find(form);
    var key = b.data('key');
    var icon = b.data('icon');
    var email = b.data('email');
    var label = 'Contribute';
    var description = 'Contribute (' + $(prettyInput).val() + ')';
    var token = function(token) {
        f.append('<input type="hidden" name="token" value="' + token.id + '" />');
        f.append('<input type="hidden" name="email" value="' + token.email + '" />');
        submitForm(f);
    }
    StripeCheckout.open({
        key: key,
        image: icon,
        name: 'MuckRock',
        description: description,
        amount: a,
        bitcoin: true,
        email: email,
        panelLabel: label,
        token: token
    });
    return true;
}

prettifyAmountInput(amount);
$(button).click(function(e){
    // get the crowdfund associated with this button
    e.preventDefault();
    var crowdfund = $(this).closest('.crowdfund.widget');
    checkoutCrowdfund(crowdfund);
});
