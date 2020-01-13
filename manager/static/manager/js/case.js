/**
 * 
 * @authors Blackstone (you@example.org)
 * @date    2019-09-20 08:43:12
 * @version $Id$
 */


/**
工具条模板
*/
var selected_tool_tmp="<p title='#value#' id='#id#' class='layui-inline'><input id='#checkboxid#' type='checkbox' style='margin-right:5px;'>#order#-#value#<span class='icon-tool'>"+
  "<a class='layui-icon layui-icon-upload-circle icon-tool-item'></a>"+
  "<a class='layui-icon layui-icon-download-circle icon-tool-item'></a>"+
  "<a class='layui-icon layui-icon-refresh icon-tool-item'></a></span></p>";
/**
加载预选&已选列表

**/

function bindselect(id){
	$("#can-select .layui-card-body").empty();
	success=function(data){
		console.log('===预选数据==')
		console.log(data);
		//alert(data)
		if(data.data&&data.data.length>0){
			for(var index=0;index<data.data.length;index++){
				if(data.data[index]['tagname']==undefined)
					data.data[index]['tagname']='*'

				var tmp="<p id='"+data.data[index]['id']+"' order='"+data.data[index]['order']+"'><input type='checkbox' style='margin-right:5px;' id='"+data.data[index]['id']+"'>"+data.data[index]['stepname']+'_'+data.data[index]['businessname']+"</p>";
			
				$("#can-select .layui-card-body").append(tmp);
			}

			//绑定双击addcase
			_addcase(id)

			_addsome(id)

			_addall(id)
		}

	};
	_post('/manager/querybusinessdatalist/',{},success);
}

function bindselected(main_id){
	$("#step-selected").empty();

	success=function(data){
		console.log(data);
		data=JSON.parse(data);
		if(data.code!=0)
		{
			layer.alert(data.msg,{icon:2})
		}

		if(data.data&&data.data.length>0){
			for(var index=0;index<data.data.length;index++){

				var value=data.data[index]['description']
				var order=data.data[index]["order"]
				var id=data.data[index]["id"]
				var tmp=selected_tool_tmp.replace("#id#",id).replace("#value#",value).replace("#order#",order).replace("#value#",_getsimple(value)).replace("#checkboxid#",id);
				$("#is-selected .layui-card-body").append(tmp);

			}

			rebindtoolevent(main_id);
			_delsome(main_id)
			_delall(main_id)
			_swap(main_id)
		
		}


	};
	_post('/manager/queryafteradd/',{"main_id":main_id,"follow_ids":-1,"kind":"step"},success);
}




/**
筛选
**/

function bindsearch(){
	$('#searchvalue').on('input propertychange', function() {//监听文本框
		v=$('#searchvalue').val();
		$("#can-select p").each(function(){
			if(v!=''){
				var flag=$(this).text().indexOf(v);
				//console.log(flag)
				if(flag==-1)
					$(this).css('display','none');
				else
					$(this).css('display','');

			}else 
				$(this).css('display','');


		
		});
	   });


	$('#searchvalue1').on('input propertychange', function() {//监听文本框
		v=$('#searchvalue1').val();
		$("#is-selected p").each(function(){
			if(v!=''){
				var flag=$(this).text().indexOf(v);
				//console.log(flag)
				if(flag==-1)
					$(this).css('display','none');
				else
					$(this).css('display','');

			}else 
				$(this).css('display','');


		
		});
	   });
}
/**
添加case
**/

function _addcase(parentid){
	$('#can-select p').each(function(e){
		$(this).dblclick(function(){
			//建立父子关系
			var	main_id=parentid;
			var follow_id=$(this).attr("id");
			console.log("main_id="+main_id+" follow_id="+follow_id)
			//获得子节点执行序号
			$("#step-selected").empty();
			success=function(data){
	
				data=JSON.parse(data)
				for(var index=0;index<data.data.length;index++){
					var id=data.data[index]["id"]
					var order=data.data[index]['order']
					var description=data.data[index]["description"]
					var tmp=selected_tool_tmp.replace("#value#",description).replace('#id#',id).replace("#order#",order).replace("#value#",_getsimple(description)).replace("#checkboxid#",id);
		        	$("#step-selected").append(tmp);
				}


				//重新绑定
				rebindtoolevent(main_id);

			}
			var param={"main_id":main_id,"follow_ids":follow_id,"kind":"step"}
			console.log(param)
			_post('/manager/queryafteradd/',param,success)


		});
	});


}


