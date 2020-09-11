layui.define(["jquery"], function (exports) {
    var $ = layui.jquery;
    var BCK = {
        _elem: null,
        _config: null,
        _hosts: [],
        _include: ['application/x-www-form-urlencoded', 'application/json'],
        render: function (config) {
            this._config = config;
            console.log('初始化配置：' + JSON.stringify(this._config));
            this._elem = $(this._config['elem']);
            this._elem.css('position', 'fixed');
            this._elem.css('z-index', 10001);
            this._elem.css('right', '10px');
            this._elem.css('max-height', '90%');
            this._elem.css('overflow-y', 'auto');
            this._elem.css('background-color', '#CCFFCC');
            this._elem.css('opacity', '0.8');
            this._elem.css('border-radius', '5px');
            if($('#grab-info').length<1)
                this._elem.append("<li class='fa fa-info-circle' id='grab-info'></li>")
            if($('#grab-info-content').length<1) {
                this._elem.append("<div id='grab-info-content'></div>");
                $('#grab-info').removeClass('fa-info-circle');
                $('#grab-info').addClass('fa-arrow-circle-o-right')
            }
            $('body').append("<table id='grab-params' class='' hidden>" +
                "<thead>" +
                "<tr>params</tr>" +
                "</thead>" +
                "<tbody></tbody>" +
                "</table>")
            $('#grab-info').on('click',function () {
                $('#grab-info-content').toggleClass('grab-hide');
                if($(this).hasClass('fa-info-circle')) {
                    $(this).removeClass('fa-info-circle');
                    $(this).addClass('fa-arrow-circle-o-right')
                }
                else {
                    $(this).removeClass('fa-arrow-circle-o-right');
                    $(this).addClass('fa-info-circle')
                }

            });

            //this.load(this._config['data'])
        },
        reload: function (config) {
            this.load(config['data']);
        },
        load: function (data) {
            var timetamp = Number(new Date());
            console.log('timestamp:', timetamp)
            var node_show = false;
            u = undefined;
            try {
                //console.log('读取数据:',data);
                u = JSON.parse(data)
            } catch (e) {
                console.log('json解析异常：',e,data);
                return false;
            }
            //
            url_tmp = "<li class='bck-node bck-node-url' title='#tip#' host='#host#' params='#params#' c1='#c1#' c2='#c2#' time='#time#' is-https='#ishttps#'  method='#method#' url='#url#' headers='#headers#'>#title#</li>";
            params = u['body'];
            url = u['url'].replace(u['host'], '');
            host = u['host'];
            is_https = u['ishttps'];
            method = u['method'];
            headers = '{}'
            if (u['request_headers'])
                rqc = u['request_headers']['Content-Type']
            headers = JSON.stringify(u['request_headers'])

            if (u['response_headers'])
                rpc = u['response_headers']['Content-Type']

            console.info('挂载数据：', {
                'method': method,
                'is_https': is_https,
                'host': host,
                'url': url,
                'params': params,
                'rqc': rqc,
                'rpc': rpc
            });
            exclude=['text/css','application/javascript','image/jpeg','image/svg+xml','application/octet-stream'];
            for(var k=0;k<exclude.length;k++){
                if(rpc&&rpc.indexOf(exclude[k])>-1)
                    return
            }


            url_tmp = url_tmp.replace('#title#', url);
            url_tmp = url_tmp.replace('#url#', url);
            url_tmp = url_tmp.replace('#tip#', url);
            url_tmp = url_tmp.replace('#params#', params);
            url_tmp = url_tmp.replace('#c1#', rqc);
            url_tmp = url_tmp.replace('#c2#', rpc);
            url_tmp = url_tmp.replace('#time#', timetamp);
            url_tmp = url_tmp.replace('#method#', method);
            url_tmp = url_tmp.replace('#ishttps#', is_https);
            url_tmp = url_tmp.replace('#host#', host);
            url_tmp = url_tmp.replace('#headers#', headers);

            if (this._hosts.indexOf(host) == -1) {
                this._hosts.push(host);
                this._elem.find('#grab-info-content').append("<li class='bck-node bck-node-host' host='" + host + "'><i class='fa fa-home'></i><host>" + host + "</host><div class='alias'>[alias]</div></li>");
            }
            //
            $('.alias').each(function () {
                $(this).off('click').on('click', function (e) {
                    e.stopPropagation();
                    is_editable = $(this).attr('contenteditable');
                    if ('true' == is_editable) {


                    } else {
                        let range = document.createRange();
                        range.selectNodeContents(this);
                        range.collapse(false);
                        let sel = window.getSelection();
                        sel.removeAllRanges();
                        sel.addRange(range);

                        $(this).attr('contenteditable', 'true');
                        $(this).css('background-color', '#FF5722');
                    }

                    return false;

                });


            });

            $(document).on('click', function (e) {
                if ($(e.target).attr('class') != 'alias') {
                    $('.alias').each(function () {
                        if ($(this).text().trim() == '' || $(this).text().trim() == '[alias]') {
                            $(this).text('[alias]');
                            $(this).css('color', '#FFB800');
                        } else
                            $(this).css('color', '#01AAED')

                        $(this).attr('contenteditable', 'false');
                        $(this).css('background-color', 'unset');

                    });

                }

                e.stopPropagation();

            });
            index = this._hosts.indexOf(host);
            console.log($(".bck-node-host:eq(" + index + ")"));
            $(".bck-node-host:eq(" + index + ")").append(url_tmp);
            //EVENT add
            target = $("[time='" + timetamp + "']");
            var this_ = this;
            if (this._config.dblclick) {
                target.off('dblclick').on('dblclick', function () {
                    this_._config.dblclick($(this));
                });
            }
            target.off('mouseenter').on('mouseenter', function (e) {
                //ps={}
                console.log(e.clientX, e.clientY);
                $('#grab-params tbody').empty();
                $('#grab-params').css('right', '320px');
                $('#grab-params').show();


                kvs = $(this).attr('params').split('&');
                for (var i = 0; i < kvs.length; i++) {
                    // ps[kvs[i].split('=')[0]]=kvs[i].split('=')[1]
                    k = kvs[i].split('=')[0];
                    v = kvs[i].split('=')[1];
                    if (k)
                        $('#grab-params tbody').append("<tr><td>" + k + "</td><td>" + v + "</td></tr>");
                }
                // alert('height:',$('#grab-params').height(),e.clientY,document.body.clientHeight);
                console.log('height:', $('#grab-params').height(), e.clientY, document.body.clientHeight);
                if (document.body.clientHeight - e.clientY - $('#grab-params').height() < 120)
                    $('#grab-params').css('top', 'unset').css('bottom', '20px');
                else
                    $('#grab-params').css('bottom', 'unset').css('top', e.clientY + 40 + 'px')
                // $('#grab-params').show();
            });
            $('#grab-params').off('mouseleave').on('mouseleave', function () {
                $(this).hide();

            })


        }
    }

    exports('grabView', BCK);
});