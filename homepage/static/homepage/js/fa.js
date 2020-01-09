/**
 * 
 * @authors Blackstone (you@example.org)
 * @date    2019-11-20 13:55:14
 * @version $Id$
 */

var fa={
	init:function(){
      var ipt = document.getElementById('gain');   
        var list = document.getElementById('dblist');

        ipt.oninput = function(e){

            var position = getPosition(ipt);
            ipt.value = ipt.value || '';

            var s = ipt.value.charAt(position)
            if((s == "" || s == " ") && ipt.value.charAt(position-1) == "@"){
                var iStyle = window.getComputedStyle(ipt),
                    fz = parseFloat(iStyle.fontSize),
                    wd = parseFloat(iStyle.width),
                    lh = parseFloat(iStyle.lineHeight),
                    pd = parseFloat(iStyle.paddingLeft),

                    newStr = ipt.value.substr(0,position+1),
                    valArr = newStr.indexOf("\n")!==-1 ? newStr.split("\n") : [ipt.value];
                for(var i=0,j=0;i<valArr.length;i++){

                    var len = valArr[i].replace(/[^\x00-\xff]/g,"01").length/2;
                    j += Math.ceil((len*fz)/wd);
                }
                list.style.left = (len*fz)%wd==0?wd:(len*fz)%wd + pd + "px";
                list.style.top = j*lh + "px";
                list.style.display = "block";
            }else{
                list.style.display = "none";
            }
        }

        for(var i=0;i<list.children.length;i++){
            list.children[i].onclick = function(e){
                ipt.value += e.target.innerHTML;
                list.style.display = "none";
            }
        }

        function getPosition(element) {
            var cursorPos = 0;
            if (document.selection) {
                var selectRange = document.selection.createRange();
                selectRange.moveStart('character', -element.value.length);
                cursorPos = selectRange.text.length;
            } else if (element.selectionStart || element.selectionStart == '0') {
                cursorPos = element.selectionStart;
            }
            return cursorPos;
        }




	}
}