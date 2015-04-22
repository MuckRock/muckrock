//
// Provides interface logic for the crowdfunding payment form
//

var form = '.crowdfund-form';
var amount = 'input[name=amount]';
var button = '.crowdfund-form .checkout-button';

prettifyAmountInput(amount);

function prettifyAmountInput(input) {
    // pretty_amount_input is used as a functional wrapper for the amount input field
    // progressive enhancement ftw!
    var prettyInputElement = '<input name="pretty-amount-input" placeholder="$5.00" class="success" id="pretty-amount-input">';
    var prettyInput = 'input[name=pretty-amount-input]';
    $(input).before(prettyInputElement);
    $(input).attr('hidden', true).hide();
    $(prettyInput).autoNumeric('init', {aSign:'$', pSign:'p'});
    $(prettyInput).change(function(){
        formatMonies(prettyInput);
    });
    $(button).click(function(e){
        e.preventDefault();
        if ($(prettyInput).val) {
            var checkoutData = getCheckoutData(button);
            checkout(
                "{{ stripe_pk }}",
                "/static/apple-touch-icon.png",
                checkoutData.description,
                checkoutData.amount,
                checkoutData.email,
                checkoutData.label,
                checkoutData.form
            );
            return false;
        } else {
            return false;
        }
    });
}

function formatMonies(input) {
    var value = $(input).autoNumeric('get');
    value *= 100;
    var string_val = $(input).val();
    if (value > 0) {
        var description = 'Contribute (' + string_val + ')';
        $(amount).attr('value', value);
        $(button).attr('data-amount', value);
        $(button).attr('data-description', description);
    } else {
        $(button).attr('disabled', true);
        $(button).removeClass('success').addClass('disabled');
    }
}

/* Stripe (should figure out how to divorce this from the file */

$('.checkout-button').click(function(e){
    e.preventDefault();

});

function checkout(pk, image, description, amount, email, label, form, submit) {
    submit = typeof submit !== 'undefined' ? submit : true;
    var token = function(token) {
        form.append('<input type="hidden" name="stripe_token" value="' + token.id + '" />');
        form.append('<input type="hidden" name="stripe_email" value="' + token.email + '" />');
        $('a').click(function() { return false; });
        $('button').click(function() { return false; });
        if (submit) {
            form.submit();
        }
    }
    StripeCheckout.open({
        key: pk,
        image: image,
        name: 'MuckRock',
        description: description,
        amount: amount,
        email: email,
        panelLabel: label,
        token: token,
        bitcoin: true
    });
}

function getCheckoutData(button) {
    button = $(button);
    var amount = button.data('amount');
    var description = button.data('description');
    var email = button.data('email');
    var form = button.data('form');
    var label = button.data('label');
    return {
        'amount': amount,
        'description': description,
        'email': email,
        'label': label,
        'form': $(form)
    }
}
