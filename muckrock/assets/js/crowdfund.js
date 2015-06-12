//
// Provides interface logic for the crowdfunding payment form
// Depends on Stripe Checkout
//

var form = '.crowdfund-form';
var amount = 'input[name=amount]';
var button = '.crowdfund-form #crowdfund-button';
var prettyInput = 'input[name=pretty-input]';

function submitForm() {

    var f = $(form);
    var c = f.parents('.crowdfund');
    var overlay = c.children('.overlay');
    var formFields = f.serializeArray();
    var data = {};
    for (var i = 0; i < formFields.length; i++) {
      var field = formFields[i];
      data[field.name] = field.value;
    }
    $(document).ajaxStart(function(){
        overlay.removeClass('hidden');
        c.addClass('pending');
        overlay.empty();
        var heading = '<h1>Loading...</h1>';
        overlay.append(heading);
    }).ajaxComplete(function(){
        c.removeClass('pending').addClass('complete');
        overlay.empty();
        var heading = '<h1>Thank you!</h1>';
        overlay.append(heading);
    }).ajaxError(function(){
        c.removeClass('pending').addCLass('error');
        var heading = '<h1>Oops!</h1>';
        $(overlay).append(heading);
    });
    $.ajax({
        url: f.attr('action'),
        type: 'post',
        data: data,
        success: null,
        dataType: 'json'
    });
}

// Stripe (should figure out how to divorce this from the file
function checkoutCrowdfund(event) {
    event.preventDefault();
    var a = $(amount).val();
    if (!a) {
        return false;
    }

    var b = $(button);
    var f = $(form);
    var key = b.data('key');
    var icon = b.data('icon');
    var email = b.data('email');
    var label = 'Contribute';
    var description = 'Contribute (' + $(prettyInput).val() + ')';
    var token = function(token) {
        f.append('<input type="hidden" name="token" value="' + token.id + '" />');
        f.append('<input type="hidden" name="email" value="' + token.email + '" />');
        submitForm();

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

function prettifyAmountInput(input, pretty) {
    // pretty_amount_input is used as a functional wrapper for the amount input field
    // progressive enhancement ftw!
    $(input).attr('hidden', true).hide();
    var initialAmount = $(input).attr('value');
    var prettyInputElement = '<input name="pretty-input" class="success" >';
    $(input).before(prettyInputElement);
    $(pretty).autoNumeric('init', {aSign:'$', pSign:'p'});
    $(pretty).autoNumeric('set', initialAmount/100.00);
    $(pretty).keydown(function(e){
        var value = $(this).autoNumeric('get') * 100;
        $(input).attr('value', value);
    });
}

prettifyAmountInput(amount, prettyInput);
$(button).click(function(e){
    checkoutCrowdfund(e);
});
