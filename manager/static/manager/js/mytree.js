var tree={
	// _newCount:1,
	className:'dark',
	_getsetting:function(){
		var setting =
		{
			view: {
		        addHoverDom:this._addHoverDom, //当鼠标移动到节点上时，显示用户自定义控件
		        removeHoverDom:this._removeHoverDom, //离开节点时的操作
		        selectedMulti:false,
		        showLine:false,
		        nameIsHTML: true,
		        addDiyDom:this._addDiyDom,
		        fontCss: this._setFontCss,
		    },

			edit:{
			   	enable:true,
		        // 关闭删除
		        showRemoveBtn: false,
		        // 关闭修改名称
		        showRenameBtn: false,
	                drag: {
	                    isCopy: true,
	                    isMove: true,
	                },

		   	},

			data:{
			    simpleData:{
			      enable:true //支持json格式
				}
			},
			callback: {
				onClick:this._onClick,
		    	beforeExpand:this._onBeforeExpand,
	            beforeDrag: this._beforeDrag,
	            beforeDrop: this._beforeDrop,
	            onDrop:this._onDrop,
	            onExpand:this._onExpand,
	            onCollapse:this._onCollapse,
				// beforeEditName: this._beforeEditName,
		  //   	beforeRemove: this._beforeRemove,
				// beforeRename: this._beforeRename,
				// onRemove: this._onRemove,
				// onRename: this._onRename,
      		}
  		}

		return setting

	},

	init:function(searchvalue=''){
		// return

		//alert('tree init..')
		var t=this
		success=function(data){
			data=JSON.parse(data);
			// console.log('用例树查询=>')
			// console.log(data)

			if(data.code!=0){
				layer.alert(data.msg,{icon:2})
				return
			}

			setting=t._getsetting()
			// console.log('基本配置=>')
			// console.log(setting)

			$.fn.zTree.init($("#case-manager"),setting,data.data);

		}

		param={
			'searchvalue':searchvalue
			}


		_post('/manager/querytreelist/',param,success)

	},

	_showLog:function(msg){
		console.log(msg)

	},
	_getTime:function(a=1){
		var now= new Date(),
		h=now.getHours(),
		m=now.getMinutes(),
		s=now.getSeconds(),
		ms=now.getMilliseconds();
		return (h+":"+m+":"+s+ " " +ms);
	},

	_setFontCss:function(treeId, treeNode){

		text=$('#search').val()
		if(text)
			return treeNode.name.indexOf(text)>-1?{'background-color':"#FFFF00"}:{};
		else
			return{}

	},
	_addDiyDom:function(treeId, treeNode) {
    var spaceWidth = 5;
    var switchObj = $("#" + treeNode.tId + "_switch"),
    icoObj = $("#" + treeNode.tId + "_ico");
    switchObj.remove();
    icoObj.parent().before(switchObj);
    var spantxt = $("#" + treeNode.tId + "_span").html();
    if (treeNode.type=='step' & spantxt.length> 15 ) {
        spantxt = spantxt.substring(0, 15) + "...";
        $("#" + treeNode.tId + "_span").html(spantxt);
    }else if(spantxt.length> 12){
    	spantxt = spantxt.substring(0, 12) + "...";
        $("#" + treeNode.tId + "_span").html(spantxt);
	}


	},
	_addHoverDom:function(treeId, treeNode){
		//console.log(treeNode)
		_m1={
			'root':['add'],
			'product':['add','edit','del','mimport'],
			'plan':['add','edit','del','run','mexport','logs'],
			'case':['add','edit','del'],
			'step':['add','edit','del'],
			'business':['edit','del']
		}
		_opinfo={

			'up':"<span class='fa fa-arrow-circle-up' id='up_#tid#' title='上移'></span>",
			'down':"<span class='fa fa-arrow-circle-down' id='down_#tid#' title='下移'></span>",
			'edit':"<span class='fa fa-pencil-square-o' id='edit_#tid#' title='编辑' onfocus='this.blur();'></span>",
			'mimport':"<span class='fa fa-hand-o-left' id='mimport_#tid#' title='导入'></span>",
			'mexport':"<span class='fa fa-hand-o-right' id='mexport_#tid#' title='导出'></span>",
			'run':"<span class='fa fa-play-circle' id='run_#tid#' title='运行'></span>",
			'add':"<span class='fa fa-plus-circle' id='add_#tid#' title='增加' onfocus='this.blur();'></span>",
			'del':"<span class='fa fa-trash' id='del_#tid#' title='删除' onfocus='this.blur();'></span>",
			'logs':"<span class='fa fa-bug' id='logs_#tid#' title='调试日志' onfocus='this.blur();'></span>",
		}

		var type=treeNode.type
		// alert(type)
		var oplist=_m1[type]
		// alert(oplist)
		if(oplist==undefined)
			return
		// console.log('len=>'+oplist.length)
		var tid=treeNode.tId
		var sObj = $("#" + treeNode.tId + "_span");
		// if (treeNode.editNameFlag || $("#add_"+treeNode.tId).length>0) return;

       	btnstr=''
       	for(var i=0;i<oplist.length;i++){
       		try{

       		if($("#"+oplist[i]+"_"+tid).length>0){
				continue;
       		}
       		btnstr=btnstr+_opinfo[oplist[i]].replace('#tid#',tid)
       		}catch(e){
       			continue;

       		}

       	}

       	//console.log('tid=>'+treeNode.tId)

		if(treeNode.editNameFlag)return
		if($("#add_"+treeNode.tId).length>0)return
		if($("#edit_"+treeNode.tId).length>0)return
		if($("#del_"+treeNode.tId).length>0)return
		if($("#run_"+treeNode.tId).length>0)return
		if($("#mimport_"+treeNode.tId).length>0)return
		if($("#mexport_"+treeNode.tId).length>0)return
		if($("#logs_"+treeNode.tId).length>0)return

		sObj.after(btnstr);

		//ADD
		var add_btn = $("#add_"+treeNode.tId);
		//console.log('len=>'+add_btn.length)
		if (add_btn) add_btn.bind("click", function(){
			console.log('add')
			type=treeNode.type
			page=''
			if(type=='root'){
				page='product'
			}
			else if(type=='product'){
				page='plan'
			}
			else if(type=='plan'){
				page='case'
			}else if(type=='case'){
				page='step'
			}else if(type=='step'){
				page='business'
			}
			// console.log('jumppage=>'+page)
			console.log(treeNode.id)
			_load_tree_content('/manager/treecontrol/?action=loadpage&op=add&page='+page+'&pid='+treeNode.id+'&ptid='+treeNode.tid)
			return false

		});
		// //EDIT
		var edit_btn = $("#edit_"+treeNode.tId);
		if (edit_btn)edit_btn.bind("click", function(){
			console.log('edit')
			type=treeNode.type
			_load_tree_content('/manager/treecontrol/?action=loadpage&uid='+treeNode.id+'&page='+type+'&utid='+treeNode.tid)
			return false

		});

		// //DEL
		var del_btn=$("#del_"+treeNode.tId)
		if (del_btn)del_btn.bind("click", function(){
			console.log('del node=>',treeNode.tId)

		    layer.confirm('确认删除['+treeNode.name+']么?',function(index){
		    	success=function(e){
		    		if(e.code==0){

						var treeObj = $.fn.zTree.getZTreeObj(treeId);
						var node = treeObj.getNodeByParam('id',treeNode.id);

				 		treeObj.removeNode(node)

		    			layer.alert(e.msg,{icon:1,time:2000})
		    		}
		    		else{

		    			layer.open(
					      {
					        title:'信息',
					        icon:2,
					        type:0,
					        // area:["350px","350px"],
					        content:e.msg,
					        btn:['强制删除','取消'],
					        yes:function(){
					        	//layer.msg('强制删除.')
					        	success=function(e){
									var treeObj = $.fn.zTree.getZTreeObj(treeId);
									var node = treeObj.getNodeByParam('id',treeNode.id);

							 		treeObj.removeNode(node)

					    			layer.alert(e.msg,{icon:1,time:2000})

					        	}

					        	_post('/manager/treecontrol/',{'action':'del_node_force','ids':treeNode.id},success)
					        }
					    });
		    		}

		    	};
		    	_post('/manager/treecontrol/',{
		    		'action':'del'+treeNode.type,
		    		'ids':treeNode.id
		    	},success)

		    })

			return false;
		});

		//RUN

		run_btn=$("#run_"+treeNode.tId)
		if (run_btn)run_btn.bind("click", function(){

			_post('/manager/treecontrol/',{
				'action':'run',
				'ids':treeNode.id
			},function(data){
				if(data.code==0){
					layer.alert('你已提交任务 ID='+data.msg,{icon:1,time:2000})
				}else{
					layer.alert('提交异常..')
				}



			})

			return false;
		});

		//EXPORT
		export_btn=$("#mexport_"+treeNode.tId)
		if (export_btn)export_btn.bind("click", function(e){

		if (e.stopPropagation)
			e.stopPropagation()

	    var url = http_base+"/manager/treecontrol/?planid="+treeNode.id+'&version=2&action=export';
	    var xhr = new XMLHttpRequest();
	    xhr.open('GET', url, true);//get请求，请求地址，是否异步
	    xhr.responseType = "blob";    // 返回类型blob
	    xhr.onload = function () {// 请求完成处理函数
	      if (this.status === 200) {
	        var blob = this.response;// 获取返回值
	        var a = document.createElement('a');
	        a.download = 'plan.ME2';
	        a.href=window.URL.createObjectURL(blob);
	        a.click();
	        }
	    };
	    // 发送ajax请求
	    xhr.send();
		return false;
		});



		// //IMPORT
		var import_btn=$("#mimport_"+treeNode.tId)
		if (import_btn) import_btn.bind("click", function(){
			page='import'
			_load_tree_content('/manager/treecontrol/?action=loadpage&op=import&page='+page+'&pid='+treeNode.id+'&ptid='+treeNode.tid)


			return false;
		});


		layui.use(['tree', 'table'], function () {
			var tree = layui.tree;
			var table = layui.table;
			logs_btn = $("#logs_" + treeNode.tId)

			if (logs_btn) logs_btn.bind("click", function () {
				_post('/homepage/plandebug/', {
					'id': treeNode.id.substr(5),
					'type': 'info'
				}, function (data) {
					layer.open({
						title: '任务名【' + data.data[0]['planname'] + '】在【' + data.data[0]['time'].substr(5, 11) + '】执行不通过情况',
						type: 1,
						area: ['90%', '90%'],
						content: $('#test'),
						shade: [0],
						anim: 2,
						shadeClose: true,
						success: function () {
							querydebug(treeNode.id.substr(5), 'plan', data.data[0]['taskid'])
						},
						end: function () {
							table.reload('demo', {data: [],text: {none: '测试全部通过了！'}});
							tree.reload('demo1', {data: [], text: {none: ''}});
							tree.reload('demo2', {data: [], text: {none: ''}});
							tree.reload('demo3', {data: [], text: {none: ''}});
							$("#log_text").html('');
						}
					});
				});
				return false;
			});

			function querydebug(id, type, taskid) {
				_post('/homepage/plandebug/', {
					'id': id,
					'type': type,
					'taskid': taskid
				}, function (data) {
					plandebug(data)
				})

			}

			function plandebug(data) {
				if (data.type == "case") {
					tree.render({
						elem: '#demo1', id: 'demo1', data: data.data, accordion: true, showLine: true,
						text: {none: '本次调试全部通过'},
						click: function (obj) {
							querydebug(obj.data.id, 'case', data.taskid)
							// tree.reload('demo3', {data: [], text: {none: ''}});
						}
					})
				} else if (data.type == "step") {
					tree.render({
						elem: '#demo2', id: 'demo2', data: data.data, accordion: true, showLine: true,
						click: function (obj) {
							querydebug(obj.data.id, 'step', data.taskid)
						}
					})
				} else if (data.type == "bussiness") {
					tree.render({
							elem: '#demo3', id: 'demo3', data: data.data, accordion: true, showLine: true,
							click: function (obj) {
								table.render({
									elem: '#demo',
									id:'demo'
									, method: 'POST'
									, url: '/homepage/plandebug/' //数据接口
									, where: {
										'id': obj.data.id,
										'type': 'bussiness',
										'taskid': data.taskid
									}
									, cols: [[ //表头
										{field: 'id', title: '项目', width: "20%", align: "center"}
										, {field: 'expect', title: '预期', width: "40%", align: "center"}
										, {field: 'real', title: '实际', width: "40%", align: "center"}
									]], text: {
										none: '测试全部通过了！'
									}
								});
								// text="接口校验预期："+data.msg[0]["itf_check"]
								// text2 ="数据库校验预期："+data.msg[0]["db_check"]
								// $("#log_text").html(text+'<br>'+text2);
							}
						}
					)
				}
			}
		})






	},

	_removeHoverDom:function(treeId, treeNode) {
	    $("#add_"+treeNode.tId).unbind().remove();
	    $("#up_"+treeNode.tId).unbind().remove();
	    $("#down_"+treeNode.tId).unbind().remove();
	    $("#edit_"+treeNode.tId).unbind().remove();
	    $("#del_"+treeNode.tId).unbind().remove();
	    $("#mimport_"+treeNode.tId).unbind().remove();
	    $("#mexport_"+treeNode.tId).unbind().remove();
	    $("#run_"+treeNode.tId).unbind().remove();
		$("#logs_"+treeNode.tId).unbind().remove();
	},

	_onBeforeExpand:function(e,treeId,treeNode){
		console.log('beforeExpand')

	},
	_beforeRemove:function(e,treeId,treeNode){
        return confirm("你确定要删除吗？");
    },

	_showRemoveBtn:function(treeId, treeNode) {
		//console.log(treeNode)
		return !treeNode.isFirstNode;
	},
	_showRenameBtn:function(treeId, treeNode) {
		return !treeNode.isLastNode;
	},
	_onExpand:function(event,treeId,treeNode){

		console.log('expand.')


	},
	_onCollapse:function(event,treeId,treeNodes){
		console.log('onCollapse')

	}
	,
	_onClick:function(event,treeId,treeNode){
		// alert(treeNode.html())
		console.log('onClick')

		console.log('节点expand状态=>'+treeNode.open)

		var treeObj = $.fn.zTree.getZTreeObj(treeId);
		// var node = treeObj.getNodeByTId(treeNode.tId);

		if(treeNode.type=='root')return

		//jump
		_load_tree_content('/manager/treecontrol/?action=view&uid='+treeNode.id+'&page='+treeNode.type)

		if(treeNode.open){
			treeObj.expandNode(treeNode,false)
			return
		}

		params={'id':treeNode.id,'type':treeNode.type}
		success=function(e){
			console.log('获取子节点数据 =>',params)
			data=JSON.parse(e)
			treeObj.removeChildNodes(treeNode)
			treeObj.addNodes(treeNode, data.data);
			treeObj.expandNode(treeNode,true)

		}
		_post('/manager/querytreelist/',params,success)


	},
	_beforeDrag:function(treeId, treeNodes) {

		// if(treeNodes[0].type=='product'||treeNodes[0].type=='plan' )
		// 	return false

		return true
	},
    _beforeDrop:function(treeId, treeNodes, targetNode, moveType,isCopy) {

    	_allow={
    		'business':['step'],
    		'step':['case'],
    		'case':['plan','case'],
    		'plan':['product'],
    		'product':['root']
    	}
    	_call_map={
    		'business':'测试数据',
    		'step':'测试步骤',
    		'case':'测试用例',
    		'plan':'测试计划',
    		'product':'产品',
    		'root':'根目录'
    	}

    	if(!targetNode){

    		//alert(targetNode)
    		return false
    	}
    	src_type=treeNodes[0].type
    	target_type=targetNode.type
    	expected=_allow[src_type]
    	warn='不允许此操作['+_call_map[src_type]+'->'+_call_map[target_type]+']'

    	if('inner'==moveType){

    		if(expected.indexOf(target_type)==-1){
    			layer.alert(warn,{icon:2,time:2000})
    			return false;
    		}

    	}else{
    		var treeObj = $.fn.zTree.getZTreeObj(treeId);
    		var parent=targetNode.getParentNode();
    	    if(expected.indexOf(parent.type)==-1){
    			layer.alert(warn,{icon:2,time:2000})
    			return false;
    		}


    	}

		return true

    },
    _onDrop:function(event, treeId, treeNodes, targetNode, moveType, isCopy){
		_post('/manager/treecontrol/',{
			'action':'movenode',
			'move_type':moveType,
			'src_id':treeNodes[0].id,
			'target_id':targetNode.id,
			'is_copy':isCopy
		},function(data){
			var node=null

			if(moveType=='inner'){
				node=targetNode

			}else{
				node=targetNode.getParentNode()
			}

			params={'id':node.id,'type':node.type}
			success=function(e){
				console.log('重加载子节点数据 =>',params)
				data=JSON.parse(e)
				var treeObj = $.fn.zTree.getZTreeObj(treeId);
				treeObj.removeChildNodes(node)
				treeObj.addNodes(node, data.data);
				treeObj.expandNode(node,true)

			}
			_post('/manager/querytreelist/',params,success)





		})
	},
}