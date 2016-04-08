import { displayFile } from './foiaRequest';

/*

tabs.js

Tabbed-based navigation using Javascript
and the manipulation of URL hashes.

Turn classed anchor links into tabs,
and allow elements within those tabs to
be accessible by hash as well.

*/

var tabs = $('.tab').attr('tabindex', '0');         // collect all the tabs and set tabindex to 0
var tabTargets = tabs.map(function() {              // get an array of tab-panel ids
    return this.hash;
}).get();
var tabPanels = $(tabTargets.join(','));            // use those ids to get the actual tab-panels
var deepItems = $('.file, .note, .communication');  // get all the deep link things
var deepItemTargets = deepItems.map(function() {    // get a list of all the file hashes
    return '#' + $(this).attr('id');
}).get();

function showTab(id) {
    // if no id provided, use the id of the first panel
    id = !id ? tabTargets[0] : id;
    if (!id) {
        return;
    }
    // remove the active class from the tabs,
    // and add it back to the one the user selected
    tabs.removeClass('active').attr('aria-selected', 'false').filter(function() {
        return (this.hash === id);
    }).addClass('active').attr('aria-selected', 'true');
    // hide all the panels, then filter to the one
    // we're interested in and show it
    tabPanels.find('.tab-panel-heading').hide();
    tabPanels.hide().attr('aria-hidden', 'true').filter(id).show().attr('aria-hidden', 'false');
}

function getTabId(id) {
    var hyphen = id.indexOf('-');
    var tabId = id.substring(0, hyphen != -1 ? hyphen : id.length) + 's';
    return tabId;
}

function deepLink(id) {
    // we expect a hyphen delimited id, e.g. #file-1
    if (!id || id.indexOf('-') === -1) {
        return;
    }
    var tab = getTabId(id);
    showTab(tab);
    if (tab == '#files') {
        // deep link to single file
        var file = deepItems.filter(id).first();
        displayFile(file);
    } else if (tab == '#notes' || tab == '#comms') {
        // deep link to specific element
        var elementOffset = deepItems.filter(id).first().offset();
        window.scrollTo(elementOffset.top, elementOffset.left);
    }
}

// Bind to hashchange event
$(window).on('hashchange', function () {
    // check if the hash is a target
    var hash = location.hash;
    if (tabTargets.indexOf(hash) !== -1) {
        showTab(hash);
    }
    if (deepItemTargets.indexOf(hash) !== -1) {
        deepLink(hash);
    }
});

// Initialize
showTab(tabTargets.indexOf(location.hash) !== -1 ? location.hash : '');
deepLink(deepItemTargets.indexOf(location.hash) !== -1 ? location.hash : '');
