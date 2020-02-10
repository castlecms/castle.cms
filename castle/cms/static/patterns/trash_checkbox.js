define([
    'jquery',
    'pat-base'
    
], function($, Base) {
    "use strict";

    var Trash_Checkboxes = Base.extend({
	name: 'trash_checkbox',
	trigger: '.pat-trash_checkbox',
	defaults: {
	},
	parser: 'mockup',
	
	init: function(){
	    $("#restore_all").click(function(){
		
		
		var elements = document.getElementsByClassName("restore-checkbox");
		var restore_item_uid = [];
		for(var element = 0; element < elements.length; element++)
		{
		    if(elements[element][1].checked == true)
		     {
			restore_item_uid.push(elements[element][0].value);
		    };
		};
		var form = document.getElementById("restore_all");
		var input = document.createElement('input');
		input.setAttribute('name', 'restore_item_uid');
		input.setAttribute('value', restore_item_uid);
		input.setAttribute('type', 'hidden');

		form.appendChild(input);
		form.submit();
	    });
	}
    });
    
    return Trash_Checkboxes;
});


				      
