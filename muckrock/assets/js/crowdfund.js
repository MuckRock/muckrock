var crowdfundForm = $('#crowdfund-form');
var crowdfundAmountInput = $('#crowdfund-amount-input');
var crowdfundAmount = $('#crowdfund-amount');
var crowdfundButton = $('#crowdfund-button');
crowdfundAmountInput.autoNumeric('init', {aSign:'$', pSign:'p'});        
crowdfundAmountInput.keyup(function(){
    var amount = crowdfundAmountInput.autoNumeric('get');
    var disabled = crowdfundButton.attr('disabled');
    var enable;
    if (amount > 0) {
        crowdfundButton.attr('disabled', false);
        enable = true;
    } else {
        crowdfundButton.attr('disabled', true);
        enable = false;
    }
    if (disabled && enable) {
        crowdfundButton.removeClass('disabled').addClass('success');
    } else if (!disabled && !enable) {
        crowdfundButton.removeClass('success').addClass('disabled');
    }
});
crowdfundAmountInput.change(function(){
    var amount = crowdfundAmountInput.autoNumeric('get');
    amount *= 100;
    if (amount > 0) {
        crowdfundAmount.attr('value', amount);
        crowdfundButton.attr('data-amount', amount);
        var string = '$' + crowdfundAmountInput.autoNumeric('get');
        var description = 'Contribute (' + string + ')';
        crowdfundButton.attr('data-description', description);
    } else {
        crowdfundButton.attr('disabled', true);
        crowdfundButton.removeClass('success').addClass('disabled');
    }
});