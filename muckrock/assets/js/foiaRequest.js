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

/* eslint-disable no-unused-vars */
// Let's keep this around for when we need to fetch thumbnails.
function get_thumbnail(doc_id) {
        var idx = doc_id.indexOf('-');
        var num = doc_id.slice(0, idx);
        var name = doc_id.slice(idx + 1);
        return 'https://assets.documentcloud.org/documents/' + num + '/pages/' + name + '-p1-small.gif';
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

$('.tracking-id.edit').click(function(){
  var button = $(this);
  button.hide();
  $('.add-tracking-id').addClass('visible');
  $('.add-tracking-id .cancel').click(function(e){
    e.preventDefault();
    $('.add-tracking-id').removeClass('visible');
    button.show();
  });
});

$('.new-portal.edit').click(function(){
  var button = $(this);
  button.hide();
  $('.add-portal').addClass('visible');
  $('.add-portal .cancel').click(function(e){
    e.preventDefault();
    $('.add-portal').removeClass('visible');
    button.show();
  });
});

$('#show-portal-info').click(function(){
    $(this).hide();
    $('.portal-info').addClass('visible');
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
    var url = file.data('url');
    var iframe = $("#viewer-iframe");
    var viewer = $("#viewer");

    $('#doc-title').empty().text(title);
    $('#doc-pages').empty().text(pages);
    // remove the active class from all the list items,
    // then apply active class to this file's list item
    files.parent('li').removeClass('active');
    files.filter(file).parent('li').addClass('active');

    // load new embed in the iframe
    iframe.attr(
        "src",
        url + "/documents/" + docId + "/?embed=1&amp;title=1"
    );
    viewer.hide();
    iframe.show();

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

$('.file-form').click(function(){
    $(this).closest('form').submit();
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
    modal($(this).next());
    return false;
});

$('.modal-link.agency-flag').click(function(e){
    e.preventDefault();
    $("#id_flag-category").val($(this).data("category"));
    modal($($(this).data('modal')));
    return false;
});

$('.modal-link').click(function(e){
    e.preventDefault();
    modal($($(this).data('modal')));
    return false;
});

/* Agency Reply */

$("#agency-reply #id_price").parent().hide();

$("#agency-reply #id_status").change(function() {
  var help_texts = {
    "processed": "This is an acknowledgement or general update message.  A future communication will contain the results of the request.",
    "fix": "You require requester to fix their request - they may need to provide additional details or narrow the scope of the request so that you may continue processing it.",
    "payment": "You are notifying the requestor of the payment amount for the request.  Please fill in the price field with the price.",
    "rejected": "The request has been rejected.  Please cite all relevant exemptions.",
    "no_docs": "No responsive documents were found for the request.",
    "done": "The request is complete.  All responsive documents are attached and uploaded.",
    "partial": "Some of the responsive documents are attached and uploaded.  More documents will be sent in a future communication."
  };
  if ($(this).val() == "payment") {
    $("#agency-reply #id_price").parent().show();
  } else {
    $("#agency-reply #id_price").parent().hide();
  }
  $(this).next(".help-text").text(help_texts[$(this).val()]);
});
$("#agency-reply #id_status").trigger("change");

/* Communication Resend */

$(".resend-communication select.resend-via").change(function() {
  if ($(this).val() == "portal" || $(this).val() == "snail") {
    $(this).siblings(".resend-email").next().hide();
    $(this).siblings(".resend-fax").next().hide();
  } else if ($(this).val() == "email") {
    $(this).siblings(".resend-email").next().show();
    $(this).siblings(".resend-fax").next().hide();
  } else if ($(this).val() == "fax") {
    $(this).siblings(".resend-email").next().hide();
    $(this).siblings(".resend-fax").next().show();
  }
});
$('document').ready(function(){
  $(".resend-communication select").trigger("change");
});
$(window).on('hashchange', function () {
  $(".resend-communication select").trigger("change");
});

/* Admin Fix */

$("#id_admin_fix-via").change(function() {
  if ($(this).val() == "portal" || $(this).val() == "snail") {
    $("#id_admin_fix-email").parent().hide();
    $("#id_admin_fix-other_emails").parent().hide();
    $("#id_admin_fix-fax").parent().hide();
  } else if ($(this).val() == "email") {
    $("#id_admin_fix-email").parent().show();
    $("#id_admin_fix-other_emails").parent().show();
    $("#id_admin_fix-fax").parent().hide();
  } else if ($(this).val() == "fax") {
    $("#id_admin_fix-email").parent().hide();
    $("#id_admin_fix-other_emails").parent().hide();
    $("#id_admin_fix-fax").parent().show();
  }
});
$("#id_admin_fix-via").trigger("change");

/* Bulk Actions */

$('document').ready(function(){
  $("#request-actions .bulk").change(function() {
    $("#request-actions .help").removeClass("error");
    $("#request-actions button").removeClass("failure");
    $("#request-actions .project-form").hide();
    $("#request-actions .tag-form").hide();
    $("#request-actions .share-form").hide();
    $("#request-actions .owner-form").hide();
    $("#request-actions .crowdsource-form").hide();
    $("#request-actions .help").text($(this).find(":selected").data("help") || "");
    switch($(this).val()) {
      case "project":
        $("#request-actions .project-form").show();
        break;
      case "tags":
        $("#request-actions .tag-form").show();
        break;
      case "share":
        $("#request-actions .share-form").show();
        break;
      case "change-owner":
        $("#request-actions .owner-form").show();
        $("#request-actions .help").addClass("error");
        $("#request-actions button").addClass("failure");
        break;
      case "crowdsource":
      case "crowdsource_page":
        $("#request-actions .crowdsource-form").show();
        break;
    }
  });
  $("#request-actions .bulk").change();
});



/* Contact Info */

export default function showOrigContactInfo() {
  $(".contact-info").each(function() {
    var
    portalType = $(this).find(".info").data("portal-type"),
    portalURL = $(this).find(".info").data("portal-url"),
    email = $(this).find(".info").data("email"),
    ccEmails = $(this).find(".info").data("cc-emails"),
    fax = $(this).find(".info").data("fax"),
    address = $(this).find(".info").data("address"),
    type = $(this).find(".info").data("type");

    if (type === "portal") {
      $(this).find(".info span").text("will be submitted via a portal.");
    } else if (type === "email") {
      $(this).find(".info span").text("will be submitted via email.");
    } else if (type === "fax") {
      $(this).find(".info span").text("will be submitted via fax.");
    } else if (type === "snail") {
      $(this).find(".info span").text("will be submitted via mail.");
    } else if (type === "none") {
      $(this).find(".info span").text("currently has no valid contact information.  We will review it and find a suitable means of submitting it for you.");
    } else if (portalURL) {
      $(this).find(".info span").text(
        "will be submitted via the "
      ).append(
        portalType
      ).append(
        " portal, located at "
      ).append(
        portalURL
      ).append(".");
    } else if (email) {
      var html = "will be submitted via email to " + email;
      if (ccEmails.length > 0) {
        html += ", as well as CCed to:";
        for (var i = 0; i < ccEmails.length; i++) {
          html += `
            <div class="">
              <label>
                <input type="checkbox" name="cc_emails" value="${ccEmails[i]}" checked>
                ${ccEmails[i]}
              </label>
            </div>
          `;
        }
      } else {
        html += ".";
      }
      $(this).find(".info span").html(html);
    } else if (fax) {
      $(this).find(".info span").text(
        "will be submitted via fax to "
      ).append(
        fax
      ).append(".");
    } else if (address) {
      $(this).find(".info span").text(
        "will be submitted via mail to "
      ).append(
        address
      ).append(".");
    } else {
      $(this).find(".info span").text("currently has no valid contact information.  We will review it and find a suitable means of submitting it for you.");
    }
  });
}

$('document').ready(function(){

  $(".contact-info .see-where").click(function(e) {
    e.preventDefault();
    $(this).hide();
    $(this).siblings(".info").show();
  });

  $(".contact-info .change").click(function(e) {
    e.preventDefault();
    var $contactInfo = $(this).closest(".contact-info");
    $contactInfo.find(".form").show();
    $contactInfo.find(".change").hide();
    $contactInfo.find(".use_contact_information").val(true);

    $contactInfo.find(".email").change();
    $contactInfo.find(".fax").change();
    $contactInfo.find(".via").change();
  });
  $(".contact-info .cancel").click(function(e) {
    e.preventDefault();
    var $contactInfo = $(this).closest(".contact-info");
    $contactInfo.find(".form").hide();
    $contactInfo.find(".change").show();
    $contactInfo.find(".use_contact_information").val(false);
    $contactInfo.find(".other_email").removeAttr("required");
    $contactInfo.find(".other_fax").removeAttr("required");
    showOrigContactInfo();
  });
  showOrigContactInfo();

  $(".contact-info .via").change(function() {
    var $contactInfo = $(this).closest(".contact-info");
    if($(this).val() === "email") {
      $contactInfo.find(".email").parent().show();
      $contactInfo.find(".email").change();
    } else {
      $contactInfo.find(".email").parent().hide();
      $contactInfo.find(".other_email").parent().hide();
      $contactInfo.find(".other_email").val('');
      $contactInfo.find(".other_email").removeAttr("required");
    }
    if($(this).val() === "fax") {
      $contactInfo.find(".fax").parent().show();
      $contactInfo.find(".fax").change();
    } else {
      $contactInfo.find(".fax").parent().hide();
      $contactInfo.find(".other_fax").parent().hide();
      $contactInfo.find(".other_fax").val('');
      $contactInfo.find(".other_fax").removeAttr("required");
    }
    if($(this).val() === "snail") {
      if($contactInfo.find(".info").data("address")) {
        $contactInfo.find(".info span").text(
          "will be submitted via mail to " +
          $contactInfo.find(".info").data("address") + "."
        );
      } else {
        $contactInfo.find(".info span").text("will be submitted via mail.");
      }
    } else if($(this).val() == "portal") {
      var portal_url = $contactInfo.find(".info").data("portal-url");
      $contactInfo.find(".info span").text(
        "will be submitted via the "
      ).append(
        $contactInfo.find(".info").data("portal-type")
      ).append(
        " portal, located at "
      ).append(
        portal_url
      ).append(".");
    }
  });

  $(".contact-info .email").change(function() {
    var $contactInfo = $(this).closest(".contact-info");
    var full_email;
    if($(this).val() === "") {
      $contactInfo.find(".other_email").parent().show();
      $contactInfo.find(".other_email").attr("required", "required");
      full_email = $contactInfo.find(".other_email").val();
    } else {
      $contactInfo.find(".other_email").parent().hide();
      $contactInfo.find(".other_email").val('');
      $contactInfo.find(".other_email").removeAttr("required");
      full_email = $(this).children("option:selected").text();
    }

    $contactInfo.find(".info span").text(
      "will be submitted via email to " + full_email + "."
    );
  });
  $(".contact-info .other_email").on("input properychange paste", function() {
    var email = $(this).val();
    var $contactInfo = $(this).closest(".contact-info");
    $contactInfo.find(".info span").text(
      "will be submitted via email to " + email + "."
    );
  });

  $(".contact-info .fax").change(function() {
    var $contactInfo = $(this).closest(".contact-info");
    var fax;
    if($(this).val() === "") {
      $contactInfo.find(".other_fax").parent().show();
      $contactInfo.find(".other_fax").attr("required", "required");
      fax = $contactInfo.find(".other_fax").val();
    } else {
      $contactInfo.find(".other_fax").parent().hide();
      $contactInfo.find(".other_fax").val('');
      $contactInfo.find(".other_fax").removeAttr("required");
      fax = $(this).children("option:selected").text();
    }
    $contactInfo.find(".info span").text(
      "will be submitted via fax to " + fax + "."
    );
  });
  $(".contact-info .other_fax").on("input properychange paste", function() {
    var fax = $(this).val();
    var $contactInfo = $(this).closest(".contact-info");
    $contactInfo.find(".info span").text(
      "will be submitted via fax to " + fax + "."
    );
  });

  $("#appeal-button").click(function() {
    /* eslint-disable no-undef */
    mixpanel.track('Appeal');
    /* eslint-enable no-undef */
  });

});

$(".raw-content-button").click(function(e) {
  $(".raw-content").hide();
  $(e.target.attributes.href.value).show();
  e.preventDefault();
});

