/* exemptionBrowser.js
**
** A JQuery plugin that adds an interface for browsing exemptions.
** Supports searching exemptions with AJAX and sampling the appeal language they provide.
** Exemptions are currently listed at the `/exemption/` API endpoint without any authentication requirements.
*/

import _ from 'lodash';

(function( $ ){
    var $browser;

    function getFormValue(key, form) {
        // Given a form selector or target, return a value from the form
        // If the key does not exist in the form then return undefined.
        var inputArray = $(form).serializeArray();
        var qIndex = _.findIndex(inputArray, function(object){
            return object.name == key;
        });
        if (qIndex > -1) {
            return inputArray[qIndex].value;
        } else {
            return undefined;
        }
    }

    function getQueryResults(endpoint, form) {
        var data = $(form).serializeArray();
        $.ajax({
            url: endpoint,
            type: 'GET',
            data: data,
            success: function(data, status, request) {
                console.debug('Response:\t', data);
            }
        });
    }

    function exemptionSearch(event) {
        // Handle a search for exemptions:
        // 1. Submit the query via AJAX
        // 2. Render the response into a list of results.
        var form = event.target;
        var action = form.action;
        var query = getFormValue('q', form);
        getQueryResults(action, form);
        console.debug('Action:\t', action);
        console.debug('Query:\t', query);
        return false;
    }

    $.fn.exemptionBrowser = function() {
        $browser = $(this);
        $browser.find('form').submit(exemptionSearch);
    }
})( jQuery );
