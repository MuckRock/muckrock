
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
  var agencyWidget = $("#id_agencies");

  function updateRequestCount(num) {
    var requestsLeft = $(".requests-left"),
    hasMonthly = requestsLeft.data("month") || 0,
    hasRegular = requestsLeft.data("reg") || 0,
    useMonthly = 0,
    useRegular = 0,
    useExtra = 0,
    requestOrgs = $(".request-organizations");

    if (num < hasMonthly) {
      useMonthly = num;
    } else if (num < (hasMonthly + hasRegular)) {
      useMonthly = hasMonthly;
      useRegular = num - hasMonthly;
    } else {
      useMonthly = hasMonthly;
      useRegular = hasRegular;
      useExtra = num - (hasMonthly + hasRegular);
    }
    var text = "You are making <strong>" + num + "</strong> request" +
      (num !== 1 ? "s" : "") + ".  ";
    var useAny = (useMonthly > 0 || useRegular > 0);
    if (useAny) {
      text += "This will use ";
      var useText = [];
      if (useMonthly > 0) {
        useText.push("<strong>" + useMonthly + "</strong> monthly request" +
          (useMonthly > 1 ? "s" : ""));
      }
      if (useRegular > 0) {
        useText.push("<strong>" + useRegular + "</strong> purchased request" +
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
        + useExtra + "</strong> extra request" + (useExtra > 1 ? "s" : ""));
      if (hasMonthly === 0 && hasRegular === 0 && requestOrgs.length > 0) {
        text += requestOrgs.html();
      } else{
        text += ".";
      }
      $(".buy-section").show();
      $("#submit_button").text("Buy & Submit");
      $("#id_num_requests").val(Math.max(
        useExtra, $("#id_num_requests").attr("min"), $("#id_num_requests").val()
      ));
      $("#id_num_requests").trigger("change");
      $(".simple-buy .amount").text($("#id_num_requests").val());
    } else {
      $(".buy-section").hide();
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
    $(".simple-buy .price").text("$" + price + ".00");
    $(".buy-request-form .price").text("$" + price + ".00");
  });
  $("#id_num_requests").trigger("change");

  agencyWidget.on("select2:select select2:unselect select2:clear", function(){
    // get boilerplate language for selected agencies
    $.ajax({
      url: "/agency/boilerplate/",
      data: {
        agencies: agencyWidget.val()
      },
      traditional: true,
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
          }
        });
      }
    });

    // update the request count
    var requestCount = agencyWidget.val().length;
    var exemptCount = agencyField.find(".exempt").length;
    var uncoopCount = agencyField.find(".uncooperative").length;
    var proxyCount = agencyField.find(".proxy").length;
    var allowedCount = requestCount - exemptCount - uncoopCount;

    updateRequestCount(allowedCount);

    // handle exempt & uncooperative agencies
    if ((uncoopCount > 0) && (exemptCount > 0) && (allowedCount > 0)) {
      $("#submit_button").prop("disabled", "");
      $("#submit_help").text("Some of the agencies you have selected are exempt or have refused to process MuckRock requests in the past.  You may submit this request to the non-exempt agencies, but the selected exempt and scofflaw agencies will not be included when you file.");
    } else if ((exemptCount > 0) && (allowedCount > 0)) {
      $("#submit_button").prop("disabled", "");
      $("#submit_help").text("Some of the agencies you have selected are exempt.  You may submit this request to the non-exempt agencies, but the selected exempt agencies will not be included.");
    } else if ((uncoopCount > 0) && (allowedCount > 0)) {
      $("#submit_button").prop("disabled", "");
      $("#submit_help").text("Some of the agencies you have selected have refused to process MuckRock requests in the past.  We are not allowing submission of requests to these agencies until we resolve these issues.  You may submit this request to the other agencies normally, but the selected scofflaw agencies will not be included when you file.");
    } else if ((uncoopCount > 0) && (exemptCount > 0)) {
      $("#submit_button").prop("disabled", "disabled");
      $("#submit_help").text("All of the agencies you have selected are exempt or have refused to process our requests in the past.  Please select other agencies.");
    } else if (exemptCount > 0) {
      $("#submit_button").prop("disabled", "disabled");
      $("#submit_help").text("The agency you have selected is exempt from public records requests.  Please select another agency.");
    } else if (uncoopCount > 0) {
      $("#submit_button").prop("disabled", "disabled");
      $("#submit_help").text("The agency you have selected has refused to process requests filed through MuckRock in the past.  We are not allowing submission of requests to these agencies until we are able to resolve this issue.  Please select another agency.");
    } else {
      $("#submit_button").prop("disabled", "");
      $("#submit_help").text("");
    }

    // handle contact info
    if (requestCount === 1) {
      var agencyId = agencyWidget.val()[0];
      if (!isNaN(parseInt(agencyId))) {
        $.ajax({
          url: "/agency/contact-info/" + agencyId + "/",
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
      }
    } else {
      $("#id_use_contact_information").val(false);
      $("#id_email").prop("disabled", "disabled");
      $("#id_fax").prop("disabled", "disabled");
      $(".contact-info").hide();
    }

    if (requestCount === 0) {
      setTimeout(function() {
        $(".agencies .select2-search__field").attr(
          "placeholder",
          "Agency's name, followed by location"
        );
      });
    } else {
      setTimeout(function() {
        $(".agencies .select2-search__field").attr(
          "placeholder",
          "Optionally add another agency - the request will be sent to all of them"
        );
      });
    }

    if (proxyCount > 0) {
      $("fieldset.no_proxy").show();
    } else {
      $("fieldset.no_proxy").hide();
    }

  });
  agencyWidget.trigger("select2:select");

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

    $(".submit-required").attr("required", "required");
    if (agencyWidget.val().length === 0) {
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
        "{ days }.\n\n" +
        "Sincerely,\n\n" +
        "{ name }";
      $("#id_requested_docs").val(newText);
      $("#id_requested_docs").change();
      $("form.create-request").addClass("edited-boilerplate");
      $(this).css("opacity", "0.5");
    } else {
      $(this).prop("checked", "checked");
    }
  });

  $("#id_requested_docs").on("input propertychange change", function() {
    var padding = parseFloat($(this).css('padding-top')) + parseFloat($(this).css('padding-bottom'));
    $(this).height(this.scrollHeight - padding);
  });
  $("#id_requested_docs").change();

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

  $(".show-buy-form").click(function(e) {
    e.preventDefault();
    $(".buy-section").removeClass("hide-form");
    $(".simple-buy").hide();
  });

  var showLogin = false;
  $(".login-toggle-link").click(function(e) {
    showLogin = !showLogin;
    e.preventDefault();
    if (showLogin) {
      $(".login-form").show();
      $(".register-form").hide();
      $(".login-toggle-text").show();
      $(".register-toggle-text").hide();
      $(".login-toggle-link").text("Register now");
      $("#id_register_full_name").removeAttr("required");
      $("#id_register_email").removeAttr("required");
      $("#id_register_full_name").val("");
      $("#id_register_email").val("");
      $("#id_login_username").attr("required", "required");
      $("#id_login_password").attr("required", "required");
      $("#save_button").text("Log In and Save Request");
    } else {
      $(".login-form").hide();
      $(".register-form").show();
      $(".login-toggle-text").hide();
      $(".register-toggle-text").show();
      $(".login-toggle-link").text("Log in");
      $("#id_register_full_name").attr("required", "required");
      $("#id_register_email").attr("required", "required");
      $("#id_login_username").removeAttr("required");
      $("#id_login_password").removeAttr("required");
      $("#id_login_username").val("");
      $("#id_login_password").val("");
      $("#save_button").text("Create Account and Save Request");
    }
  });
  $("#id_register_full_name").attr("required", "required");
  $("#id_register_email").attr("required", "required");

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
    agencyWidget.on("change.select2", changeHandler);
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
        if (!saveToDB.autosave_tracked) {
          /* eslint-disable no-undef */
          mixpanel.track("Request Autosaved");
          /* eslint-enable no-undef */
          saveToDB.autosave_tracked = true;
        }
      },
      error: function() {
        // Now show them there was an error
        changeText("Changes Not Saved", true);
      }
    });
  }

});
