export function modal(nextSelector) {
    var overlay = '#modal-overlay';
    $(overlay).addClass('visible');
    $(nextSelector).addClass('visible');
    $(overlay).click(function(){
        $(overlay).removeClass('visible');
        $(nextSelector).removeClass('visible');
    });
    $('.close-modal').click(function(){
        $(overlay).removeClass('visible');
        $(nextSelector).removeClass('visible');
    });
}
