
/* foiaRequest.js
 **
 ** Provides functionality on the composer page.
 **
 */

import modal from './modal';

$(document).ready(function(){

  var agencyField = $('fieldset.agencies');
  var agencyInput = agencyField.find('input');
  var agencyWidget = agencyField.find('.autocomplete-light-widget');
  var agencySelect = agencyWidget.find('select');

  function updateRequestCount(num) {
    var requestsLeft = $(".requests-left"),
    hasOrg = requestsLeft.data("org") || 0,
    hasMonthly = requestsLeft.data("month") || 0,
    hasRegular = requestsLeft.data("reg") || 0,
    useOrg = 0,
    useMonthly = 0,
    useRegular = 0,
    useExtra = 0;

    if (num < hasOrg) {
      useOrg = num;
    } else if (num < (hasOrg + hasMonthly)) {
      useOrg = hasOrg;
      useMonthly = num - hasOrg;
    } else if (num < (hasOrg + hasMonthly + hasRegular)) {
      useOrg = hasOrg;
      useMonthly = hasMonthly;
      useRegular = num - (hasOrg + hasMonthly);
    } else {
      useOrg = hasOrg;
      useMonthly = hasMonthly;
      useRegular = hasRegular;
      useExtra = num - (hasOrg + hasMonthly + hasRegular);
    }
    var text = "You are making <strong>" + num + "</strong> request" +
      (num !== 1 ? "s" : "") + ".  ";
    var useAny = (useOrg > 0 || useMonthly > 0 || useRegular > 0);
    if (useAny) {
      text += "This will use ";
      var useText = [];
      if (useOrg > 0) {
        useText.push("<strong>" + useOrg + "</strong> organizational request" +
          (useOrg > 1 ? "s" : ""));
      }
      if (useMonthly > 0) {
        useText.push("<strong>" + useMonthly + "</strong> monthly request" +
          (useMonthly > 1 ? "s" : ""));
      }
      if (useRegular > 0) {
        useText.push("<strong>" + useRegular + "</strong> regular request" +
          (useRegular > 1 ? "s" : ""));
      }
      if (useText.length > 1) {
        text += useText.slice(0, -1).join(", ");
        text += (" and " + useText[useText.length - 1] + ".  ");
      } else {
        text += (useText[0] + ".  ");
      }
    }
    if (useExtra > 0) {
      text += ("You will " + (useAny ? "also " : "") + "need to purchase <strong>"
        + useExtra + "</strong> extra request" + (useExtra > 1 ? "s" : "") + ".");
      $(".buy-request-form").show();
      $("#submit_button").text("Buy & Submit");
      $("#id_num_requests").val(Math.max(useExtra, $("#id_num_requests").attr("min")));
      $("#id_num_requests").trigger("change");
    } else {
      $(".buy-request-form").hide();
      $("#submit_button").text("Submit");
      $("#id_num_requests").val("");
    }
    $(".using-requests").html(text);
  }

  $("#id_num_requests").change(function(){
    var bulkPrice = $(".buy-request-form").data("bulk-price");
    var num = $(this).val();
    var price;
    if (num >= 20) {
      price = num * bulkPrice;
    } else {
      price = num * 5;
    }
    $("[name='stripe_amount']").val(price * 100);
    $("[name='stripe_description']").val(num + " request" + (num > 1 ? "s" : "") +
      " ($" + price + ".00)");
  });
  $("#id_num_requests").trigger("change");

  agencyWidget.on("widgetSelectChoice widgetDeselectChoice", function(){
    // get boilerplate language for selected agencies
    $.ajax({
      url: '/agency/boilerplate/',
      data: {
        agencies: agencyField.find(".deck > .choice").map(function(){
          return $(this).data("value");
        }).get()
      },
      type: 'get',
      success: function(data) {
        $(".document-boilerplate.intro").html(data.intro);
        $(".document-boilerplate.outro").html(data.outro);
      }
    });

    // update the request count
    var requestCount = agencyField.find(".deck > .choice").length;
    var exemptCount = agencyField.find(".exempt").length;
    var nonExemptCount = requestCount - exemptCount;

    updateRequestCount(nonExemptCount);

    // handle exempt agencies
    if ((exemptCount > 0) && (nonExemptCount > 0)) {
      $("#submit_button").prop("disabled", "");
      $("#submit_help").text("Some of the agencies you have selected are exempt.  You may submit this request to the non-exempt agencies, but the selected exempt agencies will not be included.");
    } else if (exemptCount > 0) {
      $("#submit_button").prop("disabled", "disabled");
      $("#submit_help").text("The agency you have selected is exempt from public records requests.  Please select another agency.");
    } else {
      $("#submit_button").prop("disabled", "");
      $("#submit_help").text("");
    }

  });
  agencyWidget.trigger("widgetSelectChoice");

  // secondary agency fuzzy matching
  // XXX redo this
  $("foo form.create-request").submit(function(e){
    // if a real agency is not selected, prevent the submit and
    // help the user try and find a suitable replacement
    if (agencySelect.val().length === 0) {
      e.preventDefault();

      // send whatever is typed in to the text box to an agency fuzzy matcher
      $.ajax({
        url: '/agency/similar/',
        data: {
          query: agencyInput.val()
          // jurisdiction: getJurisdiction()
        },
        type: 'get',
        success: function(data) {
          // if there was an exact match, just chose that
          if (data.hasOwnProperty('exact')) {
            agencySelect.append($("<option>", data.exact));
            agencySelect.val(data.exact.value);
            $("form.create-request").off("submit");
            $("form.create-request").submit();
            return;
          }
          length = data.suggestions.length;
          // no suggestions, just submit as is
          if (length === 0) {
            $("form.create-request").off("submit");
            $("form.create-request").submit();
            return;
          }
          // there are suggestions, display a modal asking the user if they meant
          // one of the suggested agencies
          $("#similar-agency-modal h1").text(
              "The \"" + agencyInput.val() + "\" isn't in our database yet.");
          modal($("#similar-agency-modal"));
          $("#replacement-agency").children().remove();
          for (var i = 0; i < length; i++) {
            $("#replacement-agency").append($("<option>", data.suggestions[i]));
          }
        },
        error: function() {
          $("#submit_help").text("Sorry, there was an error submitting this form.  Please try again later, or contact us if the eror continues.");
        }
      });
    }
  });

  $("#new-agency-button").click(function() {
    // The new agency button continues with the new agency - just submit the form as is
    $("form.create-request").off("submit");
    $("form.create-request").submit();
  });

  $("#replacement-agency-button").click(function() {
    // The replacement agency button selects a replacement agency
    if ($("#replacement-agency option:selected").length === 0) {
      $("#similar-agency-modal .error").text("Please select a replacement agency.");
    } else {
      agencySelect.append($("#replacement-agency option:selected").clone());
      agencySelect.val($("#replacement-agency").val());
      $("form.create-request").off("submit");
      $("form.create-request").submit();
    }
  });

  $("form.create-request").submit(function(e){
    var email_regex = /\w+@\w+.\w+/;
    if (email_regex.test($("#id_requested_docs").val()) &&
        $("#email-warning-modal").data("foias-filed") == 0) {
      e.preventDefault();
      modal($("#email-warning-modal"));
      $("form.create-request").off("submit");
    }
  });

  $(".toggle-advanced").click(function(){
    if($(".advanced-container").is(":visible")) {
      $(this).text("\u25b6 Advanced Options");
    } else {
      $(this).text("\u25bc Advanced Options");
    }
    $(".advanced-container").toggle();
  });

  $("#save_button").click(function(){
    $("input[name='action']").val("save");
    $(".submit-required").removeAttr("required");
    agencyInput.removeAttr("required");
    $(this).closest("form").submit();
  });

  $("#submit_button").click(function(){
    $("input[name='action']").val("submit");
    // if they need to buy requests, enable checkout on this form before submitting
    if ($(".buy-request-form").is(":visible")) {
      $(this).closest("form").checkout();
    }
    $(".submit-required").attr("required", "required");
    if (agencyField.find(".deck > .choice").length === 0) {
      // no agency choices
      agencyInput.attr("required", "required");
    } else {
      agencyInput.removeAttr("required");
    }
    var form = $(this).closest("form");
    if (form.get(0).reportValidity()) {
      form.submit();
    }
  });

  $("#delete_button").click(function(){
    $("input[name='action']").val("delete");
    $(".submit-required").removeAttr("required");
    agencyInput.removeAttr("required");
    $(this).closest("form").submit();
  });

  $("#id_edited_boilerplate").change(function(){
    if (this.checked) {
      var requestedDocs = $("#id_requested_docs").val();
      var newText = "To Whom It May Concern:\n\nPursuant to the { law name }, " +
        "I hereby request the following records:\n\n" + requestedDocs + "\n\n" +
        "The requested documents will be made available to the general public, " +
        "and this request is not being made for commercial purposes.\n\n" +
        "In the event that there are fees, I would be grateful if you would " +
        "inform me of the total charges in advance of fulfilling my request. " +
        "I would prefer the request filled electronically, by e-mail attachment " +
        "if available or CD-ROM if not.\n\nThank you in advance for your " +
        "anticipated cooperation in this matter.\n\n" +
        "I look forward to receiving your response to this request within " +
        "{ number of days } { business or calendar } days, " +
        "as the statute requires.\n\n" +
        "Sincerely,\n\n" +
        "{ name }";
      $("#id_requested_docs").val(newText);
      $("form.create-request").addClass("edited-boilerplate");
    } else {
      $("form.create-request").removeClass("edited-boilerplate");
    }
  });

  // https://stackoverflow.com/questions/19910843/autosave-input-boxs-to-database-during-pause-in-typing
	var timeoutId;
  var composerPk = $("form.create-request").data("composer-pk");

  function changeHandler() {
    $(".form-status-holder").text("Unsaved");
    clearTimeout(timeoutId);
    timeoutId = setTimeout(function() {
      // Runs 1 second (1000 ms) after the last change
      saveToDB();
    }, 1000);
  }

  if (composerPk) {
    $("form.create-request input, form.create-request textarea").on(
      "input propertychange change", changeHandler);
    agencyWidget.on("widgetSelectChoice widgetDeselectChoice", changeHandler);
  }

  function saveToDB() {
    var form = $("form.create-request");
    $.ajax({
      url: "/foi/composer-autosave/" + form.data("composer-pk") + "/",
      type: "POST",
      data: form.serialize(), // serializes the form's elements.
      beforeSend: function() {
        // Let them know we are saving
        $(".form-status-holder").text("Saving...");
      },
      success: function() {
        // Now show them we saved and when we did
        var d = new Date();
        $(".form-status-holder").text("Saved! Last: " + d.toLocaleTimeString());
      },
      error: function() {
        // Now show them we saved and when we did
        $(".form-status-holder").text("Error");
      },
    });
  }

});
