/**
 * 
 * @authors Blackstone (you@example.org)
 * @date    2019-11-13 13:35:32
 * @version $Id$
 */

/**
重新加载业务数据
**/
function loadbusinessdata(businessdata,stepid){

	//businessdata=JSON.parse(businessdata)
  	var businesstitle;
    data=businessdata.data

    $("#table-show").empty();
    $("#table-show").append('业务数据')
    $("#table-show").append("<br/><br/><span href='#' id='adddata' style='font-size:5px;margin-left:5px;'>新增</span>")
    $("#table-show").append("<span href='#' id='deldata' style=';font-size:5px;margin-left:20px;'>删除</span>")
    $("#table-show").append("<table id='business-table' class='layui-table' lay-filter='business-target'></table>")
    var tableIns= layui.table.render({
      // url:'/manager/querytesttable/'
      elem:'#business-table', 
      id:'business-data', 
      height: 400,
      cols:[[ //表头
      {type:'checkbox'}
      ,{field: 'id', title: 'ID',hide:true}
      ,{field: 'businessname', title: '测试点'}
      ,{field: 'itf_check', title: '接口校验'}
      ,{field: 'db_check', title: 'DB校验'} 
      ,{field: 'params', title: '参数信息'}
      ,{fixed: 'right',align:'center',title:'操作',width:100,toolbar:"#toolbar2"}

    ]],
   	  data:data,
      page:false,
      // limit:1,
      // count:3
    });

    //定义工具条事件
	 layui.table.on("tool(business-target)",function(e){
	  bid=e.data['id']
	  if(e.event=='add'){



	  }else if(e.event=='del'){


	  }else if(e.event=='edit'){
	  	success=function(d){
	  		console.log('d=>')
	  		console.log(d)
	  		if(typeof(d)==='string')
	  			d=JSON.parse(d)

	  		if(d.code!=0){
	  			layer.msg(d.msg);
	  			return;
	  		}

			$("[name='businessname']").val(d.data[0]['businessname'])
			$("[name='itf_check']").val(d.data[0]['itf_check'])
			$("[name='db_check']").val(d.data[0]['db_check'])
			$("[name='params']").val(d.data[0]['params'])

			//弹窗
			var o=layer.open({
	          type:1,
	          title:'编辑测试数据',
	          content:$('#addbusiness'),
	          btn:['提交','取消'],
	          yes:function(index,layero){

	          	layer.close(index)
	          	success=function(e){
	          		loadbusinessdata(e,stepid)
					// table.reload('business-data',{
					// 	page:{
					// 	curr:1
					// 	}

					// });

	          	}
	          	data={
	            'flag':'2',
	            'stepid':stepid,
	            'id':bid,
	            'businessname':$("[name='businessname']").val(),
	            'itf_check':$("[name='itf_check']").val(),
	            'db_check':$("[name='db_check']").val(),
	            'params':$("[name='params']").val(),

	          	}

	          	_post('/manager/querybusinessdata/',data,success)
	          }


			});
			layer.full(o);

	  	};

	  	_post('/manager/queryonebusinessdata/',{'vid':bid,'stepid':stepid},success)
	  }
	});


	//定义新列按钮
	$('#adddata').click(function(event){

	    $("#addbusiness")[0].reset()
	    layui.form.render()

		var o=layer.open({
          type:1,
          title:'新建测试数据',
          content:$('#addbusiness'),
          btn:['提交','取消'],
          yes:function(index,layero){

          	layer.close(index)

			success=function(e){

				loadbusinessdata(e,stepid)
				// table.reload('business-data',{
				// 	page:{
				// 	curr:1
				// 	}

				// });
			}

	          data={
	            'flag':'1',
	            'stepid':stepid,
	            'businessname':$("[name='businessname']").val(),
	            'itf_check':$("[name='itf_check']").val(),
	            'db_check':$("[name='db_check']").val(),
	            'params':$("[name='params']").val(),

	          }
	          _post("/manager/querybusinessdata/",data,success);

          }
		});

		layer.full(o);
	});
	$('#deldata').click(function(event){
	    var checkStatus = layui.table.checkStatus("business-data");
	    console.log(checkStatus)
	    data = checkStatus.data;
	    // alert(data)
	    ids=[]

      	for(var index=0;index<data.length;index++){
	        ids.splice(0,0,data[index]['id'])

	      }

	    layer.confirm('确认删除么?',function(index){

	      success=function(e){
	      	loadbusinessdata(e,stepid)
	      	layer.close(index)

	      }
          data={
            'flag':'3',
            'vids':ids.join(),
            'stepid':stepid,

          }
          _post("/manager/querybusinessdata/",data,success);
	   
	    });


	});

 
}

