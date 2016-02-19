// tabs.js

// collect all the tabs
var tabs = $('.tab').attr('tabindex', '0');

// get an array of tab-panel ids
var tab_targets = tabs.map(function() {
    return this.hash;
}).get();

// use those ids to get the actual tab-panels
var tab_panels = $(tab_targets.join(','));

function showTab(id) {
    // if no id provided, use the id of the first panel
    id = !id ? tab_targets[0] : id;
    if (!id) {
        return
    }
    // remove the active class from the tabs,
    // and add it back to the one the user selected
    tabs.removeClass('active').attr('aria-selected', 'false').filter(function() {
        return (this.hash === id);
    }).addClass('active').attr('aria-selected', 'true');
    // hide all the panels, then filter to the one
    // we're interested in and show it
    tab_panels.find('.tab-panel-heading').hide();
    tab_panels.hide().attr('aria-hidden', 'true').filter(id).show().attr('aria-hidden', 'false');
    console.log('Switched to tab:', id);
}

$(window).on('hashchange', function() {
    // check if the hash is a target
    var hash = location.hash;
    if (tab_targets.indexOf(hash) !== -1) {
        showTab(hash);
    }
});

// initialize
showTab(tab_targets.indexOf(location.hash) !== -1 ? location.hash : '');
