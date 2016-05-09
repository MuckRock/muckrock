import $ from 'jquery';

let projectRequestAutocomplete = $('.project.form #id_requests-autocomplete');

function getDeckElements(autocompleteInput) {
    return $(autocompleteInput).siblings('.deck').children().map(function(i, item) {
        return $(item).data('value');
    });
}

$(projectRequestAutocomplete).change(function() {
    this.yourlabsAutocomplete().data = {
        exclude: getDeckElements(this)
    };
});
