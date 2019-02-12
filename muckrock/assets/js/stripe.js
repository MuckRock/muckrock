/* stripe.js
 *
 * This handles stripe elements
 */

/* eslint-disable no-undef */
var stripe = Stripe($("#id_stripe_pk").val());
/* eslint-enable no-undef */
var elements = stripe.elements();

function stripeTokenHandler(token, form) {
  // Insert the token ID into the form so it gets submitted to the server
  var hiddenInput = $("#id_stripe_token");
  hiddenInput.val(token.id);
  // Submit the form
  form.off("submit");
  form.submit();
}

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
      var useCardOnFile = $("input[name=use_card_on_file]:checked").val() === "True";
      if (!useCardOnFile) {
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
