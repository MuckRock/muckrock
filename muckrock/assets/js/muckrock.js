function modal(nextSelector) {
    var overlay = '#modal-overlay';
    $(overlay).addClass('visible');
    $(nextSelector).addClass('visible');
    $(overlay).click(function(){
        $(overlay).removeClass('visible');
        $(nextSelector).removeClass('visible');
    });
    $('.close-modal').click(function(){
        $(overlay).removeClass('visible');
        $(nextSelector).removeClass('visible');
    });
}

function checkout(pk, image, description, amount, email, label, form, submit) {
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
        panelLabel: label,
        token: token,
        bitcoin: true
    });
}

function getCheckoutData(button) {
    var amount = button.data('amount');
    var description = button.data('description');
    var email = button.data('email');
    var form = button.data('form');
    var label = button.data('label');
    return {
        'amount': amount,
        'description': description,
        'email': email,
        'label': label,
        'form': $(form)
    }
}

// $('textarea').autosize();

if (typeof $.cookie('broadcast') == 'undefined') {
    $.cookie('broadcast', 1);
}

// MODALS
$('.modal-button').click(function(){ modal($(this).next()); });
$('.embed.hidden-modal').each(function() {
    var textarea = $(this).children('textarea');
    var doc_id = textarea.data('docId');
    var embed = '<div class="viewer" id="viewer-' + doc_id + '"></div> <script src="https://s3.amazonaws.com/s3.documentcloud.org/viewer/loader.js"><\/script> <script>DV.load("https://www.documentcloud.org/documents/' + doc_id + '.js", {width: 600, height: 600, sidebar: false, container: "#viewer-' + doc_id + '"});<\/script>';
    textarea.val(embed);
});

// SELECT ALL
$('#toggle-all').click(function(){
    var toggleAll = this;
    $(':checkbox').not('#toggle-all').each(function(){
        $(this).click(function(){
            toggleAll.checked = false;
        });
        if (!$(this).data('ignore-toggle-all')) {
            this.checked = toggleAll.checked;
        }
    });
});

// Tag Manager

$('#edit-tags').click(function() {
    var editButton = this;
    var tagManager = $(editButton).closest('.tag-manager');
    var tagForm = $(tagManager).find('.tag-form');
    var tagList = $(tagManager).find('.tag-list');
    $(tagForm).addClass('visible');
    $(editButton).hide();
    $(tagList).hide();
    $('#cancel-tags').click(function(e){
        e.preventDefault();
        $(tagForm).removeClass('visible');
        $(editButton).show();
        $(tagList).show();
    });
});

// Status Manager

$('#edit-status').click(function() {
    var editButton = this;
    var statusManager = $(editButton).closest('.status-manager');
    var statusForm = $(statusManager).find('.status-form');
    var statusTag = $(statusManager).find('.status');
    $(statusForm).addClass('visible');
    $(statusTag).hide();
    $(editButton).hide();
    $('#cancel-status').click(function(e){
        e.preventDefault();
        console.log('cancel');
        $(statusForm).removeClass('visible');
        $(statusTag).show();
        $(editButton).show();
    });
});

// MESSAGES
$('.message .visibility').click(function() {
    var header = $(this).parent();
    var message = header.siblings();
    message.toggle();
    if ($(this).hasClass('expanded')) {
        $(this).removeClass('expanded').addClass('collapsed');
        header.addClass('collapsed');
        $(this).html('&#9654;');
    } else {
        $(this).removeClass('collapsed').addClass('expanded');
        header.removeClass('collapsed');
        $(this).html('&#9660;');
    }
});

// formsets
$(function() {
	$('.formset-container').formset();
});

var urlParam = function(name){
    var urlString = '[\\?&amp;]' + name + '=([^&amp;#]*)'
    var results = new RegExp(urlString).exec(window.location.search);
    if (results) {
        return results[1] || 0;
    } else {
        return 0;
    }
}

$.expr[":"].icontains = $.expr.createPseudo(function(arg) {
    return function( elem ) {
        return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
});

$('#website-sections-dropdown').click(function(){
    var menu = 'ul.website-sections';
    var overlay = '#modal-overlay';
    $(menu).toggleClass('visible');
    $(overlay).toggleClass('visible');
    $(overlay).click(function(e) {
        $(menu).removeClass('visible');
        $(overlay).removeClass('visible');
    });
});

$('#sidebar-button').click(function(){
    var overlay = '#modal-overlay';
    var sidebar = '#website-sidebar';
    $(sidebar).addClass('visible');
    $(overlay).addClass('visible');
    $(overlay).click(function(){
        $(sidebar).removeClass('visible');
        $(overlay).removeClass('visible');
    });
});

$('#show-search').click(function(){
    var search = '#global-search';
    var closeSearch = '#hide-search';
    var searchInput = $(search).children('input[type="search"]');
    $(search).toggleClass('visible');
    if ($(search).hasClass('visible')) {
        searchInput.focus();
    } else {
        searchInput.blur()
    }
    $(closeSearch).click(function(){
        $(search).removeClass('visible');
    });
});
