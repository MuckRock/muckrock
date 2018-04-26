
/* foiaRequest.js
 **
 ** Provides functionality on the composer page.
 **
 */

import modal from './modal';
import showOrigContactInfo from './foiaRequest';

$(document).ready(function(){

  var agencyField = $('fieldset.agencies');
  var agencyInput = agencyField.find('input');
  var agencyWidget = agencyField.find('.autocomplete-light-widget');

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

  function setContactInfoOptions(select, options) {
    select.find('option').remove();
    for(var i = 0; i < options.length; i++) {
      select.append(
        $("<option>").attr("value", options[i].value).text(options[i].display)
      );
    }
    select.append($("<option value=\"\">").text("Other..."));
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
      url: "/agency/boilerplate/",
      data: {
        agencies: agencyField.find(".deck > .choice").map(function(){
          return $(this).data("value");
        }).get()
      },
      type: "get",
      success: function(data) {
        $(".document-boilerplate.intro").html(data.intro);
        $(".document-boilerplate.outro").html(data.outro);
        $(".tooltip").tooltipster({
          trigger: "custom",
          triggerOpen: {
            click: true,
            mouseenter: true,
            touchstart: true,
            tap: true
          },
          triggerClose: {
            click: true,
            mouseleave: true,
            originClick: true,
            tap: true,
            touchleave: true
          },
        });
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

    // handle contact info
    if (requestCount === 1) {
      $.ajax({
        url: "/agency/contact-info/" + agencyField.find(".deck > .choice").data("value") + "/",
        type: 'get',
        success: function(data) {
          if (data.type) {
            $(".contact-info .info").data("type", data.type);
          } else {
            if (data.portal) {
              $(".contact-info .info").data("portal-type", data.portal.type);
              $(".contact-info .info").data("portal-url", data.portal.url);
              if ($("#id_via option[value='portal']").length === 0) {
                $("#id_via").prepend("<option value=\"portal\">Portal</option>");
              }
            } else {
              $("#id_via option[value='portal']").remove();
            }
            $(".contact-info .info").data("email", data.email);
            $(".contact-info .info").data("cc-emails", data.cc_emails);
            $(".contact-info .info").data("fax", data.fax);
            $(".contact-info .info").data("address", data.address);
            setContactInfoOptions($("#id_email"), data.emails);
            setContactInfoOptions($("#id_fax"), data.faxes);
          }
          showOrigContactInfo();
          $("#id_email").prop("disabled", "");
          $("#id_fax").prop("disabled", "");
          $(".contact-info").show();
        }
      });
    } else {
      $("#id_use_contact_information").val(false);
      $("#id_email").prop("disabled", "disabled");
      $("#id_fax").prop("disabled", "disabled");
      $(".contact-info").hide();
    }

    if (requestCount === 0) {
      $("#id_agencies-autocomplete").attr(
        "placeholder",
        "Agency's name, followed by location"
      );
    } else {
      $("#id_agencies-autocomplete").attr(
        "placeholder",
        "Optionally add another agency - the request will be sent to all of them"
      );
    }

  });
  agencyWidget.trigger("widgetSelectChoice");

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
    var textArea = $("form.create-request .requested_docs textarea");
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
      textArea.height(textArea[0].scrollHeight);
      $(this).css("opacity", "0.5");
    } else {
      $(this).prop("checked", "checked");
    }
  });

  $("#id_permanent_embargo").change(function(){
    if (this.checked) {
      $("#id_embargo").prop("checked", true);
    }
  });

  $("#id_embargo").change(function(){
    if (!this.checked) {
      $("#id_permanent_embargo").prop("checked", false);
    }
  });

  // Autosaving
  // https://stackoverflow.com/questions/19910843/autosave-input-boxs-to-database-during-pause-in-typing
	var timeoutId, hiddenId;
  var composerPk = $("form.create-request").data("composer-pk");

  function changeText(text, error) {
    clearTimeout(hiddenId);
    $(".form-status-holder").text(text).removeClass("hidden");
    if (error) {
      $(".form-status-holder").addClass("error");
    } else {
      $(".form-status-holder").removeClass("error");
    }
    hiddenId = setTimeout(function(){$(".form-status-holder").addClass("hidden");}, 2000);
  }
  changeText("Autosave Enabled");

  function changeHandler() {
    changeText("Unsaved");
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
        changeText("Saving Changes...");
      },
      success: function() {
        // Now show them we saved
        changeText("Draft Saved");
        setTimeout(function(){$(".form-status-holder").addClass("hidden");}, 2000);
      },
      error: function() {
        // Now show them there was an error
        changeText("Changes Not Saved", true);
      }
    });
  }

});
