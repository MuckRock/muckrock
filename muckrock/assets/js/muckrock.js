import '../vendor/jquery.formset'
import '../vendor/jquery.loupe'
import '../vendor/jquery.multiselect'
import '../vendor/jquery.quicksearch'
import '../vendor/jquery.ui.datepicker'

import './muckrock.checkout'
import './muckrock.currencyfield'
import './muckrock.crowdfund'
import './communication'
import './foiaRequest'
import './list'
import './notification'
import './tabs'
import './task'

function modal(nextSelector) {
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

// MODALS
$('.modal-button').click(function(){ modal($(this).next()); });
$('.embed.hidden-modal').each(function() {
    var textarea = $(this).children('textarea');
    var doc_id = textarea.data('docId');
    var embed = '<div class="viewer" id="viewer-' + doc_id + '"></div> <script src="https://s3.amazonaws.com/s3.documentcloud.org/viewer/loader.js"><\/script> <script>DV.load("https://www.documentcloud.org/documents/' + doc_id + '.js", {width: 600, height: 600, sidebar: false, container: "#viewer-' + doc_id + '"});<\/script>';
    textarea.val(embed);
});

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

// SELECT ALL
$('#toggle-all').click(function(){
    var toggleAll = this;
    $(':checkbox').not('#toggle-all').each(function(){
        $(this).click(function(){
            toggleAll.checked = false;
        });
        if (!$(this).data('ignore-toggle-all')) {
            this.checked = toggleAll.checked;
        }
    });
});

// Manager Component
// A manager presents a state and a form that can modify that state.
$('.manager .edit').click(function(){
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

// formsets
$(function() {
	$('.formset-container').formset();
});

function urlParam(sParam)
{
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++)
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam)
        {
            return sParameterName[1];
        }
    }
}

$.expr[":"].icontains = $.expr.createPseudo(function(arg) {
    return function( elem ) {
        return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
});

$('#sidebar-button').click(function(e){
    var overlay = '#modal-overlay';
    var sidebar = '#website-sidebar';
    $(sidebar).addClass('visible');
    $(overlay).addClass('visible');
    $(overlay).click(function(e){
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

function selectAll(source, name) {
    var checkboxes = $('input[type="checkbox"][name="' + name + '"]');
    $(checkboxes).each(function(){
        this.checked = source.checked;
        $(this).change();
    });
}

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
        searchInput.blur()
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

$('document').ready(function(){

    // Stripe Checkout
    $('form.stripe-checkout').checkout();

    // Crowdfund form submission
    $('form.crowdfund-form').crowdfund();

    // Currency Field
    $('input.currency-field').currencyField();

    // Date Picker
    $('.datepicker').datepicker({
        changeMonth: true,
        changeYear: true,
        minDate: new Date(1776, 6, 4),
        maxDate: '+1y',
        yearRange: '1776:+1'
    });

    $('.news--main img').loupe({
        height: 200,
        width: 200
    });

});
