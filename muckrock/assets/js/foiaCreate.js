
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

  // if the selected agency is exempt, show an error message
  agencyWidget.on("widgetSelectChoice widgetDeselectChoice", function(){
    $.ajax({
      url: '/agency/boilerplate/',
      data: {
        agencies: agencyField.find(".choice.hilight").map(function(){
          return $(this).data("value");
        }).get()
      },
      type: 'get',
      success: function(data) {
        $(".document-boilerplate.intro").html(data.intro);
        $(".document-boilerplate.outro").html(data.outro);
      }
    });
  });

  agencyWidget.on("widgetSelectChoice", function(){
    if (agencyField.find('.small.red.badge').length > 0) {
      $("#submit_button").prop("disabled", "disabled");
      $("#submit_help").text("The agency you have selected is exempt from public records requests.  Please select another agency.");
    }
  });

  // clear the exempt error message when the agency is deselected
  agencyWidget.on("widgetDeselectChoice", function(){
    $("#submit_button").prop("disabled", "");
    $("#submit_help").text("");
  });

  // run some validation
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

});
