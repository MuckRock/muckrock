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
    modal($(this).next());
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

$(".resend-communication select").change(function() {
  if ($(this).val() == "portal" || $(this).val() == "snail") {
    $(this).siblings("#id_email-wrapper").hide();
    $(this).siblings("#id_fax-wrapper").hide();
  } else if ($(this).val() == "email") {
    $(this).siblings("#id_email-wrapper").show();
    $(this).siblings("#id_fax-wrapper").hide();
  } else if ($(this).val() == "fax") {
    $(this).siblings("#id_email-wrapper").hide();
    $(this).siblings("#id_fax-wrapper").show();
  }
});
$(".resend-communication select").trigger("change");

/* Admin Fix */

$("#id_admin_fix-via").change(function() {
  if ($(this).val() == "portal" || $(this).val() == "snail") {
    $("#id_admin_fix-email-wrapper").parent().hide();
    $("#id_admin_fix-other_emails").parent().hide();
    $("#id_admin_fix-fax-wrapper").parent().hide();
  } else if ($(this).val() == "email") {
    $("#id_admin_fix-email-wrapper").parent().show();
    $("#id_admin_fix-other_emails").parent().show();
    $("#id_admin_fix-fax-wrapper").parent().hide();
  } else if ($(this).val() == "fax") {
    $("#id_admin_fix-email-wrapper").parent().hide();
    $("#id_admin_fix-other_emails").parent().hide();
    $("#id_admin_fix-fax-wrapper").parent().show();
  }
});
$("#id_admin_fix-via").trigger("change");

/* Bulk Actions */

$('document').ready(function(){
  $("#request-actions .bulk").change(function() {
    $("#request-actions .project-form").hide();
    $("#request-actions .tag-form").hide();
    $("#request-actions .share-form").hide();
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
      case "crowdsource":
        $("#request-actions .crowdsource-form").show();
        break;
    }
  });
  $("#request-actions .bulk").change();
});



/* Contact Info */

function formatCC(ccEmails) {
  if (ccEmails.length == 1) {
    return ccEmails[0];
  } else {
    return ccEmails.slice(0, -1).join(" ,") + " and " + ccEmails[ccEmails.length - 1];
  }
}

export default function showOrigContactInfo() {
  var
  portalType = $(".contact-info .info").data("portal-type"),
  portalURL = $(".contact-info .info").data("portal-url"),
  email = $(".contact-info .info").data("email"),
  ccEmails = $(".contact-info .info").data("cc-emails"),
  fax = $(".contact-info .info").data("fax"),
  address = $(".contact-info .info").data("address"),
  type = $(".contact-info .info").data("type");

  if (type === "portal") {
    $(".contact-info .info span").text("will be submitted via a portal.");
  } else if (type === "email") {
    $(".contact-info .info span").text("will be submitted via email.");
  } else if (type === "fax") {
    $(".contact-info .info span").text("will be submitted via fax.");
  } else if (type === "snail") {
    $(".contact-info .info span").text("will be submitted via mail.");
  } else if (type === "none") {
    $(".contact-info .info span").text("currently has no valid contact information.  We will review it and find a suitable means of submitting it for you.");
  } else if (portalURL) {
    $(".contact-info .info span").text(
      "will be submitted via the "
    ).append(
      portalType
    ).append(
      " portal, located at "
    ).append(
      portalURL
    ).append(".");
  } else if (email) {
    var text = "will be submitted via email to " + email;
    if (ccEmails.length > 0) {
      text += ", as well as CCed to " + formatCC(ccEmails);
    }
    text += ".";
    $(".contact-info .info span").text(text);
  } else if (fax) {
    $(".contact-info .info span").text(
      "will be submitted via fax to "
    ).append(
      fax
    ).append(".");
  } else if (address) {
    $(".contact-info .info span").text(
      "will be submitted via mail to "
    ).append(
      address
    ).append(".");
  } else {
    $(".contact-info .info span").text("currently has no valid contact information.  We will review it and find a suitable means of submitting it for you.");
  }

}

