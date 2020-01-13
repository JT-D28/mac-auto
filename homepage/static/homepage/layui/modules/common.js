layui.define(['jquery'], function(exports){
    var $ = layui.jquery;
    var obj = {
        ajax: function (url, type, dataType, data, callback) {
            $.ajax({
                beforeSend:function(){
                            layui.use(['layer'], function(){
                                loadIndex = layer.load(1, {
                                    shade: [0.1, '#393D49'],
                                });
                            })
                        },
                complete:function(XMLHttpRequest,status){
                            layui.use(['layer'], function(){
                                layer.close(loadIndex);
                            })
                        },
                url: url,
                type: type,
                dataType: dataType,
                data: data,
                success: callback,
                error:function(e){
                            layer.alert(e.msg,{icon:5,time:3000})
                        }
            });
        }
    };
    //输出接口
    exports('common', obj);
});
