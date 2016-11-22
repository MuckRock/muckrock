import $ from 'jquery';

import '../scss/docViewer.scss';

$('.toggle-embed').click(function(){
    const embed = $('.file-embed');
    $(embed).toggleClass('visible');
    $(embed).children('textarea').select();
    $(embed).children('.close-embed').click(function(){
        $(embed).removeClass('visible');
    });
});
