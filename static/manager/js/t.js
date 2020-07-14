/*下拉树形图*/
    var setting = {
        view: {
            showIcon: true,//设置 zTree 是否显示节点的图标。默认值：true
            showLine: false//设置 zTree 是否显示节点之间的连线。默认值：true
        },
        data: {
            simpleData: {
                enable: true
            }
        },
        callback: {
            onClick: onClick
        }
    };

    function onClick(e, treeId, treeNode) {
        $('#txtselect').val(treeNode.name);
    }

    function showMenu() {
        var cityObj = $('#txtselect');
        var cityOffset = cityObj.offset();
        $("#menuContent").css({ left: cityOffset.left + "px", top: cityOffset.top + cityObj.outerHeight() + "px" }).slideDown("fast");
        $("body").bind("mousedown", onBodyDown);
    }

    function hideMenu() {
        $("#menuContent").fadeOut("fast");
        $("body").unbind("mousedown", onBodyDown);
    }
    function onBodyDown(event) {
        if (!(event.target.id == "menuBtn" || event.target.id == "menuContent" || $(event.target).parents("#menuContent").length > 0)) {
            hideMenu();
        }
    }

    $(document).ready(function () {
        var zNodes =[
            { id:1, pId:0, name:"河北", open:true},
            { id:11, pId:1, name:"石家庄"},
            { id:111, pId:11, name:"衡水"},
            { id:112, pId:11, name:"邢台"},
            { id:113, pId:11, name:"承德"},
            { id:114, pId:11, name:"保定"},
            { id:12, pId:1, name:"河南"},
            { id:121, pId:12, name:"郑州"},
            { id:122, pId:12, name:"郑州1"},
            { id:123, pId:12, name:"郑州2"},
            { id:124, pId:12, name:"郑州3"},
            { id:13, pId:1, name:"武汉", isParent:true},
            { id:2, pId:0, name:"四川"},
            { id:21, pId:2, name:"成都", open:true},
            { id:211, pId:21, name:"成都1"},
            { id:212, pId:21, name:"成都2"},
            { id:213, pId:21, name:"成都3"},
            { id:214, pId:21, name:"成都4"},
            { id:22, pId:2, name:"贵州"},
            { id:221, pId:22, name:"云南白药"},
            { id:222, pId:22, name:"云南白药1"},
            { id:223, pId:22, name:"云南白药2"},
            { id:224, pId:22, name:"云南白药3"},
            { id:23, pId:2, name:"云南"},
            { id:231, pId:23, name:"昆明"},
            { id:232, pId:23, name:"弥勒"},
            { id:233, pId:23, name:"西双版纳"},
            { id:234, pId:23, name:"云南白药"},
            { id:3, pId:0, name:"深圳", isParent:true}
        ];

        $.fn.zTree.init($("#treeDemo"), setting, zNodes);
        // showMenu()

        console.log('treeDemo init finish..')
    });
