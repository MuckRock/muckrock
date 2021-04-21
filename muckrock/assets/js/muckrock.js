/* muckrock.js
 **
 ** This file is the "keystone" of MuckRock's Javascript assets.
 ** It is responsible for importing other JS modules.
 ** It is also responsbile for initializing many of the JQuery components.
 **
 ** Known issues:
 ** - Some JQuery components may be initialized in other templates, mostly due to
 **   those initializations requiring variables defined by the template context.
 ** - Some JQuery logic is defined here, and those definitions should be moved to
 **   standalone files and then imported back into here.
 */

import 'jquery-ui/datepicker';
import 'jquery-ui/widget';
import 'jquery-ui/sortable';
import 'formBuilder';
import 'tooltipster';
import '../vendor/formset';
import '../vendor/loupe';
import '../vendor/quicksearch';
import '../vendor/stacktable';
import qq from '../vendor/fine-uploader';
window.qq = qq;

import './account';
import './checkout';
import './communication';
import './crowdfund';
import './crowdsource';
import './currencyField';
import './dropdown';
import './editor';
import './exemptionBrowser/app';
import './foiaRequest';
import './foiaCreate';
import './jurisdiction';
import './list';
import modal from './modal';
import './nav';
import './selectAll';
import './stripe';
import './tabs';
import './task';

import 'jquery.tabulator';

/* Bind plugins and event handlers to frontend elements. */

$('document').ready(function(){

  if ('ontouchstart' in window) {
    $('body').addClass('touch');
  }

  // Stripe Checkout
  $('form.stripe-checkout').checkout();

  // Crowdfund
  $('.crowdfund__widget').crowdfund();

  // Currency Field
  $('input.currency-field').each(function(){
    $(this).currencyField();
  });

  // Modal
  $('.modal-trigger').click(function(){
    modal(this.hash);
    return false;
  });

  // Select All
  $('.select-all').each(function(){
    $(this).selectAll();
  });

  // Date Picker
  $('.datepicker').datepicker({
    changeMonth: true,
    changeYear: true,
    minDate: new Date(2010, 0, 1),
    maxDate: '+1y',
    yearRange: '2010:+1'
  });
  $('.datepicker-future').datepicker({
    changeMonth: true,
    changeYear: true,
    minDate: 0,
    maxDate: '+1y'
  });
  $('.datepicker-simple').datepicker({
    changeMonth: true,
    changeYear: true
  });

  // Loupe
  /*
   * Temprarily disabled for now, see issue #1427
  $('.news__article__main img').loupe({
    height: 200,
    width: 200
  });
  */

  // Quicksearch
  $('#comms-filter').quicksearch('#comms .communications-list .communication');
  $('#notes-filter').quicksearch('#notes .note');
  $('#tags .search').quicksearch('.tag-table tr');

  // Flag form
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

  // Messages
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

  // Formset
  $('.formset-container').formset();

  // TODO: Figure out what this does????????
  $.expr[":"].icontains = $.expr.createPseudo(function(arg) {
    return function( elem ) {
      return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
  });

  // COLLAPSABLE
  $('.collapsable header').click(function(){
    $(this).parent().toggleClass('collapsed');
  });
  $('.collapsable header').find('.nocollapse').click(function(event){
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

  $('#filter-form button.get').click(function() {
    $('#filter-form [name=csrfmiddlewaretoken]').removeAttr('name');
  });

});
