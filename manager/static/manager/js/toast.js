var toast={

    /**
     * 右下角提示框
     * @param title
     * @param info
     */
    _getcontent:function(title,info,type) {
        if(type==0){
            return '<div class="toast toast--green">' +
                '  <div class="toast__icon">' +
                '    <svg version="1.1" class="toast__svg" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 512 512" style="enable-background:new 0 0 512 512;" xml:space="preserve">' +
                '<g><g><path d="M504.502,75.496c-9.997-9.998-26.205-9.998-36.204,0L161.594,382.203L43.702,264.311c-9.997-9.998-26.205-9.997-36.204,0    c-9.998,9.997-9.998,26.205,0,36.203l135.994,135.992c9.994,9.997,26.214,9.99,36.204,0L504.502,111.7    C514.5,101.703,514.499,85.494,504.502,75.496z"></path>' +
                '</g></g>' +
                '    </svg>' +
                '  </div>' +
                '  <div class="toast__content">' +
                '    <p class="toast__type">'+title+'</p>' +
                '    <p class="toast__message">'+info+'</p>' +
                '  </div>' +
                '  <div class="toast__close">' +
                '    <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 15.642 15.642" xmlns:xlink="http://www.w3.org/1999/xlink" enable-background="new 0 0 15.642 15.642"> ' +
                '</svg>' +
                '  </div>' +
                '</div>'
        }else if(type==1){
            return '<div class="toast toast--blue add-margin">' +
                '  <div class="toast__icon">' +
                '<svg version="1.1" class="toast__svg" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 32 32" style="enable-background:new 0 0 32 32;" xml:space="preserve">' +
                '<g>' +
                '<g id="info">' +
                '<g>' +
                '<path  d="M10,16c1.105,0,2,0.895,2,2v8c0,1.105-0.895,2-2,2H8v4h16v-4h-1.992c-1.102,0-2-0.895-2-2L20,12H8     v4H10z"></path>' +
                '<circle  cx="16" cy="4" r="4"></circle>' +
                '</g>' +
                '</g>' +
                '</g>' +
                '' +
                '    </svg>' +
                '  </div>' +
                '  <div class="toast__content">' +
                '    <p class="toast__type">'+title+'</p>' +
                '    <p class="toast__message">'+info+'</p>' +
                '  </div>' +
                '  <div class="toast__close">' +
                '    <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 15.642 15.642" xmlns:xlink="http://www.w3.org/1999/xlink" enable-background="new 0 0 15.642 15.642">' +
                '' +
                '</svg>' +
                '  </div>' +
                '</div>'
        }else{
            return '<div class="toast toast--yellow add-margin">' +
                '  <div class="toast__icon">' +
                '<svg version="1.1" class="toast__svg" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 301.691 301.691" style="enable-background:new 0 0 301.691 301.691;" xml:space="preserve">' +
                '<g>' +
                '<polygon points="119.151,0 129.6,218.406 172.06,218.406 182.54,0  "></polygon>' +
                '<rect x="130.563" y="261.168" width="40.525" height="40.523"></rect>' +
                '</g>' +
                '    </svg>' +
                '  </div>' +
                '  <div class="toast__content">' +
                '    <p class="toast__type">'+title+'</p>' +
                '    <p class="toast__message">'+info+'</p>' +
                '  </div>' +
                '  <div class="toast__close">' +
                '    <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 15.642 15.642" xmlns:xlink="http://www.w3.org/1999/xlink" enable-background="new 0 0 15.642 15.642">' +
                '</svg>' +
                '  </div>' +
                '</div>'
        }
    },
	msg:function (title,info,type) {
	        // $('head').find('link[href="${appPath}/layui/css/svg.css"]').remove();
	        // $('head').prepend("<link href='${appPath}/layui/css/svg.css' rel='stylesheet' type='text/css' />");
            layer.open({
                offset: 'rb',
                title: false,
                area: ['350px', '85px'],
                shade: 0,
                type: 1,
                content:this._getcontent(title,info,type),
                time: 10000,
                icon: 1,
                anim: 2
            });
	    }
}