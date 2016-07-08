import 'jquery-ui/datepicker';

import './account';
import './autocomplete';
import './checkout';
import './communication';
import './crowdfund';
import './currencyField';
import './dropdown';
import './editor';
import './foiaRequest';
import './formset';
import './list';
import './loupe';
import './quicksearch';
import './tabs';
import './task';

// FLAG FORM
$('#show-flag-form').click(function(){
    var thisButton = $(this);
    $(thisButton).hide();
    var flagForm = $(this).next();
    $(flagForm).addClass('visible').find('.cancel.button').click(function(){
        $(thisButton).show();
        $(flagForm).removeClass('visible');
    });
});

// Manager Component
// A manager presents a state and a form that can modify that state.
$('.manager .action').click(function(){
    var editButton = this;
    var manager = $(editButton).closest('.manager');
    var form = $(manager).find('form');
    var display = $(manager).find('.state');
    $(form).addClass('visible');
    $(display).hide();
    $(editButton).hide();
    $(manager).find('.cancel').click(function(e){
        e.preventDefault();
        $(form).removeClass('visible');
        $(display).show();
        $(editButton).show();
    });
});

// MESSAGES
$('.message .visibility').click(function() {
    var header = $(this).parent();
    var message = header.siblings();
    message.toggle();
    if ($(this).hasClass('expanded')) {
        $(this).removeClass('expanded').addClass('collapsed');
        header.addClass('collapsed');
        $(this).html('&#9654;');
    } else {
        $(this).removeClass('collapsed').addClass('expanded');
        header.removeClass('collapsed');
        $(this).html('&#9660;');
    }
});

$('.formset-container').formset();

$.expr[":"].icontains = $.expr.createPseudo(function(arg) {
    return function( elem ) {
        return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
});

// COLLAPSABLE
$('.collapsable header').click(function(){
    $(this).parent().toggleClass('collapsed');
});
$('.collapsable header').children('.nocollapse').click(function(event){
    // Prevent click from propagating up to the collapsable header.
    event.stopPropagation();
});

$('#sidebar-button').click(function(){
    var overlay = '#modal-overlay';
    var sidebar = '#website-sidebar';
    $(sidebar).addClass('visible');
    $(overlay).addClass('visible');
    $(overlay).click(function(){
        $(sidebar).removeClass('visible');
        $(overlay).removeClass('visible');
    });
});

function toggleNav(nav, button) {
    $(nav).toggleClass('visible');
    $(button).toggleClass('active');
}

function hideNav(nav, button) {
    $(nav).removeClass('visible');
    $(button).removeClass('active');
}

function selectAll() {
    var source = $(this);
    var name = source.data('name');
    var checkboxes = $('input[type="checkbox"][name="' + name + '"]');
    $(checkboxes).each(function(){
        this.checked = source.prop('checked');
        $(this).change();
    });
}

$('document').ready(function(){

    // Stripe Checkout
    $('form.stripe-checkout').checkout();

    // Crowdfund
    $('.crowdfund__widget').crowdfund();

    // Currency Field
    $('input.currency-field').each(function(){
        $(this).currencyField();
    });

    // Date Picker
    $('.datepicker').datepicker({
        changeMonth: true,
        changeYear: true,
        minDate: new Date(1776, 6, 4),
        maxDate: '+1y',
        yearRange: '1776:+1'
    });

    $('.news__main img').loupe({
        height: 200,
        width: 200
    });

    $('.select-all').click(selectAll);

    $('#show-sections').click(function(){
        var button = this;
        var sections = '#global-sections';
        toggleNav(sections, button);
    });

    $('#show-search').click(function(){
        var searchButton = this;
        var search = '#global-search';
        var closeSearch = '#hide-search';
        var searchInput = $(search).children('input[type="search"]');
        toggleNav(search, searchButton);
        $(closeSearch).click(function(){
            hideNav(search, searchButton);
        });
        if ($(search).hasClass('visible')) {
            searchInput.focus();
        } else {
            searchInput.blur();
        }
    });

    $('#quick-log-in').click(function(e){
        e.preventDefault();
        var quickLogin = $('#quick-log-in-form');
        quickLogin.addClass('visible');
        quickLogin.find('input[type=text]')[0].focus();
        quickLogin.find('.cancel').click(function(){
            quickLogin.removeClass('visible');
        });
    });

});