$('document').ready(function(){

  $(".contact-info .see-where").click(function(e) {
    e.preventDefault();
    $(".contact-info .see-where").hide();
    $(".contact-info .info").show();
  });

  $(".contact-info .change").click(function(e) {
    e.preventDefault();
    $(".contact-info .form").show();
    $(".contact-info .change").hide();
    $("#id_use_contact_information").val(true);

    $(".contact-info #id_email").change();
    $(".contact-info #id_fax").change();
    $(".contact-info #id_via").change();
  });
  $(".contact-info .cancel").click(function(e) {
    e.preventDefault();
    $(".contact-info .form").hide();
    $(".contact-info .change").show();
    $("#id_use_contact_information").val(false);
    $(".contact-info #id_other_email").removeAttr("required");
    $(".contact-info #id_other_fax").removeAttr("required");
    showOrigContactInfo();
  });
  showOrigContactInfo();

  $(".contact-info #id_via").change(function() {
    if($(this).val() === "email") {
      $(".contact-info #id_email").parent().show();
      $(".contact-info #id_email").change();
    } else {
      $(".contact-info #id_email").parent().hide();
      $(".contact-info #id_other_email").parent().hide();
      $(".contact-info #id_other_email").val('');
      $(".contact-info #id_other_email").removeAttr("required");
    }
    if($(this).val() === "fax") {
      $(".contact-info #id_fax").parent().show();
      $(".contact-info #id_fax").change();
    } else {
      $(".contact-info #id_fax").parent().hide();
      $(".contact-info #id_other_fax").parent().hide();
      $(".contact-info #id_other_fax").val('');
      $(".contact-info #id_other_fax").removeAttr("required");
    }
    if($(this).val() === "snail") {
      if($(".contact-info .info").data("address")) {
        $(".contact-info .info span").text(
          "will be submitted via mail to " +
          $(".contact-info .info").data("address") + "."
        );
      } else {
        $(".contact-info .info span").text("will be submitted via mail.");
      }
    } else if($(this).val() == "portal") {
      var portal_url = $(".contact-info .info").data("portal-url");
      $(".contact-info .info span").text(
        "will be submitted via the "
      ).append(
        $(".contact-info .info").data("portal-type")
      ).append(
        " portal, located at "
      ).append(
        portal_url
      ).append(".");
    }
  });

  $(".contact-info #id_email").change(function() {
    var full_email;
    if($(this).val() === "") {
      $(".contact-info #id_other_email").parent().show();
      $(".contact-info #id_other_email").attr("required", "required");
      full_email = $(".contact-info #id_other_email").val();
    } else {
      $(".contact-info #id_other_email").parent().hide();
      $(".contact-info #id_other_email").val('');
      $(".contact-info #id_other_email").removeAttr("required");
      full_email = $(this).children("option:selected").text();
    }

    $(".contact-info .info span").text(
      "will be submitted via email to " + full_email + "."
    );
  });
  $(".contact-info #id_other_email").on("input properychange paste", function() {
    var email = $(this).val();
    $(".contact-info .info span").text(
      "will be submitted via email to " + email + "."
    );
  });

  $(".contact-info #id_fax").change(function() {
    var fax;
    if($(this).val() === "") {
      $(".contact-info #id_other_fax").parent().show();
      $(".contact-info #id_other_fax").attr("required", "required");
      fax = $(".contact-info #id_other_fax").val();
    } else {
      $(".contact-info #id_other_fax").parent().hide();
      $(".contact-info #id_other_fax").val('');
      $(".contact-info #id_other_fax").removeAttr("required");
      fax = $(this).children("option:selected").text();
    }
    $(".contact-info .info span").text(
      "will be submitted via fax to " + fax + "."
    );
  });
  $(".contact-info #id_other_fax").on("input properychange paste", function() {
    var fax = $(this).val();
    $(".contact-info .info span").text(
      "will be submitted via fax to " + fax + "."
    );
  });

});
