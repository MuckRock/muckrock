/* account.js
**
** This prevents the verify email button from being used after
** the user changes their email but before they save the change.
*/

var $email = $('.account.settings #id_email');
var $verify = $('.account.settings #verify_email');
var oldEmail = $email.val();
var verifyHref = $verify.attr('href');
$email.change(function(){
    var newEmail = $(this).val();
    if (newEmail != oldEmail) {
        $verify.addClass('disabled').removeAttr('href');
    } else {
        $verify.removeClass('disabled').attr('href', verifyHref);
    }
});
