var toolbar = $('.toolbar :button, .toolbar :input');

function disableToolbar() {
    toolbar.attr('disabled', true).closest('.field').addClass('disabled');
}

function enableToolbar() {
    toolbar.attr('disabled', false).closest('.field').removeClass('disabled');
}

function handleBodyCheckboxChange(checkbox) {
    var table = $(checkbox).closest('table');
    var headerCheckbox = $(table).find('th input:checkbox');
    var bodyCheckboxes = $(table).find('td input:checkbox');
    var checkedBoxes = bodyCheckboxes.filter(':checked');
    if (checkedBoxes.length == bodyCheckboxes.length) {
        headerCheckbox[0].indeterminate = false;
        headerCheckbox[0].checked = true;
    } else {
        headerCheckbox[0].indeterminate = true;
    }
    if (checkedBoxes.length == 0) {
        headerCheckbox[0].indeterminate = false;
        headerCheckbox[0].checked = false;
        disableToolbar();
    } else {
        enableToolbar();
    }
}

function handleHeaderCheckboxChange(checkbox) {
    var table = $(checkbox).closest('table');
    var headerCheckbox = $(checkbox);
    var bodyCheckboxes = $(table).find('td input:checkbox');
    var checked = checkbox.checked;
    bodyCheckboxes.each(function(index, bodyCheckbox){
        bodyCheckbox.checked = checked;
    });
    if (checked) {
        enableToolbar();
    } else {
        disableToolbar();
    }
}

$('th input:checkbox').change(function(){
    handleHeaderCheckboxChange(this);
});

$('td input:checkbox').change(function(){
    handleBodyCheckboxChange(this);
});

$(document).ready(function(){
    disableToolbar();
});
