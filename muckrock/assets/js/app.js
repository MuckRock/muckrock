function modal(nextSelector) {
    var overlay = '<div class="overlay"></div>';
    $(overlay).insertBefore($('.container')).fadeIn();
    nextSelector.removeClass('hidden-modal').addClass('modal');
    $('.overlay').click(function(){
        $('.overlay').fadeOut().remove();
        $('.modal').removeClass('modal').addClass('hidden-modal');
    });
}

$(document).ready(function() {

    /* Key and Swipe Bindings
    $(document).bind('keydown', 'm', toggleSidebar());
    $(document).bind('keydown', 'shift+m', toggleSidebar());
    $(document).bind('keydown', 'left', toggleSidebar());
    $(document).bind('keydown', 'right', toggleSidebarOff());
    $(document).bind('keydown', 'esc', toggleSidebarOff());
    // swipe left to toggle sidebar on
    // swipe right to toggle sidebar off

    // Sidebar Interactions
    //
    // if sidebar is open
    //      on clicking or tapping div.container or div.footer-container:
    //          sidebar closes
    //      on clicking or tapping a.menu-button:
    //          sidebar closes
    //          a.menu-button content changes
    // if sidebar is closed
    //      on clicking or tapping a.menu-button:
    //          sidebar opens
    //          a.menu-button content changes
    */
    
    $('.notification button.close').click(function() {
        $(this).parent().parent().hide();
    });
    
    $('.modal-button').click(function(){ modal($(this).next()); });
});