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
    $(prettyInput).keyup(function(){
        toggleCrowdfundButton(prettyInput);
    });
    $(prettyInput).change(function(){
        formatMonies(prettyInput);
    });
}

function toggleCrowdfundButton(input) {
    var value = $(input).autoNumeric('get');
    var disabled = $(button).attr('disabled');
    var enable;
    if (value > 0) {
        $(button).attr('disabled', false);
        enable = true;
    } else {
        $(button).attr('disabled', true);
        enable = false;
    }
    if (disabled && enable) {
        $(button).removeClass('disabled').addClass('success');
    } else if (!disabled && !enable) {
        $(button).removeClass('success').addClass('disabled');
    }
}

function formatMonies(input) {
    var value = $(input).autoNumeric('get');
    value *= 100;
    if (value > 0) {
        var description = 'Contribute ($' + str(value) + ')';
        $(amount).attr('value', value);
        $(button).attr('data-amount', value);
        $(button).attr('data-description', description);
    } else {
        $(button).attr('disabled', true);
        $(button).removeClass('success').addClass('disabled');
    }
}
