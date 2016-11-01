/* nav.js
**
** Provides logic for the global site navigation.
*/

function toggleNav(nav, button) {
    $(nav).toggleClass('visible');
    $(button).toggleClass('active');
}

function hideNav(nav, button) {
    $(nav).removeClass('visible');
    $(button).removeClass('active');
}

// Global nav sections dropdown
$('#toggle-sections').click(function(){
    var button = this;
    var sections = '#nav-list-sections';
    toggleNav(sections, button);
});


$('.section-list .dropdown .nav-item').click(function(){
    // We only want the nav-item to be triggerable when the dropdown is visible
    // and if it contains some list to drop down.
    var menuIsVisible = $(this).closest('.section-list').hasClass('visible');
    var section = $(this).parent();
    var otherSections = section.siblings();
    var dropdown = section.children('ul');
    if (menuIsVisible && dropdown.length > 0) {
        otherSections.toggle();
        toggleNav(dropdown, section);
        var offsetTop = 42 * 2; // The dropdown is always beneath two 42px tall menus
        var maxHeight = window.innerHeight - offsetTop;
        $(dropdown).css('maxHeight', maxHeight);
    }
});

// Global nav search field
$('#show-search').click(function(){
    var searchButton = this;
    var search = '#global-search';
    var closeSearch = '#hide-search';
    var searchInput = $(search).find('input[type="search"]');
    toggleNav(search, searchButton);
    $(closeSearch).click(function(){
        hideNav(search, searchButton);
    });
    if ($(search).hasClass('visible')) {
        searchInput.focus();
    } else {
        searchInput.blur();
    }
});

// Handle touch events on mobile
$('#user-nav .dropdown').on('click', function(e){
    if (!('ontouchstart' in window)) { // Test for touch device
        e.preventDefault();
        return false;
    }
});

