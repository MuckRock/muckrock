function modal(nextSelector) {
    var overlay = '<div class="overlay"></div>';
    $(overlay).insertBefore($('.container')).fadeIn();
    nextSelector.removeClass('hidden-modal').addClass('modal');
    $('.overlay').click(function(){
        $('.overlay').fadeOut().remove();
        $('.modal').removeClass('modal').addClass('hidden-modal');
    });
}

function checkout(pk, image, description, amount, email, form, submit) {
    submit = typeof submit !== 'undefined' ? submit : true;
    var token = function(token) {
        form.append('<input type="hidden" name="stripe_token" value="' + token.id + '" />');
        form.append('<input type="hidden" name="stripe_email" value="' + token.email + '" />');
        $('a').click(function() { return false; });
        $('button').click(function() { return false; });
        if (submit) {
            form.submit();
        }
    }
    StripeCheckout.open({
        key: pk,
        image: image,
        name: 'MuckRock',
        description: description,
        amount: amount,
        email: email,
        token: token
    });
}

function getCheckoutData(button) {
    var amount = button.data('amount');
    var description = button.data('description');
    var email = button.data('email');
    var form = button.data('form');
    return {
        'amount': amount,
        'description': description,
        'email': email,
        'form': $(form)
    }
}

$(document).ready(function() {

    $('.modal-button').click(function(){ modal($(this).next()); });
    $('.embed.hidden-modal').each(function() {
        var textarea = $(this).children('textarea');
        var doc_id = textarea.data('docId');
        var embed = '<div id="viewer-' + doc_id + '"></div><script src="https://s3.amazonaws.com/s3.documentcloud.org/viewer/loader.js"><\/script><script>DV.load("https://www.documentcloud.org/documents/' + doc_id + '.js", { height: 600, sidebar: false, container: "#viewer-' + doc_id + '"});<\/script>';
        textarea.val(embed);
    });    
    $('.notification button.close').click(function() {
        $(this).parent().parent().hide();
    });
    
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
    
});