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
        console.log('cleeek');
        $(this).parent().parent().hide();
    });
});