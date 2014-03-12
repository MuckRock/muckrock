django = {'jQuery': $};

 // Wizard location page to enable/disable selects
 $(document).ready(function(){
		 $("input[name='FOIAWizardWhereForm-local-autocomplete']").attr("disabled", "disabled");
		 $("input[name='FOIAWizardWhereForm-state-autocomplete']").attr("disabled", "disabled");
		 $("input[name='FOIAWizardWhereForm-level']").change(function(){
				 if ($("input[name='FOIAWizardWhereForm-level']:checked").val() == 'local') {
					 $("input[name='FOIAWizardWhereForm-local-autocomplete']").removeAttr("disabled");
					 $("input[name='FOIAWizardWhereForm-state-autocomplete']").attr("disabled", "disabled");
				 }
				 else if ($("input[name='FOIAWizardWhereForm-level']:checked").val() == 'state') {
					 $("input[name='FOIAWizardWhereForm-state-autocomplete']").removeAttr("disabled");
					 $("input[name='FOIAWizardWhereForm-local-autocomplete']").attr("disabled", "disabled");
				 }
				 else if ($("input[name='FOIAWizardWhereForm-level']:checked").val() == 'federal') {
					 $("input[name='FOIAWizardWhereForm-state-autocomplete']").attr("disabled", "disabled");
					 $("input[name='FOIAWizardWhereForm-local-autocomplete']").attr("disabled", "disabled");
				 }
				 else if ($("input[name='FOIAWizardWhereForm-level']:checked").val() == 'multi') {
					 $("input[name='FOIAWizardWhereForm-state-autocomplete']").attr("disabled", "disabled");
					 $("input[name='FOIAWizardWhereForm-local-autocomplete']").attr("disabled", "disabled");
				 }
				 $(this).blur();
			 });
 });

// Set up tabs and progress bars and tool tips
$(function() {
	$("#tabs").tabs();
	$("input:submit").button();
	$(".jqbutton").button();
	$("#progressbar").progressbar({ value: parseInt($("#progressbar").attr("title")) });
	$(".tipTip").tipTip({defaultPosition: "top", delay: 0});
});

// Set up the combobox for agency selection
(function( $ ) {
	$.widget( "ui.combobox", {
		_create: function() {
			var self = this,
				select = this.element.hide(),
				selected = select.children( ":selected" ),
				value = selected.val() ? selected.text() : "";
			var input = $( "<input>" )
				.insertAfter( select )
				.val( value )
				.autocomplete({
					delay: 0,
					minLength: 0,
					source: function( request, response ) {
						var matcher = new RegExp( $.ui.autocomplete.escapeRegex(request.term), "i" );
						response( select.children( "option" ).map(function() {
							var text = $( this ).text();
							if ( this.value && ( !request.term || matcher.test(text) ) )
								return {
									label: text.replace(
										new RegExp(
											"(?![^&;]+;)(?!<[^<>]*)(" +
											$.ui.autocomplete.escapeRegex(request.term) +
											")(?![^<>]*>)(?![^&;]+;)", "gi"
										), "<strong>$1</strong>" ),
									value: text,
									option: this
								};
						}) );
					},
					select: function( event, ui ) {
						ui.item.option.selected = true;
						self._trigger( "selected", event, {
							item: ui.item.option
						});
					},
					change: function( event, ui ) {
						if ( !ui.item ) {
							var matcher = new RegExp( "^" + $.ui.autocomplete.escapeRegex( $(this).val() ) + "$", "i" ),
								valid = false;
							select.children( "option" ).each(function() {
								if ( this.value.match( matcher ) ) {
									this.selected = valid = true;
									return false;
								}
							});
						}
					}
				})
				.attr("name", "combo-name")
				.addClass( "ui-widget ui-widget-content ui-corner-left" );

			input.data( "autocomplete" )._renderItem = function( ul, item ) {
				return $( "<li></li>" )
					.data( "item.autocomplete", item )
					.append( "<a>" + item.label + "</a>" )
					.appendTo( ul );
			};

			$( "<button type=\"button\">&nbsp;</button>" )
				.attr( "tabIndex", -1 )
				.attr( "title", "Show All Items" )
				.insertAfter( input )
				.button({
					icons: {
						primary: "ui-icon-triangle-1-s"
					},
					text: false
				})
				.removeClass( "ui-corner-all" )
				.addClass( "ui-corner-right ui-button-icon" )
				.click(function() {
					// close if already visible
					if ( input.autocomplete( "widget" ).is( ":visible" ) ) {
						input.autocomplete( "close" );
						return;
					}

					// pass empty string as value to search for, displaying all results
					input.autocomplete( "search", "" );
					input.focus();
				});
		}
	});
})( jQuery );

// Also for agency combo box
$(function() {
	$( ".combobox" ).combobox();
});

// embed dialog pop up
$(function() {
	$('#dialog').dialog({
		autoOpen: false,
		width: 560,
		height: 480,
		modal: true,
		zIndex: 100000
	});
	$('#opener').click(function() {
		$('#dialog').dialog('open');
		return false;
	});
});

// formsets
$(function() {
	$('.formset-container').formset();
});

function actionButton(name) {
	$('#action-form > input').attr('value', name);
	$('#action-buttons').hide();
	$('#action-form').show(400);
	$('html, body').animate({scrollTop: $(window).scrollTop() + 100});
	$('#action-form > textarea').focus();
	return false;
}

function cancelActionButton(name) {
	$('#action-form').hide(400);
	$('#action-buttons').show();
	return false;
}


