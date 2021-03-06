/* stripe.js
 *
 * This handles stripe elements
 */

function stripeTokenHandler(token, form) {
  // Insert the token ID into the form so it gets submitted to the server
  var hiddenInput = $("#id_stripe_token");
  hiddenInput.val(token.id);
  // Submit the form
  form.off("submit");
  form.submit();
}

if ($("#id_stripe_pk").length) {
  /* eslint-disable no-undef */
  var stripe = Stripe($("#id_stripe_pk").val());
  /* eslint-enable no-undef */
  var elements = stripe.elements();

  var style = {
    base: {
      color: '#3F3F3F',
      fontSize: '16px',
      fontFamily: 'system-ui, sans-serif',
      fontSmoothing: 'antialiased',
      '::placeholder': {
        color: '#899194'
      }
    },
    invalid: {
      color: '#e5424d',
      ':focus': {
        color: '#303238'
      }
    }
  };

  $("document").ready(function(){
    $("#id_use_card_on_file_0").change(function() {
      $("#card-element-container").hide();
      $("#id_save_card").closest("div").hide();
    });
    $("#id_use_card_on_file_1").change(function() {
      $("#card-element-container").show();
      $("#id_save_card").closest("div").show();
    });

    var $orgSelect = $(".buy-request-form #id_organization");
    var $useCardOnFile = $("#id_use_card_on_file").closest("div.field");
    if ($orgSelect.length > 0) {
      $orgSelect.change(function() {
        var card = $(".buy-request-form").data("org-card-" + $(this).val());
        if (card) {
          $("#id_use_card_on_file_0")[0].nextSibling.nodeValue = card;
          $useCardOnFile.show();
        } else {
          $("#id_use_card_on_file_1").prop("checked", true).trigger("change");
          $useCardOnFile.hide();
        }
      });
      $orgSelect.change();
    }

    var card = elements.create("card", {style: style});
    card.addEventListener("ready", function() {
      if($("input[name=use_card_on_file]:checked").val() === "True") {
        $("#id_use_card_on_file_0").change();
      } else {
        $("#id_use_card_on_file_1").change();
      }
    });
    if ($("#card-element").length > 0) {
      card.mount("#card-element");
      card.addEventListener("change", function(event) {
        var displayError = $("#card-errors");
        if (event.error) {
          displayError.text(event.error.message);
        } else {
          displayError.text("");
        }
      });
      // We don"t want the browser to fill this in with old values
      $("#id_stripe_token").val("");
      // Create a token or display an error when the form is submitted.
      var form = $("#card-element").closest("form");
      form.submit(function(event) {
        var buySection = $(".buy-section");
        // buy section must be visible to buy
        // if buy section doesn't exist (such as the detail page for paying fees)
        // we want to pay, so default to true
        var buySectionVisible =
          buySection.length > 0 ? buySection.is(":visible") : true;
        var useCardOnFile = $("input[name=use_card_on_file]:checked").val() === "True";
        var actionInput = form.find("input[name='action']");
        var actionSubmit = true; // assume we are submitting by default
        if (actionInput.length) {
          // if there is an action input, check it is submit (for composer page)
          // or pay_fee (for detail page)
          actionSubmit = (actionInput.val() === 'submit') ||
            (actionInput.val() === 'pay_fee');
        }
        if (buySectionVisible && !useCardOnFile && actionSubmit) {
          event.preventDefault();

          stripe.createToken(card).then(function(result) {
            if (result.error) {
              // Inform the customer that there was an error.
              var errorElement = $("#card-errors");
              errorElement.text(result.error.message);
            } else {
              // Send the token to your server.
              stripeTokenHandler(result.token, form);
            }
          });
        }
      });
    }
  });
}
