/**
 * 
 * @authors Blackstone (you@example.org)
 * @date    2019-08-30 17:35:25
 * @version $Id$
 */


// var usercache='unexpected'

// var host='10.60.45.63:8000'
var host=window.location.host
console.log(host)

var http_base='http://'+host

function connect_on(){

	$("#interface-list").val("")
	// alert($("#interface-list"))

    let chatSocket = new WebSocket(
        "ws://"+host+"/ws/intercept/"

    );
    console.log("connected .")

    chatSocket.onmessage = function (e) {
            let data = JSON.parse(e.data);
            console.log(data)
            let message="<a class='list-group-item' class='url' id='"+data['url']+"' header='' body=''>"+data['url']+"</a>";
            //alert(message)
            $("#interface-list").prepend(message);
            $('#interface-list').off('click','a');
            $('#interface-list').on("click",'a',function(){
                //console.log($(this).attr('id'))
                $('#interface-url').val($(this).attr('id'));
                $('#interface-header').val($(this).attr('header'));
                $('#interface-body').val($(this).attr('body'));

            });

        };
    chatSocket.onclose=function (e) {
        console.log("chat socket closed unexpectly");
    };

    // chatSocket.send('');


};


function insertAtCursor(myField, myValue) {
 
   //IE 浏览器
   if (document.selection) {
     myField.focus();
     sel = document.selection.createRange();
     sel.text = myValue;
     sel.select();
   }
 
   //FireFox、Chrome等
   else if (myField.selectionStart || myField.selectionStart == '0') {
     var startPos = myField.selectionStart;
     var endPos = myField.selectionEnd;
 
     // 保存滚动条
     var restoreTop = myField.scrollTop;
     myField.value = myField.value.substring(0, startPos) + myValue + myField.value.substring(endPos, myField.value.length);
     
     if (restoreTop > 0) {
      myField.scrollTop = restoreTop;
     }
     
     myField.focus();
     myField.selectionStart = startPos + myValue.length;
     myField.selectionEnd = startPos + myValue.length;
   } else {
     myField.value += myValue;
     myField.focus();
   }
 }

/**
**快捷输入变量&属性引用
**/

function add_var_prop_smart_inputs(elemIds){
  for(var index=0;index<elemIds.length;index++){
    add_var_prop_smart_input(elemIds[index])
  }
  
}
function add_var_prop_smart_input(elemId){

  dom=document.getElementById(elemId)
  dom.removeEventListener('keydown',undefined)
  dom.onkeydown=function(e){

        if(e.keyCode==66&&e.ctrlKey){
          console.log('ctrl+B')
          layer.prompt({
            title:'插入变量'},
            function(value, index, elem){

              insertAtCursor(document.getElementById(elemId),'{{'+value+'}}')


            layer.close(index);
          }
          );
          console.log($(this).selectionStart)

        }
        else if(e.keyCode==88&&e.ctrlKey){
          console.log('ctrl+X')
          layer.prompt({
            title:'插入属性'},
            function(value, index, elem){

              insertAtCursor(document.getElementById(elemId),'${'+value+'}')

            layer.close(index);
          }
          );
          console.log($(this).selectionStart)

        }

  }

}
/**
数据库下拉框加载
**/

function _load_db_dropdownlist(kind,id){

  var tmp="<option value='#id#' class='dboption' name='ooo'>#dbname#</option>"
  success=function(res){
    res=JSON.parse(res)
    if(res.code==0){

      dft=tmp.replace('#dbname#','请选择').replace('#id#',"")
      $("[name='db_id']").append(dft)
      for(var index=0;index<res.data.length;index++){
        id=res.data[index]['id']
        dbname=res.data[index]['name']
        t=tmp.replace('#id#',id).replace('#dbname#',dbname)
        $("[name='db_id']").append(t)
    

      }

      console.log('加载数据库信息列表成功')


    }else{
      layer.alert('数据库信息查询失败',{icon:2})
    }

  }
  _post('/manager/querydblist/',{},success)
}



/***
@联想

**/
function show_lx(elem) {


  $("[name='gain']").on("input propertychange",function(e){

    var len=$(this).val().length
    var last_word=$(this).val().charAt(len-1)

    if(last_word=='@'){
      layer.msg('输入@')
      // $("#show").show()
      var p = kingwolfofsky.getInputPositon(elem);

      console.log('坐标=>'+p.left+","+p.bottom)
      var s = document.getElementById('show');
      // s.style.marginTop='';
      s.style.top = p.bottom+'px';
      s.style.left = p.left + 'px';
      //s.style.display = 'inherit';

      // if(kingwolfofsky._COUNT==1)
      //   s.style.marginTop='200px';
      s.style.display='inline'

      alert(document.getSelection())

      var o=document.getSelection().createRange()
      alert(o.offsetTop+","+o.offsetLeft)


      // kingwolfofsky._COUNT= kingwolfofsky._COUNT+1
     
    }
    console.log(last_word)
  });
}

/***

**/

function _load_tree_content(url){

  console.log('load page=>'+url)


  $('#tree-content').attr('src',url)
}


function _get_query_param(pname)
{
       var query = window.location.search.substring(1);
       //console.log('query params=>',query)
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] == pname){return pair[1];}
       }
       return(false);
}


function _fill_form(data,fieldids){

  /***
  {
  
  type:'input',

  }
  [input]
  [radio]
  [select]
  **/
  if(typeof(data)==='string')
    data=JSON.parse(data)


  for(var  i =0;i<fieldids.length;i++){

    dom=$('#'+fieldids[i])
    if(dom){


    }else{
      console.error('')
    }


  }


  layui.form.render('select')



}

function _get(url,data,success,headers={}){
    //data['username']=$("#username").text()
    //alert($("#username").text())

    // console.log('username=>'+$('#username').text())
    // console.log('username=>'+window.sessionStorage.getItem("username"))
    // //console.log('username'+{%request.session.username%})
    // console.log('username=>'+window.usercache)
    // data['username']='tester'
    console.log("【GET】"+url)
    console.log("【data】"+JSON.stringify(data))
    var loadIndex=''
    var ajaxobj=$.ajax({
      headers:headers,
      type: 'GET',
      // timeout:6000,
      url: http_base+url,
      data: data,
      success: success,
      dataType: 'json',
      complete:function(XMLHttpRequest,status){
    
        layui.use(['layer'], function(){
            layer.close(loadIndex);
        });

        // if(status=='timeout'){
        //   ajaxobj.abort();
        //   layer.alert('请求超时!',{icon:2})

        // }

      },
      beforeSend:function(){

        layui.use(['layer'], function(){
            loadIndex = layer.load(1, {
                shade: [0.7, '#393D49']
            });
        })

      },
    });

};



function _post(url,data,success){

  // console.log(getCookie("csrftoken"));
  var loadIndex=''
    var ajaxobj=$.ajax({
      type: 'POST',
      // timeout:6000,
      url: http_base+url,
      data: data,
      // headers:{ "X-CSRFtoken":"jjjjfjavvv"},
      success: success,
      complete:function(XMLHttpRequest,status){
    
        layui.use(['layer'], function(){
            layer.close(loadIndex);
        })


      },
      beforeSend:function(){

        layui.use(['layer'], function(){
            loadIndex = layer.load(1, {
                shade: [0.7, '#393D49']
            });
        })

      },
      dataType: 'json'
    });
};




// alert('start refresh.')