/**取消case

**/

function rebindtoolevent(main_id){
	console.log('rebindtoolevent')
	$("#is-selected p").each(function(){

		var follow_id=$(this).attr("id")
		$(this).dblclick(function(){
			console.log('dblclick')
			// var follow_id=$(this).attr("id")
			success=function(data){
				data=JSON.parse(data)
				$("#step-selected").empty();
				for(var index=0;index<data.data.length;index++){
					var id=data.data[index]["id"]
					var order=data.data[index]['order']
					var description=data.data[index]["description"]
					var tmp=selected_tool_tmp.replace("#value#",description).replace('#id#',id).replace("#order#",order).replace("#value#",_getsimple(description)).replace("#checkboxid#",id);
		        	$("#step-selected").append(tmp);
				}
				rebindtoolevent(main_id)
			}
			var param={"main_id":main_id,"follow_ids":follow_id,"kind":"step"}
			_post("/manager/queryafterdel/",param,success)
			
		});

		// console.log($(this).children('.layui-icon-upload-circle'))

		$(this).find("a:eq(0)").click(function(){
			console.log("up")
			// var follow_id=$(this).attr("id")
			console.log("follow_id=>"+follow_id)
			success=function(data){
				data=JSON.parse(data)
				console.log(data)
				$("#step-selected").empty();
				for(var index=0;index<data.data.length;index++){
					var id=data.data[index]["id"]
					var order=data.data[index]['order']
					var description=data.data[index]["description"]
					var tmp=selected_tool_tmp.replace("#value#",description).replace('#id#',id).replace("#order#",order).replace("#value#",_getsimple(description)).replace("#checkboxid#",id);
		        	$("#step-selected").append(tmp);
		        }
		        rebindtoolevent(main_id)

			}
			_post("/manager/changepos/",{"main_id":main_id,"follow_id":follow_id,"move":-1,"kind":"step"},success)

		});

		$(this).find("a:eq(1)").click(function(){
			console.log("down")
			// var follow_id=$(this).attr("id")
			success=function(data){
				data=JSON.parse(data)
				$("#step-selected").empty();
				for(var index=0;index<data.data.length;index++){
					var id=data.data[index]["id"]
					var order=data.data[index]['order']
					var description=data.data[index]["description"]
					var tmp=selected_tool_tmp.replace("#value#",description).replace('#id#',id).replace("#order#",order).replace("#value#",_getsimple(description)).replace("#checkboxid#",id);
		        	$("#step-selected").append(tmp);
		        }
		        rebindtoolevent(main_id)

			}
			_post("/manager/changepos/",{"main_id":main_id,"follow_id":follow_id,"move":1,"kind":'step'},success)
			
		});

		$(this).find("a:eq(2)").click(function(){
			console.log("group")
			success=function(data){
				data=JSON.parse(data)
				$("#step-selected").empty();
				for(var index=0;index<data.data.length;index++){
					var id=data.data[index]["id"]
					var order=data.data[index]['order']
					var description=data.data[index]["description"]
					var tmp=selected_tool_tmp.replace("#value#",description).replace('#id#',id).replace("#order#",order).replace("#value#",_getsimple(description)).replace("#checkboxid#",id);
		        	$("#step-selected").append(tmp);
		        }
		        rebindtoolevent(main_id)

			}
			_post("/manager/aftergroup/",{"main_id":main_id,"follow_id":follow_id,"kind":'step'},success)
			
			
		});

	});


}




