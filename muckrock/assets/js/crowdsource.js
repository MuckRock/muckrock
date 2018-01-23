/* crowdsource.js
**
*/

$(document).ready(function(){
  var formBuilder = $("#build-wrap").formBuilder({
      disableFields: [
        'autocomplete',
        'button',
        'checkbox-group',
        'date',
        'file',
        'header',
        'hidden',
        'number',
        'paragraph',
        'radio-group',
        'textarea'
      ],
      disabledAttrs: [
        'access',
        'className',
        'inline',
        'max',
        'maxlength',
        'min',
        'multiple',
        'name',
        'other',
        'placeholder',
        'required',
        'rows',
        'step',
        'style',
        'subtype',
        'toggle',
        'value'
      ],
      disabledActionButtons: ['data', 'save', 'clear'],
      defaultFields: JSON.parse($("#id_crowdsource-form_json").val())
  });

  $("form.create-crowdsource").submit(function() {
    $("#id_crowdsource-form_json").val(formBuilder.actions.getData('json'));
  });

  $("#add-crowdsource-data").click(function(e) {
    e.preventDefault();
    cloneMore("div.crowdsource-data:last");
  });

  function cloneMore(selector) {
    var newElement = $(selector).clone(true);
    var total = $('#id_data-TOTAL_FORMS').val();
    newElement.find(':input').each(function() {
      var name = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
      var id = 'id_' + name;
      $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
    });
    newElement.find('label').each(function() {
      var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
      $(this).attr('for', newFor);
    });
    total++;
    $('#id_data-TOTAL_FORMS').val(total);
    $(selector).after(newElement);
  }

});
