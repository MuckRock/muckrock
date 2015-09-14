$('.hidden-reply').hide();
$('.embed textarea').trigger('autosize.destroy');

function textAreaModal(nextSelector) {
    modal(nextSelector);
    $('<textarea name="text"></textarea>').insertBefore(nextSelector.children('button'));
    $('#modal-overlay').click(function(){
        console.log('Click!');
        nextSelector.children('textarea').remove();
    });
    $('.close-modal').click(function(){
        nextSelector.children('textarea').remove();
    });
}

function textAreaReply(nextSelector) {
    console.log(nextSelector);
    nextSelector.show();
    $('.reply-button').hide();
    $('.modal-button').hide();
    nextSelector.siblings('.hidden-reply:visible').hide();
    if (nextSelector.children('textarea').length == 0) {
        $('<textarea name="text"></textarea>').insertBefore(nextSelector.children('.buttons'));
    }
    nextSelector.children('.buttons').children('.close-reply').click(function(){
        nextSelector.hide();
        nextSelector.children('textarea').remove();
        $('.reply-button').show();
        $('.modal-button').show();
    });
}

function hideAllExcept(visible) {
    $('.tab-section').removeClass( 'active' );
    visible.addClass( 'active' );
}

function get_thumbnail(doc_id) {
        var idx = doc_id.indexOf('-');
        var num = doc_id.slice(0, idx);
        var name = doc_id.slice(idx + 1);
        return 'https://s3.amazonaws.com/s3.documentcloud.org/documents/' + num + '/pages/' + name + '-p1-small.gif';
}

function displayDoc(docId, docTitle, docAnchor) {
    var title;
    if (!!docTitle) {
        title = docTitle;
    } else {
        title = 'Untitled';
    }
    $('#doc-title').empty().text(title);
    $('.file').parent('li').removeClass('active');
    if (!!docAnchor) {
        var fileListItem = $('#files ul li > #' + docAnchor).parent('li');
        $(fileListItem).addClass('active');
    }
    DV.load(
        'https://www.documentcloud.org/documents/' + docId + '.js',
        {
            sidebar: false,
            container: "#viewer"
        }
    );
}

function displayDefaultDoc() {
    var defaultDoc = $('a.view-file').first();
    if (!!defaultDoc) {
        var defaultDocId = defaultDoc.data('docId');
        var defaultDocTitle = defaultDoc.data('docTitle');
        var defaultDocAnchor = defaultDoc.data('docAnchor');
        displayDoc(defaultDocId, defaultDocTitle, defaultDocAnchor);
    }
}

/* Side Bar */

$('#toggle-specific-information').click(function(e){
    e.preventDefault();
    console.log('click');
    $('.specific-information').toggleClass('visible');
    if ($(this).data('state') == 0) {
        $(this).data('state', 1);
        $(this).text('Hide details');
    } else {
        $(this).data('state', 0);
        $(this).text('Show details');
    }
});

$('.estimated-completion .edit').click(function(){
    var button = $(this);
    $('.dates').hide();
    $('.change-date').addClass('visible');
    $('.change-date .cancel').click(function(e){
        e.preventDefault();
        $('.change-date').removeClass('visible');
        $('.dates').show();
        $(button).show();
    });
});

/* Tab Bar */

$('#tab-overview').click(function() {
    $(this).addClass('active');
    $(this).siblings().removeClass('active');
    $('#overview').addClass('visible');
    $('#overview').siblings().removeClass('visible');
});

$('#tab-request').click(function() {
    $(this).addClass('active');
    $(this).siblings().removeClass('active');
    $('#request').addClass('visible');
    $('#request').siblings().removeClass('visible');
});

$('#tab-files').click(function() {
    $(this).addClass('active');
    $(this).siblings().removeClass('active');
    $('#files').addClass('visible');
    $('#files').siblings().removeClass('visible');
});

$('#tab-notes').click(function() {
    $(this).addClass('active');
    $(this).siblings().removeClass('active');
    $('#notes').addClass('visible');
    $('#notes').siblings().removeClass('visible');
});

$('#tab-tasks').click(function() {
    $(this).addClass('active');
    $(this).siblings().removeClass('active');
    $('#tasks').addClass('visible');
    $('#tasks').siblings().removeClass('visible');
});

/* Deep link into tab */

var target = window.location.hash;
var n = target.indexOf('-');
target = target.substring(0, n != -1 ? n : target.length);
if (target == '#comm' || target == '#comms') {
    $('#tab-request').trigger('click');
} else if (target == '#file' || target == '#files') {
    $('#tab-files').trigger('click');
} else if (target == '#note' || target == '#notes') {
    $('#tab-notes').trigger('click');
}

/* Communications */

$('#toggle-communication-collapse').click(function(e){
    var state = $(this).data('state');
    var tab = $(this).closest('.tab-section.communications');
    var communications = $(tab).find('.communications-list').children();
    if (state == 0) {
        $(communications).addClass('collapsed');
        $(this).data('state', 1);
        $(this).text('Expand All');
    }
    else {
        $(communications).removeClass('collapsed');
        $(this).data('state', 0);
        $(this).text('Collapse All');
    }
});

/* Follow up and appeal */

var composeResponse = function(target, composerForm) {
    var composer = $(target).closest('.communications-composer');
    var inactiveComposerForm = $(composer).find('.inactive.composer-input');
    var activeComposerForm = $(composer).find(composerForm);
    $(activeComposerForm).siblings().removeClass('visible');
    $(activeComposerForm).addClass('visible');
    var textarea = $(activeComposerForm).children('textarea');
    $(textarea).focus();
    $(activeComposerForm).find('.button.cancel').click(function(e){
        e.preventDefault();
        $(inactiveComposerForm).siblings().removeClass('visible');
        $(inactiveComposerForm).addClass('visible');
    });
}

$('#follow-up').click(function(e){
    e.preventDefault();
    composeResponse(this, '.follow-up.composer-input');
});

$('#appeal').click(function(e){
    e.preventDefault();
    composeResponse(this, '.appeal.composer-input');
});

$('.inactive.composer-input').click(function(){
    $('#follow-up').click();
});

$('#inactive-appeal').click(function(){
    $('#appeal').click();
    return false;
});

/* Documents */

$('a.view-file').click(function() {
    var docId = $(this).data('docId');
    var docTitle = $(this).data('docTitle');
    var docAnchor = $(this).data('docAnchor');
    $('#files-radio').trigger('click');
    displayDoc(docId, docTitle, docAnchor);
});

if (target == '#file') {
    var specificFile = window.location.hash;
    $(specificFile + ' .view-file').trigger('click');
}

/* Modals */

$('.text-area.modal-button').click(function(e){
    e.preventDefault();
    textAreaModal($(this).next());
    return false;
});

/* CHECKOUT */

$('.checkout-button').click(function(e){
    e.preventDefault();
    var checkoutData = getCheckoutData($(this));
    checkout(
        "{{ stripe_pk }}",
        "{% static 'apple-touch-icon.png' %}",
        checkoutData.description,
        checkoutData.amount,
        checkoutData.email,
        checkoutData.label,
        checkoutData.form
    );
    return false;
});
