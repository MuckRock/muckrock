
/* foiaRequest.js
 **
 ** Provides functionality on the composer page.
 **
 */

import modal from './modal';

$(document).ready(function(){

  var localField = $('fieldset.local');
  var stateField = $('fieldset.state');
  var localRadio = $('li.local input:radio');
  var stateRadio = $('li.state input:radio');
  var federalRadio = $('li.federal input:radio');
  var localChecked = $('li.local input:checked');
  var stateChecked = $('li.state input:checked');
  var federalChecked = $('li.federal input:checked');
  var localSelect = $('.autocomplete-light-widget select[name="local"]');
  var stateSelect = $('.autocomplete-light-widget select[name="state"]');
  var agencyField = $('fieldset.agency');
  var agencyInput = agencyField.find('input');
  var agencyWidget = agencyField.find('.autocomplete-light-widget');
  var agencySelect = agencyWidget.find('select');

  function agencyByJurisdiction(jurisdictionSelectElement) {
    agencyInput.yourlabsAutocomplete().data = {
      jurisdiction_id: jurisdictionSelectElement.val()
    };
  }

  function agencyToggle(value) {
    if (value) {
      agencyField.show();
      agencyInput.focus();
      agencyInput.keydown();
    } else {
      agencyField.hide();
    }
  }

  /* Check if prefilled by cloning */
  if (localChecked.length > 0) {
    localChecked.parent().addClass('active');
    localField.show();
    agencyByJurisdiction(localSelect);
    agencyToggle(localSelect.val());
  }
  if (stateChecked.length > 0) {
    stateChecked.parent().addClass('active');
    stateField.show();
    agencyByJurisdiction(stateSelect);
    agencyToggle(stateSelect.val());
  }
  if (federalChecked.length > 0) {
    federalChecked.parent().addClass('active');
    localField.hide();
    stateField.hide();
    agencyByJurisdiction(federalRadio);
    agencyToggle(true);
  }

  /* Bind changes to actions */
  localRadio.change(function() {
    $(this).parent().addClass('active');
    $(this).parent().siblings().removeClass('active');
    localField.show();
    stateField.hide();
    agencyToggle(localSelect.val().length);
    agencyInput.val('');
    agencyWidget.yourlabsWidget().freeDeck();
  });

  stateRadio.change(function() {
    $(this).parent().addClass('active');
    $(this).parent().siblings().removeClass('active');
    localField.hide();
    stateField.show();
    agencyToggle(stateSelect.val().length);
    agencyInput.val('');
    agencyWidget.yourlabsWidget().freeDeck();
  });

  federalRadio.change(function() {
    $(this).parent().addClass('active');
    $(this).parent().siblings().removeClass('active');
    localField.hide();
    stateField.hide();
    agencyToggle(true);
    agencyInput.val('');
    agencyWidget.yourlabsWidget().freeDeck();
    agencyByJurisdiction(federalRadio);
  });

  function selectChange(select) {
    agencyByJurisdiction(select);
    agencyToggle(select.val().length);
    agencyInput.val('');
    agencyWidget.yourlabsWidget().freeDeck();
  }

  localSelect.change(function(){
    selectChange($(this));
  });

  stateSelect.change(function(){
    selectChange($(this));
  });

  // if the selected agency is exempt, show an error message
  agencyWidget.on("widgetSelectChoice", function(){
    if (agencyField.find('.small.red.badge').length > 0) {
      $("#submit").prop("disabled", "disabled");
      $("#submit_help").text("The agency you have selected is exempt from public records requests.  Please select another agency.");
    }
  });

  // clear the exempt error message when the agency is deselected
  agencyWidget.on("widgetDeselectChoice", function(){
    $("#submit").prop("disabled", "");
    $("#submit_help").text("");
  });

  // get the selected jurisdiction for fuzzy agency checking
  function getJurisdiction() {
    if ($('li.local input:checked').length > 0) {
      return localSelect.val();
    } else if ($('li.state input:checked').length > 0) {
      return stateSelect.val();
    } else if ($('li.federal input:checked').length > 0) {
      return 'f';
    } else {
      return '';
    }
  }

  // run some validation
  $("form.create-request").submit(function(e){
    // if a real agency is not selected, prevent the submit and
    // help the user try and find a suitable replacement
    if (agencySelect.val().length === 0) {
      e.preventDefault();

      // send whatever is typed in to the text box to an agency fuzzy matcher
      $.ajax({
        url: '/agency/similar/',
        data: {
          query: agencyInput.val(),
          jurisdiction: getJurisdiction()
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
              "You are submitting to \"" + agencyInput.val() + "\", which is not in our agency database");
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

});
