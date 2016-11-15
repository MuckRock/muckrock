/* tabs.js
**
** Tabbed-based navigation using Javascript
** and the manipulation of URL hashes.
**
** Turn classed anchor links into tabs,
** and allow elements within those tabs to
** be accessible by hash as well.
*/

import { displayFile } from './foiaRequest';

var tabs = $('.tab').attr('tabindex', '0');         // collect all the tabs and set tabindex to 0
var tabTargets = tabs.map(function() {              // get an array of tab-panel ids
    return this.hash;
}).get();
var tabPanels = $(tabTargets.join(','));            // use those ids to get the actual tab-panels

function showTab(hash) {
    // if no id provided, use the id of the first panel
    hash = !hash ? tabTargets[0] : hash;
    if (!hash) {
        return;
    }
    // remove the active class from the tabs,
    // and add it back to the one the user selected
    tabs.removeClass('active').attr('aria-selected', 'false').filter(function() {
        return (this.hash === hash);
    }).addClass('active').attr('aria-selected', 'true');
    // hide all the panels, then filter to the one
    // we're interested in and show it
    tabPanels.find('.tab-panel-heading').hide();
    tabPanels.hide().attr('aria-hidden', 'true').filter(hash).show().attr('aria-hidden', 'false');
}

function handleHashChange() {
    // check if the hash is a target
    var hash = location.hash;
    if (tabTargets.includes(hash)) {
        showTab(hash);
        return;
    }
    // check if the hash is a child of a target
    // if it is, switch to that tab and stop checking
    $(tabTargets).each(function(_, target) {
        if ($(hash).closest(target).length > 0) {
            showTab(target);
            // if the inner item was a file, display it
            // otherwise, jump down to the inner item
            if (target == '#files') {
                displayFile(hash);
            } else {
                // scroll to the hashed item
                var elementOffset = $(hash).offset();
                // we subtract (42+19) due to the fixed header height and some spacing
                window.scrollTo(elementOffset.left, elementOffset.top - (42+19));
            }
            // return false to prevent any other tabs from being matched
            return false;
        }
    });
}

// Bind to hashchange event
$(window).on('hashchange', handleHashChange);

// Initialize
handleHashChange();

