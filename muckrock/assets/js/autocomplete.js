import $ from 'jquery';

let projectRequestAutocomplete = $('.project.form #id_requests-autocomplete');

function getDeckElements(autocompleteInput) {
    var elementIds = [];
    $(autocompleteInput).siblings('.deck').children().map((i, item) => {
        elementIds.push($(item).data('value'));
    });
    return elementIds;
}

$(projectRequestAutocomplete).change(function() {
    $(this).yourlabsAutocomplete().data = {
        exclude: getDeckElements(this)
    };
});
