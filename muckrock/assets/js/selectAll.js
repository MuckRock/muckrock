/* selectAll.js
**
** A JQuery plugin to handle the logic when interacting with a select-all checkbox:
** - Handles switching the checkbox between All, None, and Intermediate states
** - Handles checking or unchecking related checkboxes
** - Handles enabling or disabling a related toolbar
*/

(function( $ ){
    var selectAllCheckbox, checkboxes, toolbar;
    function disableToolbar() {
        $(toolbar).attr('disabled', true).closest('.field').addClass('disabled');
    }
    function enableToolbar() {
        $(toolbar).attr('disabled', false).closest('.field').removeClass('disabled');
    }
    function handleSelectAllCheckboxClick() {
        var checked = $(selectAllCheckbox)[0].checked;
        $(checkboxes).each(function(){
            this.checked = checked;
            $(this).change();
        });
        if (checked) {
            enableToolbar();
        } else {
            disableToolbar();
        }
    }
    function handleCheckboxClick() {
        var checkedCheckboxes = $(checkboxes).filter(':checked');
        if (checkedCheckboxes.length == $(checkboxes).length) {
            selectAllCheckbox[0].indeterminate = false;
            selectAllCheckbox[0].checked = true;
        } else {
            selectAllCheckbox[0].indeterminate = true;
        }
        if (checkedCheckboxes.length == 0) {
            selectAllCheckbox[0].indeterminate = false;
            selectAllCheckbox[0].checked = false;
            disableToolbar();
        } else {
            enableToolbar();
        }
    }
    $.fn.selectAll = function() {
        selectAllCheckbox = $(this);
        var checkboxesName = $(selectAllCheckbox).data('name');
        var toolbarId = $(selectAllCheckbox).data('toolbar');
        // The checkboxes are defined by a 'name' data attribute on the checkbox
        checkboxes = $('input[name=' + checkboxesName + ']');
        // The toolbar is defined by a 'toolbar' data attribute on the checkbox
        // And is actually the inputs and buttons contained within the toolbar
        toolbar = $(toolbarId).find(':input, :button');
        // Listen to changes on the checkboxes
        $(checkboxes).click(handleCheckboxClick);
        // Listen to changes to the select all checkbox
        $(selectAllCheckbox).click(handleSelectAllCheckboxClick);
        // Disable the toolbar to start.
        disableToolbar();
    };
})( jQuery );
