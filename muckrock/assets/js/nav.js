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
function showLogin(login, trigger) {
    $(trigger).addClass('active')
    $(login).addClass('visible').find('input[type=text]')[0].focus();
}

function hideLogin(login, trigger) {
    $(trigger).removeClass('active');
    $(login).removeClass('visible');
}
$('#quick-log-in').click(function(e){
    e.preventDefault();
    var button = $(this);
    var quickLogin = $('#quick-log-in-form');
    showLogin(quickLogin, button);
    quickLogin.find('.cancel').click(()=>{
        hideLogin(quickLogin, button);
    });
});

// Handle touch events on mobile
$('#user-nav > ul > li').on('touchend', function(e){
    if (e.target.nodeName == 'A') {
        return
    }
    var target = this;
    $(target).siblings().removeClass('hover');
    $(target).toggleClass('hover');
    if ($(target).hasClass('hover')) {
        $('#modal-overlay').addClass('visible').on('click', function() {
            $(this).removeClass('visible');
            $(target).removeClass('hover');
        });
    } else {
        $('#modal-overlay').removeClass('visible');
    }
});

