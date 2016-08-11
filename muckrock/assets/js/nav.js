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
$('#show-sections').click(function(){
    var button = this;
    var sections = '#global-sections';
    toggleNav(sections, button);
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

// Global nav quick login
$('#quick-log-in').click(function(e){
    e.preventDefault();
    var quickLogin = $('#quick-log-in-form');
    quickLogin.addClass('visible');
    quickLogin.find('input[type=text]')[0].focus();
    quickLogin.find('.cancel').click(function(){
        quickLogin.removeClass('visible');
    });
});
