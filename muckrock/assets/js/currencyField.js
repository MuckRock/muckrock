/* currencyField.js
**
** A jQuery plugin for turning a simple number input into a logical currency input.
** Uses the autonumeric library to format the display of the currency value.
** When the currency value is changed, it also updates the value of the underlying number input.
** Assumes the value contained in the number input is a 1-cent delimited value, e.g. $1.00 -> 100
*/

import 'autonumeric';

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
        if (typeof(amount) === "undefined") {
            amount = 0;
        }
        // set up the currency field with attributes
        // and use the autoNumeric plugin on it
        $currency.attr('name', 'pretty-input').addClass('currency');
        $currency.autoNumeric('init', {aSign:'$', pSign:'p'});
        $currency.autoNumeric('set', amount/100.00);
        // we want to copy all the input to the currency field
        // back to the original amount field, since that is what
        // will ultimately be submitted
        function copyValue() {
            var value = ($currency.autoNumeric('get') * 100).toFixed(0);
            $input.val(value);
        }
        $currency.keyup(copyValue);
        copyValue();
        // swap out the input with the currency field
        $currency.insertBefore($input);
        $input.attr('hidden', true).hide();
        return $input;
   };
})( jQuery );
