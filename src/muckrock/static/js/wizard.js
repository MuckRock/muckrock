
 $(document).ready(function(){
		 $("select[name='FOIAWizardWhereForm-local']").attr("disabled", "disabled");
		 $("select[name='FOIAWizardWhereForm-state']").attr("disabled", "disabled");
		 $("input[name='FOIAWizardWhereForm-level']").change(function(){
				 if ($("input[name='FOIAWizardWhereForm-level']:checked").val() == 'local') {
					 $("select[name='FOIAWizardWhereForm-local']").removeAttr("disabled");
					 $("select[name!='FOIAWizardWhereForm-local']").attr("disabled", "disabled");
				 }
				 else if ($("input[name='FOIAWizardWhereForm-level']:checked").val() == 'state') {
					 $("select[name='FOIAWizardWhereForm-state']").removeAttr("disabled");
					 $("select[name!='FOIAWizardWhereForm-state']").attr("disabled", "disabled");
				 }
				 else if ($("input[name='FOIAWizardWhereForm-level']:checked").val() == 'federal') {
					 $("select").attr("disabled", "disabled");
				 }
				 $(this).blur();
			 });
 });

$(function() {
	$("#tabs").tabs();
	$("input:submit").button();
	$("#progressbar").progressbar({ value: parseInt($("#progressbar").attr("title")) });
});

$(function() {
	$('#dialog').dialog({
		autoOpen: false,
		width: 320,
		zIndex: 100000
	});
	
	$('#opener').click(function() {
		$('#dialog').dialog('open');
		return false;
	});
});
