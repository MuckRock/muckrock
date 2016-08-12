/* exemptionBrowser.js
**
** A JQuery plugin that adds an interface for browsing exemptions.
** Supports searching exemptions with AJAX and sampling the appeal language they provide.
** Exemptions are currently listed at the `/exemption/` API endpoint without any authentication requirements.
*/

import _ from 'lodash';

(function( $ ){
    var $browser, globalQuery;

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

    function renderResultListItem(result) {
        var $result = $('<li class="result"></li>');
        $result.append(result.name);
        return $result;
    }

    function renderResultsList(results) {
        // Renders a list of the results.
        console.debug('Results:\t', results);
        var $resultsList = $browser.append('<ul class="results"></ul>');
        _(results).forEach(function(result){

            $resultsList.append(renderResultListItem(result));
        });
    }

    function renderEmptyResultsList() {
        // Renders an empty list.
        console.debug('No results!');
    }

    function searchSuccess(data, status, request) {
        console.debug('Response:\t', data);
        if (data.count > 0) {
            renderResultsList(data.results);
        } else {
            renderEmptyResultsList();
        }
    }

    function performSearch(form) {
        // Perform the search using AJAX
        $.ajax({
            url: form.action,
            type: form.method,
            data: $(form).serializeArray(),
            success: searchSuccess
        });
    }

    function exemptionSearch(event) {
        // Handle a search for exemptions:
        // 1. Submit the query via AJAX
        // 2. Render the response into a list of results.
        var form = event.target;
        var query = getFormValue('q', form);
        // Check that the query changed.
        // If it changed, then perform the query.
        // If it didn't change, then don't update the results!
        if (query != globalQuery) {
            globalQuery = query;
            console.debug('New query:\t', query);
            performSearch(form);
        }
        return false;
    }

    $.fn.exemptionBrowser = function() {
        $browser = $(this);
        $browser.find('form').submit(exemptionSearch);
    }
})( jQuery );
