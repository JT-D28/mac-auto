/**
 * 
 * @authors Blackstone (you@example.org)
 * @date    2019-09-02 10:01:35
 * @version $Id$
 */

function bind_interface_click(){

	$("#interface-list").click(function(e){

		nodes=$(this).children()
		nodes.unbind();

		nodes.each(function(){
			$(this).click(function(){
				console.log('click.')
			});
		});



	});
};





