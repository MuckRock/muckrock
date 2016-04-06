import 'autonumeric';

// A jQuery function for turning a number
// input into a pretty currency input.

(function( $ ){
    $.fn.currencyField = function() {
        if (this.length < 1) {
            return;
        }
        // we want to replace the input with a
        // currency input that automatically
        // formats and controls inputs
        var $input = $(this);
        var $currency = $('<input type="text"/>');
        var amount = $input.attr('value');
        // set up the currency field with attributes
        // and use the autoNumeric plugin on it
        $currency.attr('name', 'pretty-input').addClass('currency');
        $currency.autoNumeric('init', {aSign:'$', pSign:'p'});
        $currency.autoNumeric('set', amount/100.00);
        // we want to copy all the input to the currency field
        // back to the original amount field, since that is what
        // will ultimately be submitted
        function copyValue() {
            var value = $currency.autoNumeric('get') * 100;
            $input.attr('value', value);
        }
        $currency.keyup(copyValue);
        // swap out the input with the currency field
        $currency.insertBefore($input);
        $input.attr('hidden', true).hide();
        return $input;
   };
})( jQuery );
