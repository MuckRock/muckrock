/* dropdown.js
**
** Provides the logic for displaying dropdown menus.
*/

var dropdowns = $('.dropdown');

$('.dropdown .icon, .dropdown .dropdown-trigger').click(function(){
    var thisDropdown = $(this).closest('.dropdown');
    var thisDropdownState = thisDropdown.hasClass('visible');
    // Remove visible to all dropdowns, then make this dropdown visible
    // if it was hidden before. If it was visible already, keep it hidden.
    dropdowns.removeClass('visible');
    if (!thisDropdownState) {
        thisDropdown.addClass('visible');
    }
    // If we click anywhere else on the document, the dropdown should hide.
    $(document).click(function(){
        dropdowns.removeClass('visible');
    });
    return false;
});
