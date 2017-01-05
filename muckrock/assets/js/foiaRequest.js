/* foiaRequest.js
**
** Provides functionality on the request page.
**
** TODO:
** Much of this can and should be refactored into more general functions,
** then applied to the specific selectors.
*/

import modal from './modal';

$('.hidden-reply').hide();

function textAreaModal(nextSelector) {
    modal(nextSelector);
    $('<textarea name="text"></textarea>').insertBefore(nextSelector.children('button'));
    $('#modal-overlay').click(function(){
        nextSelector.children('textarea').remove();
    });
    $('.close-modal').click(function(){
        nextSelector.children('textarea').remove();
    });
}

/* eslint-disable no-unused-vars */
// Let's keep this around for when we need to fetch thumbnails.
function get_thumbnail(doc_id) {
        var idx = doc_id.indexOf('-');
        var num = doc_id.slice(0, idx);
        var name = doc_id.slice(idx + 1);
        return 'https://s3.amazonaws.com/s3.documentcloud.org/documents/' + num + '/pages/' + name + '-p1-small.gif';
}
/* eslint-enable no-unused-vars */

/* Side Bar */

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

$('#toggle-communication-collapse').click(function(){
    var onText = 'Expand All';
    var offText = 'Collapse All';
    var state = $(this).data('state');
    var communications = $('.communications .communication');
    if (state === 0) {
        communications.addClass('collapsed');
        $(this).data('state', 1);
        $(this).text(onText);
    }
    else {
        communications.removeClass('collapsed');
        $(this).data('state', 0);
        $(this).text(offText);
    }
});

/* Request action composer */

var composers = $('.composer');

function showComposer(id) {
    // if no id provided, use the inactive panel
    id = !id ? '#inactive' : id;
    // hide all the composers, then filter to
    // the one we're interested in and show it
    var composer = composers.hide().filter(id).show();
    // We also want to bring the composer's first input into focus
    // in order to make it clear to the user that this is actionable
    composer.find(':text,textarea,select').filter(':visible:first').focus();
}

// Bind to hashchange event
$(window).on('hashchange', function () {
    // check if the hash is a target
    var hash = location.hash;
    var targetComposer = composers.filter(hash);
    if (targetComposer.length > 0) {
        showComposer(hash);
    }
});

// Initialize
$(document).ready(function(){
    showComposer(composers.filter(location.hash).length > 0 ? location.hash : '');
});

/* Documents */

export function displayFile(file) {
    if (!file) {
        return;
    }
    file = $(file);
    var activeFile = $('.active-document');
    var files = $('.file');
    var docId = file.data('doc-id');
    var title = file.data('title') || 'Untitled';
    var pages = file.data('pages') || 0;
    $('#doc-title').empty().text(title);
    $('#doc-pages').empty().text(pages);
    // remove the active class from all the list items,
    // then apply active class to this file's list item
    files.parent('li').removeClass('active');
    files.filter(file).parent('li').addClass('active');
    var docCloudSettings = {sidebar: false, container: "#viewer"};
    /* DV is defined by the external DocumentCloud script at runtime. */
    DV.load('https://www.documentcloud.org/documents/' + docId + '.js', docCloudSettings);
    activeFile.addClass('visible');
    window.scrollTo(0, 0);
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
    };
    var handleSuccess = function(data) {
        var newLink = window.location.origin + window.location.pathname + '?key=' + data.key;
        $(linkDisplay).val(newLink);
        flashLinkDisplay();
    };
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

$('.modal-link').click(function(e){
    e.preventDefault();
    textAreaModal($($(this).data('modal')));
    return false;
});
