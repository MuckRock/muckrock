
 $(document).ready(function(){
		 $("input[name='0-level']").change(function(){
				 if ($("input[name='0-level']:checked").val() == 'state') {
					 $("select[name='0-state']").removeAttr("disabled");
					 $("select[name!='0-state']").attr("disabled", "disabled");
				 }
				 else if ($("input[name='0-level']:checked").val() == 'local') {
					 $("select[name='0-local']").removeAttr("disabled");
					 $("select[name!='0-local']").attr("disabled", "disabled");
				 }
				 $(this).blur();
			 });
 });
