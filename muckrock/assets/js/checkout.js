/* checkout.js
**
** A jQuery plugin for handling the submission
** of forms that require a Stripe token.
** Tokens are obtained by using the Stripe Checkout library.
** When the form is submitted, we want to raise a Stripe Checkout window.
** The successful submission of this form will return a token, which we will
** add back to the form before resubmitting it.
*/

// This is used only for donations & crowdfunds now
// Once those have been ported to squarelet, this can be removed
(function( $ ){

    var $form = null;

    function formValue(name, newValue) {
        // Return the value of the form field matching the given name.
        // If a new value is given, set the value of the field before returning it.
        var selector = '[name=' + name + ']';
        var element = $form.find(selector);
        if (typeof newValue !== 'undefined') {
            element.val(newValue);
        }
        return element.val();
    }

    function handleToken(token) {
        // Set the value of the form's token and the email
        // fields based on the token received by this method
        formValue('stripe_token', token.id);
        formValue('stripe_email', token.email);
        // We submit the form once the token is in place.
        // As long as the token is added to the form,
        // it will submit successfully.
        $form.submit();
    }

    function handleCheckout() {
        var key         = formValue('stripe_pk'),
            image       = formValue('stripe_image'),
            label       = formValue('stripe_label'),
            description = formValue('stripe_description'),
            amount      = formValue('stripe_amount'),
            fee         = formValue('stripe_fee'),
            email       = formValue('stripe_email'),
            name        = 'MuckRock';
        amount = parseInt(amount);
        fee = parseFloat(fee);
        if (fee > 0) {
            amount += amount * fee;
        }
        var settings = {
            key: key,
            image: image,
            name: name,
            description: description,
            amount: amount,
            email: email,
            panelLabel: label,
            token: handleToken
        };
        // We rely on an external script from Stripe to use Checkout
        // so it will be undefined until runtime.
        StripeCheckout.open(settings);
    }

    $.fn.checkout = function() {
        // We bind a submit event handler for any element
        // registered with this plugin.
        $(this).submit(function(event) {
            // Upon submission, we set this plugin's global
            // $form variable. This ensures that the other
            // plugin methods can act freely on just this form.
            $form = $(this);
            // We only submit the form when it has a token.
            // If it doesn't have a token, we will block the
            // submission and call the handleCheckout method,
            // which will add a token before resubmitting the form.
            if (formValue('stripe_token')) {
                return true;
            } else {
                event.stopImmediatePropagation();
                event.preventDefault();
                handleCheckout();
                return false;
            }
        });
    };
})( jQuery );

$('document').ready(function(){

  $("#other_amount").currencyField();
  $(".currency").attr("placeholder", "Other Amount");
  $(".currency").autoNumeric("set", "");
  $(".currency").trigger("focusout");

  $(".currency").focus(function() {
    var amount = $(".donation.button-group input[name='amount']");
    amount.prop("checked", false);
    amount.trigger("change");
    $(this).autoNumeric("set", $(this).autoNumeric("get"));
  });

  $(".donation.button-group input:radio").change(function() {
    var label = $("label[for='" + $(this).attr("id") + "']");
    label.siblings("label").removeClass('primary');
    if ($(this).prop("checked")) {
      label.addClass('primary');
    } else {
      label.removeClass('primary');
    }
  });

  $(".donation.button-group input[name='amount']:radio").change(function() {
    if ($(this).prop("checked")) {
      $(".currency").autoNumeric("set", "");
      $(".currency").trigger("focusout");
      $("#other_amount").val($(this).val() * 100);
    }
  });

  $(".donation.button-group input[name='type']:radio").change(function() {
    var values;
    if ($(this).val() == "one-time") {
      values = [10, 25, 50, 100];
    } else {
      values = [5, 10, 25, 50];
    }
    $(".donation.button-group input[name='amount']:radio").each(function(index) {
      $(this).val(values[index]);
      $("label[for='" + $(this).attr("id") + "']").text("$" + values[index]);
    });
  });

  $(".donation.button-group input:radio:checked").trigger("change");

});
