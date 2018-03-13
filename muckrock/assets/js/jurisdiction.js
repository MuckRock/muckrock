
/* jurisdiction.js
 **
 ** Provides functionality on the interactive map page
 **
 */

$(document).ready(function(){

  $("#map-stat").change(function() {
    $(".state").removeClass("yes");
    $(".state").removeClass("no");
    var select = this;
    $(".state").each(function() {
      if ($(this).data($(select).val()) === "True") {
        $(this).addClass("yes");
      } else {
        $(this).addClass("no");
      }
    });
  });
  $("#map-stat").change();

});
