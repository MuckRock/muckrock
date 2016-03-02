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

function get_thumbnail(doc_id) {
        var idx = doc_id.indexOf('-');
        var num = doc_id.slice(0, idx);
        var name = doc_id.slice(idx + 1);
        return 'https://s3.amazonaws.com/s3.documentcloud.org/documents/' + num + '/pages/' + name + '-p1-small.gif';
}

/* Side Bar */

$('#toggle-specific-information').click(function(e){
    e.preventDefault();
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

$('#thanks').click(function(e){
    e.preventDefault();
    composeResponse(this, '.thanks.composer-input');
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

function displayFile(file) {
    var activeFile = $('.active-document');
    var files = $('.file');
    if (!file) {
        return
    }
    var title = file.data('title');
    var docId = file.data('doc-id');
    if (!title) {
        title = 'Untitled';
    }
    $('#doc-title').empty().text(title);
    // remove the active class from all the list items,
    // then apply active class to this file's list item
    files.parent('li').removeClass('active');
    files.filter(file).parent('li').addClass('active');
    docCloudSettings = {sidebar: false, container: "#viewer"}
    DV.load('https://www.documentcloud.org/documents/' + docId + '.js', docCloudSettings);
    activeFile.addClass('visible');
    window.scrollTo(0, activeFile.offset().top);
}

$('.view-file').click(function() {
    // We force a hashchange when the view-file link is clicked.
    $(window).trigger('hashchange');
    window.scrollTo(0, $('.active-document').offset().top);

});

$('.active-document').find('.cancel.button').click(function(){
    var activeFile = $('.active-document');
    var files = $('.file');
    $('#viewer').empty();
    activeFile.removeClass('visible');
    files.parent('li').removeClass('active');
    console.log('Closed file');
});

$('.toggle-embed').click(function(){
    var file = $(this).closest('.file');
    var embed = $(file).find('.file-embed');
    $(embed).toggleClass('visible');
    $(embed).children('textarea').select();
    $(embed).children('.close-embed').click(function(){
        $(embed).removeClass('visible');
    });
});

/* Notes */

$('.note-header').click(function(){
    $(this).parent().toggleClass('collapsed');
});

/* Sharing */

var foiaId = $('.request.detail').attr('id');
if (foiaId != undefined) {
    foiaId = foiaId.substring(foiaId.indexOf('-') + 1);
}
if ($('#id_users-autocomplete').length) {
    $('#id_users-autocomplete').yourlabsAutocomplete().data = {
        foiaId: foiaId
    }
}

// Generate private link with AJAX

$('form.generate-private-link').submit(function(e){
    e.preventDefault();
    var linkDisplay = $(this).children('input[type=text]');
    var dataToSubmit = 'action=generate_key';
    var flashLinkDisplay = function() {
        $(linkDisplay).addClass('success');
        window.setTimeout(function(){
            $(linkDisplay).removeClass('success');
        }, 500);
    }
    var handleSuccess = function(data, status, jqXHR) {
        var newLink = window.location.origin + window.location.pathname + '?key=' + data.key;
        $(linkDisplay).val(newLink);
        flashLinkDisplay();
    }
    $.ajax({
        method: 'POST',
        data: dataToSubmit,
        success: handleSuccess
    });
});

/* Modals */

$('.text-area.modal-button').click(function(e){
    e.preventDefault();
    textAreaModal($(this).next());
    return false;
});
