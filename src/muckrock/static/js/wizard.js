
 $(document).ready(function(){
		 $("select").attr("disabled", "disabled");
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
	});
