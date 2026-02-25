/* account.js
**
*/

import $ from 'jquery';

$('document').ready(function(){
  $('.api-token a').click(function(e) {
    e.preventDefault();
    $(this).hide();
    $('.api-token input').show();
  });
});
