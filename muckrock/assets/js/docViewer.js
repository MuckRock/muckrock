import $ from 'jquery';

import '../css/tokens.css';
import '../css/docViewer.css';

$('.toggle-embed').click(function(){
    const embed = $('.file-embed');
    $(embed).toggleClass('visible');
    $(embed).children('textarea').select();
    $(embed).children('.close-embed').click(function(){
        $(embed).removeClass('visible');
    });
});
