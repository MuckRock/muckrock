/* stripe.js
 *
 * This handles stripe elements
 */

/* eslint-disable no-undef */
var stripe = Stripe($("#stripe_pub_key").val());
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
    fontSize: "1rem",
    color: "#32325d",
  }
};

$("document").ready(function(){
  var card = elements.create("card", {style: style});
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
      var freePlan = $("#id_plan option:selected").text() === "Free";
      if (!useCardOnFile && !freePlan) {
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