function _addsome(parentid,btn_pattern='#addsome',range_pattern='#can-select input:checkbox:checked'){
	$(btn_pattern).click(function(){
	  //alert(1)

	cs=$(range_pattern)
	console.log('----------------批量添加操作--------------------------')
	console.log(cs.length)

	follow_ids=[]
	cs.each(function(index,e){
		follow_ids.push(e.attributes['id'].nodeValue)

	});

	$("#step-selected").empty();

	success=function(data){

		data=JSON.parse(data)
		if(data.code!=0){
			//alert(data.msg)
			layer.alert(data.msg,{icon:2})
			return
		}
		
		console.log(data)

		for(var index=0;index<data.data.length;index++){
			var id=data.data[index]["id"]
			var order=data.data[index]['order']
			var description=data.data[index]["description"]
			var tmp=selected_tool_tmp.replace("#value#",description).replace('#id#',id).replace("#order#",order).replace("#value#",_getsimple(description)).replace("#checkboxid#",id);
	    	$("#step-selected").append(tmp);
		}
		//重新绑定
		rebindtoolevent(parentid);
	}

	var param={"main_id":parentid,"follow_ids":follow_ids.join(),"kind":"step"}
	_post('/manager/queryafteradd/',param,success)

	});
}

function _addall(parentid){
	_addsome(parentid,'#addall','#can-select input:checkbox')

}
function _delsome(parentid,btn_pattern='#delsome',range_pattern='#step-selected input:checkbox:checked'){

	var follow_ids=[]

	$(btn_pattern).click(function(){
		//alert(btn_pattern)
		cs=$(range_pattern)
		main_id=parentid

		cs.each(function(index,e){
			follow_ids.push(e.attributes["id"].nodeValue)

		})

		//layer.alert(cs.length,{icon:1})

		success=function(data){
			data=JSON.parse(data)
			$("#step-selected").empty();
			for(var index=0;index<data.data.length;index++){
				var id=data.data[index]["id"]
				var order=data.data[index]['order']
				var description=data.data[index]["description"]
				var tmp=selected_tool_tmp.replace("#value#",description).replace('#id#',id).replace("#order#",order).replace("#value#",_getsimple(description)).replace("#checkboxid#",id);
	        	$("#step-selected").append(tmp);
			}
			rebindtoolevent(main_id)
		}
		var param={"main_id":main_id,"follow_ids":follow_ids.join(),"kind":"step"}
		_post("/manager/queryafterdel/",param,success)




	});



}
function _delall(parentid){
	range_pattern='#step-selected input:checkbox'
	_delsome(parentid,'#delall',range_pattern)

}
function _swap(parentid){
	$('#swap').click(function(){
		//alert('swap')
		cs=$('#step-selected input:checkbox:checked')
		if(cs.length==2){

			uids=[]

			
			cs.each(function(index,e){
				uids[index]=e.attributes["id"].nodeValue
			})

			success=function(e){

				//console.log(e)
				var data;
				if (typeof(e)=='string')
					data=JSON.parse(e)
				else
					data=e

				//alert(data.code)

				//console.log('交换后的信息：'+data+','+typeof(data))
				if(data.code==0){
					$("#step-selected").empty()

					for(var index=0;index<data.data.length;index++){
						var id=data.data[index]["id"]
						var order=data.data[index]['order']
						var description=data.data[index]["description"]
						var tmp=selected_tool_tmp.replace("#value#",description).replace('#id#',id).replace("#order#",order).replace("#value#",_getsimple(description)).replace("#checkboxid#",id);
				    	$("#step-selected").append(tmp);
					}
					//重新绑定
					rebindtoolevent(parentid);

					layer.alert(data.msg,{icon:1,time:1000})
				}else{
					layer.alert(data.msg,{icon:2})
				}


			}

			//alert(uids)
			_post('/manager/changepos/',{'move_kind':'swap','main_id':parentid,'aid':uids[0],'bid':uids[1],'kind':'step'},success)

		}

	})


}

function _getsimple(oldstr){


	max=12
	if(oldstr.length>max)
		return oldstr.substring(0,max-1)+'...'
	else
		return oldstr
}