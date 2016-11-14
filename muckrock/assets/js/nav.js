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

function showOverlay(overlay) {
  return $(overlay).addClass('visible');
}

function hideOverlay(overlay) {
  return $(overlay).removeClass('visible');
}

function setMaxHeight(element, maxHeight) {
  /* Set the max height of an element, in case when we render it it will go off the page. */
  return $(element).css('maxHeight', maxHeight);
}

// Handle touch events on mobile
var navItems = $('#site-nav .section-list, #user-nav .dropdown ul');
var navTriggers = $('#site-nav #toggle-sections, #user-nav .dropdown > .nav-item');
var $overlay = $('#modal-overlay');
navTriggers.on('click', function(e){
  if (!('ontouchstart' in window)) { // Test for non-touch devices
    // Non-touch devices should use the standard behavior! Since they have hover.
    return;
  }
  // First hide all other navs, then show this one
  var $thisElement = $($(this).data('for'));
  var $thisTrigger = $(this);
  hideNav(navItems.not($thisElement), navTriggers.not($thisTrigger));
  toggleNav($thisElement, $thisTrigger);
  if ($thisElement.hasClass('visible')) {
    showOverlay($overlay);
  } else {
    hideOverlay($overlay);
  }
  // Only set max height on user nav dropdowns. The site-nav dropdowns handle this differently.
  if ($thisElement.is('#user-nav .dropdown ul')) {
    setMaxHeight($thisElement, window.innerHeight - 42); // Only 1 nav-bar high
  }
  e.preventDefault();
  return false;
});
$overlay.on('click touchend', function(e){
  hideNav(navItems, navTriggers);
  hideOverlay(this);
  e.preventDefault();
  return false;
});

/*
Here, we control the behavior of a toggle-able site-wide navigation.
On large screen sizes, the list of dropdowns doesn't need to be toggled.
On smaller screen sizes, the list of dropdowns is hidden behind a toggle.
Then, each dropdown menu is displayed by hiding the other dropdown options
while showing the elements present in that dropdown.
*/
$('.section-list .dropdown > .nav-item').click(function(e){
  // We only want the nav-item to be triggerable when the dropdown is visible
  // and if it contains some list to drop down.
  var menuIsVisible = $('#toggle-sections').is('.active');
  var section = $(this).parent();
  var otherSections = section.siblings();
  var dropdown = section.children('ul');
  if (menuIsVisible && dropdown.length > 0) {
    otherSections.toggleClass('hidden');
    toggleNav(dropdown, section);
    var offsetTop = 42 * 2; // The dropdown is always beneath two 42px tall menus
    setMaxHeight(dropdown, window.innerHeight - offsetTop);
    e.preventDefault();
    return false;
  }
});

// Global nav search field
$('#show-search').click(function(){
  var searchButton = this;
  var search = '.global-search';
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
