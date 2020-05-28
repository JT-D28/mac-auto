var app = new Vue({
    el: '#app',
    delimiters: ['${', '}'],
    data() {
        var vue = this;
        return {
            props: {
                label: 'name',
                id: 'id'
            },
            showReport: false,
            productCountnum: '',
            productRatenum: '',
            noticeSetVisible: false,
            runningState: '',
            log_text: '',
            synchronize: '获取',
            Coverage: {
                branchCoverage: {
                    "covered": 0,
                    "missed": 0,
                    "percentageFloat": 0,
                    "total": 0
                },
                classCoverage: {
                    "covered": 0,
                    "missed": 0,
                    "percentageFloat": 0,
                    "total": 0
                },
                complexityScore: {
                    "covered": 0,
                    "missed": 0,
                    "percentageFloat": 0,
                    "total": 0
                },
                instructionCoverage: {
                    "covered": 0,
                    "missed": 0,
                    "percentageFloat": 0,
                    "total": 0
                },
                lineCoverage: {
                    "covered": 0,
                    "missed": 0,
                    "percentageFloat": 0,
                    "total": 0
                },
                methodCoverage: {
                    "covered": 0,
                    "missed": 0,
                    "percentageFloat": 0,
                    "total": 0
                }
            },
            historytime: '',
            timeDefaultShow: '',
            pickerOptions: {
                shortcuts: [{
                    text: '最近3天',
                    onClick(picker) {
                        const end = new Date();
                        const start = new Date();
                        start.setTime(start.getTime() - 3600 * 1000 * 24 * 3);
                        picker.$emit('pick', [start, end]);
                    }
                }, {
                    text: '最近一周',
                    onClick(picker) {
                        const end = new Date();
                        const start = new Date();
                        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
                        picker.$emit('pick', [start, end]);
                    }
                }, {
                    text: '最近一个月',
                    onClick(picker) {
                        const end = new Date();
                        const start = new Date();
                        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
                        picker.$emit('pick', [start, end]);
                    }
                }, {
                    text: '最近三个月',
                    onClick(picker) {
                        const end = new Date();
                        const start = new Date();
                        start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
                        picker.$emit('pick', [start, end]);
                    }
                }],
                disabledDate(time) {
                    return time.getTime() > Date.now();
                }, onPick(time) {
                    if (time.minDate && !time.maxDate) {
                        vue.timeOptionRange = time.minDate;
                    }
                    if (time.maxDate) {
                        vue.timeOptionRange = null;
                    }
                }
            },
            oldBugData: [{
                路径: '',
                接口: '',
                测试点: '',
                参数信息: '',
                失败原因: '',
                任务id: '',
            }],
            mailcolors: [{id: 1, color: 'blue'}, {id: 2, color: 'red'}],
            products: [],
            plans: [],
            dbschemes: [],
            services: [],
            runVisible: false,
            productSetVisible: false,
            topposition: 'top',
            rightposition: 'right',
            planHistoryVisible: false,
            form: {
                debug_url: '',
                is_verify_url: '',
                formLabelWidth: '120px',
                product: '',
                third_plan: '',
                third_dbschemes: '',
                forceStopPlans: '',
                plan: '',
                service: '',
                mailcolor: '',
                productset: {
                    jenkinsurl: '',
                    authname: '',
                    authpwd: '',
                    jobname: '',
                    order: '',
                    jacocoClearJob: ''
                },
                reportNoticeSet: {
                    color: '',
                    to_receive: '',
                    description: '',
                    text: '',
                    dingdingtoken: ''
                }
            },
        }
    },
    methods: {
        getproduct() {
            var that = this;
            _post_nl('/homepage/queryproduct/', {}, function (data) {
                var data = JSON.parse(data);
                that.products = data.data
            })
        },
        selectProduct() {
            var that = this;
            this.form.plan = '';
            _post_nl('/homepage/queryplan/', {id: this.form.product}, function (data) {
                data = JSON.parse(data)
                that.plans = data.data;
                that.services = data.service;
                that.form.plan = that.plans[0] != null ? that.plans[0].id : ''
                that.form.service = that.services[0] != null ? [that.services[0].id] : []
                that.getReportChart()
                that.getproductReport(data.rate, data.total)
                that.showReport = true
                productPiclist.forEach(function (item, index) {
                    setTimeout(() => actproduct[index].resize(), 0)
                });
                that.jacocoReFlash('get')
            })
        },
        runplan() {
            var that = this;
            planid = that.form.plan.substr(5);
            if (planid != '') {
                _post_nl('/manager/runplan', {ids: planid, is_verify: '1'}, function (data) {
                    data = JSON.parse(data)
                    if (data.code == 0) {
                        layer.msg(data.msg, {
                            time: 30000,
                            shade: 0.2,
                            shadeClose: true,
                            btn: ['火速围观', '残忍拒绝'],
                            yes: function (index, layero) {
                                window.top.document.getElementById("console").click()
                                layer.close(index)
                            }
                        });
                    } else layer.msg(data.msg)
                })
            } else {
                this.$message({
                    message: '请选择项目和计划',
                    type: 'error', center: true
                });
            }
        },
        setplan() {
            var that = this;
            var productid = that.form.product;
            if (productid == '') {
                this.$message({
                    message: '请选择项目',
                    type: 'error', center: true
                });
            } else {
                _post_nl('/homepage/queryProductSet/', {productid: productid}, function (data) {
                    if (data.code == 0) {
                        if (data.data != '') {
                            that.form.productset.jenkinsurl = data.data.jenkinsurl;
                            that.form.productset.authname = data.data.authname
                            that.form.productset.authpwd = data.data.authpwd
                            that.form.productset.jobname = data.data.jobname
                            that.form.productset.jacocoClearJob = data.data.clearjob
                            that.productSetVisible = true;
                            if (data.data.buildplans.length != 0) {
                                setTimeout(() => {
                                    app.$refs.tree.setCheckedNodes(data.data.buildplans)
                                }, 100)
                            }
                        } else {
                            that.productSetVisible = true;
                        }
                    } else {
                        layer.msg(data.msg)
                    }
                })
                _post_nl('/manager/queryDbScheme/', {action: 1}, function (data) {
                    if (data.code == 0) {
                        that.dbschemes = data.data
                    }
                })
            }
        },
        jacocoSetSave() {
            var that = this;
            var jenkinsurl = that.form.productset.jenkinsurl;
            var authname = that.form.productset.authname;
            var authpwd = that.form.productset.authpwd;
            var jobname = that.form.productset.jobname;
            var jacocoClearJob = that.form.productset.jacocoClearJob;
            var productid = that.form.product;
            var plansrun = []
            checknodes = app.$refs.tree.getCheckedNodes()
            for (j = 0, len = checknodes.length; j < len; j++) {
                plansrun.push(checknodes[j].id)
            }
            var buildplans = plansrun.join(',')
            _post_nl('/homepage/editProductSet/', {
                'productid': productid, 'jenkinsurl': jenkinsurl, 'buildplans': buildplans,
                'authname': authname, 'authpwd': authpwd, 'jobname': jobname, 'jacocoClearJob': jacocoClearJob
            }, function (data) {
                if (data.code == 0) {
                    layer.msg(data.msg);
                    that.productSetVisible = false;
                } else layer.msg(data.msg)
            })
        },
        planHistory() {
            var that = this;
            planid = that.form.plan.substr(5);
            if (planid != '') {
                const start = new Date().toJSON().substr(0, 10);
                const end = new Date().toJSON().substr(0, 10);
                this.historytime = [start, end];
                this.queryOldBug('omit');
                this.planHistoryVisible = true
            } else this.$message({
                message: '请选择项目',
                type: 'error', center: true
            });
        },
        newRepoet() {
            var that = this;
            planid = that.form.plan.substr(5)
            if (planid == '') {
                this.$message({
                    message: '请选择项目和计划',
                    type: 'error', center: true
                });
            } else {
                _post_nl('/homepage/querytaskid/', {'planid': planid, 'action': 'plan'}, function (data) {
                    data = JSON.parse(data)
                    taskid = data.data
                    if (data.code != 0) {
                        layer.msg(data.msg);
                    } else {
                        var resulturl = '/manager/querytaskdetail/?taskid=' + taskid
                        //window.open(resulturl)
                        layer.open({
                            type: 2,
                            title: false,
                            shade: [0],
                            area: ['90%', '90%'],
                            anim: 2,
                            shadeClose: true,
                            content: [resulturl, 'yes'], //iframe的url，no代表不显示滚动条
                        });
                    }
                })
            }
        },
        setPlanNotice() {
            var that = this;
            var planid = that.form.plan.substr(5);
            if (planid == '') {
                this.$message({
                    message: '请选择计划',
                    type: 'error', center: true
                });
            } else {
                _post_nl('/manager/queryonemailconfig/', {id: planid}, function (data) {
                    if (data.code == 0) {
                        that.form.reportNoticeSet.color = data.data.color_scheme != 'None' ? data.data.color_scheme : '';
                        that.form.reportNoticeSet.to_receive = data.data.to_receive != 'None' ? data.data.to_receive : '';
                        that.form.reportNoticeSet.description = data.data.description != 'None' ? data.data.description : '';
                        that.form.reportNoticeSet.text = data.data.rich_text != 'None' ? data.data.rich_text : '';
                        that.form.reportNoticeSet.dingdingtoken = data.data.dingdingtoken != 'None' ? data.data.dingdingtoken : ''
                        that.noticeSetVisible = true;
                    } else {
                        layer.msg(data.msg)
                    }
                })
            }
        },
        savenoticeSet(ss) {
            var that = this;
            var planid = that.form.plan.substr(5);
            _post_nl("/manager/editmailconfig/", {
                id: planid,
                color_scheme: that.form.reportNoticeSet.color,
                description: that.form.reportNoticeSet.description,
                to_receive: that.form.reportNoticeSet.to_receive,
                rich_text: that.form.reportNoticeSet.text,
                dingdingtoken: that.form.reportNoticeSet.dingdingtoken,
            }, function (data) {
                data = JSON.parse(data);
                if (data.code == 0 && ss == 0) {
                    that.noticeSetVisible = false;
                    layer.msg(data.msg)
                } else if (data.code == 0 && ss == 1) {
                    return
                } else layer.alert(data.msg, {icon: 2, time: 2000})
            })
        },
        sendRepoet() {
            var that = this;
            if (that.form.reportNoticeSet.to_receive == undefined) {
                layer.alert("请检查内容！", {icon: 2, time: 1500})
            }
            that.savenoticeSet(1);
            planid = that.form.plan.substr(5);
            _post_nl('/homepage/sendreport/', {'planid': planid}, function (data) {
                data = JSON.parse(data)
                if (data.code == 0) {
                    layer.alert(data.msg, {icon: 1, time: 1500}, area = ['500px', '300px'])
                    that.noticeSetVisible = false;
                } else {
                    layer.alert(data.msg, {icon: 2, time: 1500})
                }
            })
        },
        seeprocess() {
            var that = this;
            planid = that.form.plan.substr(5);
            if (planid == '') {
                this.$message({
                    message: '请选择项目和计划',
                    type: 'error', center: true
                });
            } else {
                _post_nl('/homepage/querytaskid/', {'planid': planid, 'action': 'plan'}, function (data) {
                    data = JSON.parse(data)
                    taskid = data.data
                    is_running = data.is_running
                    if (data.code != 0) {
                        layer.msg(data.msg);
                    } else {
                        var logSocket = new WebSocket("ws://" + host + "/ws/runlog/");
                        layer.open({
                            type: 1,
                            id: "log-process",
                            title: false,
                            shade: [0],
                            area: ['90%', '90%'],
                            anim: 2,
                            shadeClose: true,
                            content: $("#seeprocess"),
                            success: function () {
                                $("#log_text").html('')
                                logSocket.onopen = function () {
                                    logSocket.send(is_running + '::' + taskid)
                                };
                                logSocket.onmessage = function (e) {
                                    e = JSON.parse(e.data);
                                    setTimeout(() => {
                                        const total = e.count;
                                        const once = is_running !== '0' ? 200 : 5000;
                                        const loopCount = total / once;
                                        let countOfRender = 0;
                                        let ul = document.getElementById("log_text");

                                        function add() {
                                            //   console.time('get')
                                            const fragment = document.createDocumentFragment();
                                            // for (let i = 0; i < once; i++) {
                                            //     const li = document.createElement("li");
                                            //      li.innerHTML = e.data[once * countOfRender + i] != undefined ? e.data[once * countOfRender + i] : '';
                                            //       fragment.appendChild(li);
                                            //    }
                                            //   console.timeEnd('get')

                                            const li = document.createElement("li");
                                            li.innerHTML = ArraytoString(e.data.slice(once * countOfRender, once * (countOfRender + 1)));
                                            fragment.appendChild(li);
                                            ul.appendChild(fragment);
                                            countOfRender += 1;
                                            loop();
                                            var exits = document.getElementById('log-process');
                                            if (is_running !== '0' && exits != null) {
                                                exits.scrollTop = exits.scrollHeight;
                                            }
                                        }

                                        function loop() {
                                            if (countOfRender < loopCount) {
                                                window.requestAnimationFrame(add);
                                            }
                                        }

                                        loop();
                                    }, 100);
                                };
                                logSocket.onclose = function () {
                                    console.log("结束获取日志..")
                                }
                            }, end: function () {
                                logSocket.close();
                                $("#log_text").html('')
                            }
                        });
                    }
                })
            }
        },
        reportconfig(data, code) {
            x = [];
            success = [];
            total = [];
            fail = [];
            skip = [];
            error = [];
            success_rate = []
            hundred = [];
            taskids = [];
            if (code == 0) {
                title = data[0][1]
                for (let i = data.length - 1; i >= 0; i--) {
                    x.push(data[i][7])
                    success.push(data[i][2])
                    total.push(data[i][5])
                    fail.push(data[i][3])
                    skip.push(data[i][4])
                    error.push(data[i][9])
                    //mysql  success_rate.push(data[i][8].substr(0, 5))
                    success_rate.push(data[i][8])
                    taskids.push(data[i][6])
                    hundred.push(100 - data[i][8])
                }
                totalmax = total.map(function (e) {
                    return Math.max.apply(null, total)
                });
            } else {
                title = data
                totalmax = 1
            }
            var optionRecords = {
                animation: false,
                legend: {
                    right: '0.7%',
                    top: '3%',
                    data: ['成功率', '成功数', '失败数', '错误数', '跳过数', '失败率']
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'cross'
                    },
                    backgroundColor: 'rgba(255,255,255,1)',
                    borderWidth: 1,
                    borderColor: '#ccc',
                    padding: [12, 12, 4, 12],
                    textStyle: {
                        color: '#000'
                    },
                    width: '110px',
                    position: function (pos, params, el, elRect, size) {
                        var obj = {top: 10};
                        obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 30;
                        return obj;
                    },
                    formatter: function (params) {
                        res = '<p style="margin-bottom:4px;width:66px;height:17px;font-size:12px;font-family:PingFang-SC-Regular,PingFang-SC;font-weight:400;color:rgba(51,51,51,1);line-height:17px;">' + params[0].name + '</p>'
                        res += '<div style="margin-bottom:14px;width:12px;height:12px;background:rgba(221,221,221,1);border-radius:1px;">' + '<p style="font-size:12px;font-family:PingFang-SC-Regular,PingFang-SC;font-weight:400;color:rgba(51,51,51,1);line-height:12px;">' + params[4].marker + ' ' + params[4].seriesName + '：' + params[4].value + '%' + '</p>' + '</div>'
                        for (var i = 0; i < params.length - 1; i++) {
                            res += '<p style="margin-bottom:8px;font-size:12px;font-family:PingFang-SC-Regular,PingFang-SC;font-weight:400;color:rgba(51,51,51,1);line-height:12px;">' + params[i].marker + ' ' + params[i].seriesName + '：' + params[i].value + '</p>'
                        }
                        return res
                    },
                    extraCssText: 'width: 110px'
                },
                axisPointer: {
                    link: {xAxisIndex: 'all'},
                    label: {
                        backgroundColor: '#777'
                    }
                },
                grid: [
                    {
                        top: '80px',
                        left: '65px',
                        right: '65px',
                        bottom: '40px',
                    },
                ],
                xAxis: [
                    {
                        type: 'category',
                        data: x,
                        scale: true,
                        boundaryGap: false,
                        axisLine: {onZero: false},
                        axisLabel: {
                            interval: 1,  //控制坐标轴刻度标签的显示间隔.设置成 0 强制显示所有标签。设置为 1，隔一个标签显示一个标签。设置为2，间隔2个标签。以此类推
                            rotate: 0,//倾斜度 -90 至 90 默认为0
                            textStyle: {
                                fontSize: 12,
                                fontFamily: 'ingFang-SC-Regular,PingFang-SC',
                                fontWeight: "400",  //加粗
                                color: "rgba(153,153,153,1)"   //黑色
                            },
                        },
                        splitLine: {show: false},
                        splitNumber: 3,
                        min: 'dataMin',
                        max: 'dataMax',
                        axisPointer: {
                            z: 100
                        }
                    },
                ],
                yAxis: [
                    {
                        scale: true,
                        name: '用例数',
                        min: 0,
                        max: totalmax[0] + 10,
                        position: 'left',
                        offset: 12,
                        splitArea: {
                            show: true
                        },
                        nameTextStyle: {
                            color: 'rgba(153,153,153,1)',
                            fontWeight: 400,
                            fontFamily: 'PingFang-SC-Regular,PingFang-SC',
                            fontSize: 12,
                            lineHeight: 17,
                            padding: [0, 0, 0, -35],
                        }
                    },
                    {
                        scale: true,
                        name: '成功率',
                        position: 'right',
                        splitNumber: 2,
                        axisLabel: {show: true, formatter: '{value}%'},
                        axisLine: {show: true},
                        axisTick: {show: false},
                        splitLine: {show: false},
                        offset: 15,
                        min: 0,
                        max: 100,
                        axisPointer: {
                            label: {
                                show: false
                            }
                        },
                        nameTextStyle: {
                            color: 'rgba(153,153,153,1)',
                            fontWeight: 400,
                            fontFamily: 'PingFang-SC-Regular,PingFang-SC',
                            fontSize: 12,
                            lineHeight: 17,
                            padding: [0, 0, 0, 44],
                        }
                    },
                ],

                series: [
                    {
                        name: '成功数',
                        type: 'line',
                        data: success,
                        symbol: 'none',
                        smooth: true,
                        lineStyle: {
                            normal: {color: 'rgba(0,151,136,1)', width: 3}
                        },
                        itemStyle: {
                            normal: {
                                color: 'rgba(0,151,136,1)',
                            }
                        },
                    },
                    {
                        name: '失败数',
                        type: 'line',
                        symbol: 'none',
                        data: fail,
                        smooth: true,
                        lineStyle: {
                            normal: {color: 'rgba(105,208,242,1)', width: 3}
                        },
                        itemStyle: {
                            normal: {
                                color: 'rgba(105,208,242,1)',
                            }
                        },
                    },
                    {
                        name: '跳过数',
                        type: 'line',
                        symbol: 'none',
                        data: skip,
                        smooth: true,
                        lineStyle: {
                            normal: {color: 'rgba(184,223,125,1)', width: 3}
                        },
                        itemStyle: {
                            normal: {
                                color: 'rgba(184,223,125,1)',
                            }
                        },
                    },
                    {
                        name: '错误数',
                        type: 'line',
                        symbol: 'none',
                        data: error,
                        smooth: true,
                        lineStyle: {
                            normal: {color: 'rgb(255,56,55)', width: 3}
                        },
                        itemStyle: {
                            normal: {
                                color: 'rgb(255,56,55)',
                            }
                        },
                    },
                    {
                        name: '成功率',
                        stack: '总量',
                        type: 'bar',
                        label: {
                            normal: {
                                show: false,
                                position: 'top',
                                color: 'black'
                            }
                        },
                        itemStyle: {
                            normal: {
                                color: {
                                    type: 'linear',
                                    x: 0,
                                    y: 0,
                                    x2: 0,
                                    y2: 1,
                                    colorStops: [{
                                        offset: 1, color: 'rgba(255,255,255,1)' // 0% 处的颜色
                                    }, {
                                        offset: 0, color: 'rgba(239,239,239,1)' // 100% 处的颜色
                                    }],
                                    global: false // 缺省为 false
                                },
                                borderRadius: '2px'
                            }
                        },
                        areaStyle: {},
                        yAxisIndex: 1,
                        barWidth: 30,
                        data: success_rate
                    },
                    {
                        type: 'bar',
                        axisPointer: {show: false},
                        stack: '总量',
                        itemStyle: {
                            normal: {
                                color: 'rgba(201,155,237,0)',
                            }
                        },
                        yAxisIndex: 1,
                        data: hundred,
                        barWidth: 30,
                    },
                ]
            };
            $("#echarts-records").css('background-color', 'white')
            return optionRecords;
        },
        jacocoRepConfig(rate, covered, missed, total) {
            option = {
                legend: {
                    orient: 'vertical',
                    right: 0,
                    top: 'center',
                    data: [rate + '%'],
                    formatter: function (name) {
                        return '覆盖率：' + rate + '%' + '\n\n覆盖数：' + covered + '\n\n缺失数：' + missed + '\n\n总数：' + total;
                    },
                    icon: 'none',
                    selectedMode: false,
                    textStyle: {
                        fontSize: 12,
                        fontWeight: 400,
                        color: 'rgba(51,51,51,1)',
                    }
                },
                series: [
                    {
                        color: ['rgba(77,201,122,1)', 'rgba(242,242,242,1)'],
                        type: 'pie',
                        radius: ['85%', '95%'],
                        center: ["32%", "50%"],
                        hoverAnimation: false,
                        label: {
                            normal: {
                                show: true,
                                position: 'center',
                                textStyle: {
                                    fontSize: '16',
                                    fontFamily: 'PingFang-SC-Medium,PingFang-SC',
                                    fontWeight: '500',
                                    color: 'rgba(51,51,51,1)'
                                },
                            },
                        },
                        data: [
                            {value: rate, name: rate + '%'},
                            {value: 100 - rate}
                        ]
                    }
                ]
            };
            return option
        },
        queryOldBug(taskid) {
            var that = this;
            layui.use('table', function () {
                layui.table.render({
                    elem: '#oldbugtable',
                    method: 'POST',
                    page: true,
                    limit: 10,
                    height: 'full-170',
                    url: '/homepage/buglog/', //数据接口,
                    where: {
                        time: that.historytime[0] + ';' + that.historytime[1],
                        planid: that.form.plan,
                        taskid: taskid
                    },
                    cols: [[ //表头
                        {field: '路径', title: '用例-步骤', width: "25%", align: "left"}
                        , {field: '接口', title: '接口', width: "40%", align: "left"}
                        , {field: '测试点', title: '测试点', width: "13%", align: "left"}
                        , {field: '参数信息', title: '参数信息', width: "15%", align: "left"}
                        , {field: '失败原因', title: '失败原因', width: "15%", align: "left"}
                        , {field: '任务id', title: '任务id', width: "25%", align: "left"}
                    ]],
                    text: {
                        none: '该期间无缺陷记录！'
                    }
                });
            })
        },
        downloadReport() {
            var that = this;
            planid = that.form.plan.substr(5);
            if (planid == '') {
                this.$message({
                    message: '请选择项目和计划',
                    type: 'error', center: true
                });
            } else {
                _post_nl('/homepage/querytaskid/', {'planid': planid, 'action': 'plan'}, function (data) {
                    var res = JSON.parse(data);
                    if (res.code == 0) {
                        const req = new XMLHttpRequest();
                        req.open('POST', '/homepage/downloadReport/', true);
                        req.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                        req.responseType = 'blob';
                        req.send("taskid=" + res.data); //输入参数
                        req.onload = function () {
                            console.log(this.response.size)
                            if (this.status === 200 & this.response.size > 20) {
                                const data = req.response;
                                const blob = new Blob([data]);
                                var a = document.createElement('a');
                                a.download = '报告_' + res.data + '.html';
                                a.href = window.URL.createObjectURL(blob);
                                a.click();
                            } else {
                                layer.msg("没有找到报告记录")
                            }
                        };
                    } else layer.msg(res.msg)
                })
            }
        },
        downloadRunlog() {
            var that = this;
            _post_nl('/homepage/querytaskid/', {'planid': that.form.plan.substr(5), 'action': 'plan'}, function (data) {
                var res = JSON.parse(data);
                if (res.code == 0) {
                    const req = new XMLHttpRequest();
                    req.open('POST', '/homepage/downloadlog/', true);
                    req.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                    req.responseType = 'blob';
                    req.send("taskid=" + res.data); //输入参数
                    req.onload = function () {
                        console.log(this.response.size)
                        if (this.status === 200 & this.response.size > 20) {
                            const data = req.response;
                            const blob = new Blob([data]);
                            var a = document.createElement('a');
                            a.download = '日志_' + res.data + '.html';
                            a.href = window.URL.createObjectURL(blob);
                            a.click();
                        } else {
                            layer.msg("没有找到运行日志")
                        }
                    };
                } else layer.msg(res.msg)
            })
        },
        planStatereFlash() {
            var that = this;
            var id = that.form.forceStopPlans
            _post_nl('/homepage/queryPlanState/', {id: id}, function (data) {
                that.runningState = data.data == 1 ? '运行' : '未运行'
            })
        },
        forceStop() {
            var that = this;
            _post_nl('/homepage/planforceStop/', {id: that.form.forceStopPlans}, function (data) {
                if (data.code == 0) {
                    that.planStatereFlash()
                }
            });
        },
        copyUrl(obj) {
            let oInput = document.createElement('input');
            oInput.value = obj;
            document.body.appendChild(oInput);
            oInput.select(); // 选择对象;
            document.execCommand("Copy"); // 执行浏览器复制命令
            this.$message({
                message: '已成功复制到剪切板',
                type: 'success'
            });
            oInput.remove()
        },
        jacocoReFlash(s) {
            var that = this;
            productid = that.form.product;
            jobname = that.form.service
            if (productid != '' & jobname != '') {
                that.synchronize = '获取中';
                _post_nl('/homepage/jacocoreport/', {
                    productid: productid,
                    jobname: jobname,
                    s: s
                }, function (data) {
                    data = JSON.parse(data);
                    if (data.code == 0) {
                        coverlist.forEach(function (item, index) {
                            rate = data.data[item]['percentageFloat'] != '' ? (data.data[item]['percentageFloat']).toFixed(2) : 0
                            covered = data.data[item]['covered']
                            missed = data.data[item]['missed']
                            total = data.data[item]['total']
                            actjacoco[index].resize()
                            actjacoco[index].setOption(that.jacocoRepConfig(rate, covered, missed, total));
                        });
                    } else if (data.code == 1) {
                        that.$notify({
                            title: '获取结果',
                            message: data.msg,
                            type: 'warning',
                            dangerouslyUseHTMLString: true,
                            duration: 1000,
                            position: 'bottom-left'
                        });
                    } else {
                        coverlist.forEach(function (item, index) {
                            actjacoco[index].resize()
                            actjacoco[index].setOption(that.jacocoRepConfig(0, 0, 0, 0));
                        });
                    }
                    that.synchronize = '获取'
                })
            } else return
        },
        serviceChange(curdata) {
            if (curdata.indexOf(0) != -1) {
                if (curdata[curdata.length - 1] == 0) {
                    this.form.service = [0]
                } else {
                    curdata.splice(curdata.indexOf(0), 1)
                    this.form.service = curdata
                }
            } else if (curdata[0] == 0) {
                this.form.service = curdata.shift()
            }
            this.jacocoReFlash('get')
        },
        getReportChart() {
            var that = this;
            _post_nl('/homepage/reportchart/', {planid: that.form.plan.substr(5)}, function (result) {
                result = JSON.parse(result);
                echartsRecords.resize();
                echartsRecords.setOption(that.reportconfig(result.data, result.code));
            });
        },
        reportChartCilck(obj) {
            if (obj.$el.id == 'pane-0') {
                this.getReportChart()
            } else if (obj.$el.id == 'pane-1') {
                coverlist.forEach(function (item, index) {
                    setTimeout(() => actjacoco[index].resize(), -1)
                });
            }
        },
        selectPlanVisible(obj) {
            if (!obj && this.form.plan != '') {
                this.getReportChart()
            }
        },
        jacocoRun() {
            var that = this;
            _post_nl('/homepage/runforJacoco/', {
                'productid': that.form.product,
            }, function (data) {
                layer.msg(data.data)
            })
        },
        getproductReport(rate, total) {
            var that = this;
            that.productRatenum = '共运行通过率:<br><p style="font-weight:bold">' + rate + "%</p>";
            that.productCountnum = '共运行次数:<br><p style="font-weight:bold">' + total + "</p>";
            option0 = {
                color: ['rgba(253,174,57,1)'],
                legend: {
                    left: '45%',
                    top: 'center',
                    orient: 'vertical',
                    data: [total + ''],
                    formatter: function (total) {
                        let arr = [
                            '{a|' + '项目共运行次数:' + '}',
                            '{b|' + total + '次}'
                        ]
                        return arr.join('\n')
                    },
                    textStyle: {
                        color: '#FBFBFB',
                        fontSize: 16,
                        rich: {
                            a: {
                                color: 'rgba(102,102,102,1)',
                                fontSize: 12,
                                fontWeight: 500,
                                lineHeight: 43,
                                fontFamily: 'PingFang-SC-Medium,PingFang-SC',
                            },
                            b: {
                                color: 'rgba(51,51,51,1)',
                                fontSize: 16,
                                fontWeight: 500,
                                fontFamily: 'PingFang-SC-Medium,PingFang-SC',
                            },
                        },
                    },
                    icon: 'none',
                    selectedMode: false,
                },
                series: [
                    {
                        type: 'pie',
                        radius: ['85%', '95%'],
                        center: ["25%", "53%"],
                        hoverAnimation: false,
                        label: {
                            normal: {
                                show: true,
                                position: 'center',
                                textStyle: {
                                    fontSize: '22',
                                    fontWeight: '500',
                                    color: 'rgba(51,51,51,1)'
                                },
                            },
                        },
                        data: [
                            {value: total, name: total + ''}
                        ]
                    }
                ]
            };
            option1 = {
                color: ['rgba(77,201,122,1)', 'rgba(242,242,242,1)'],
                legend: {
                    orient: 'vertical',
                    left: '45%',
                    top: 'center',
                    data: [rate + '%'],
                    formatter: function (name) {
                        let arr = [
                            '{a|' + '项目整体成功率:' + '}',
                            '{b|' + name + '}'
                        ]
                        return arr.join('\n')
                    },
                    icon: 'none',
                    selectedMode: false,
                    textStyle: {
                        color: '#FBFBFB',
                        fontSize: 16,
                        rich: {
                            a: {
                                color: 'rgba(102,102,102,1)',
                                fontSize: 12,
                                fontWeight: 500,
                                lineHeight: 43,
                                fontFamily: 'PingFang-SC-Medium,PingFang-SC',
                            },
                            b: {
                                color: 'rgba(51,51,51,1)',
                                fontSize: 16,
                                fontWeight: 500,
                                fontFamily: 'PingFang-SC-Medium,PingFang-SC',
                            },
                        },
                    },
                },
                series: [
                    {
                        type: 'pie',
                        radius: ['85%', '95%'],
                        center: ["25%", "53%"],
                        hoverAnimation: false,
                        label: {
                            normal: {
                                show: true,
                                position: 'center',
                                textStyle: {
                                    fontSize: '22',
                                    fontWeight: '500',
                                    color: 'rgba(51,51,51,1)'
                                },
                            },
                        },
                        data: [
                            {value: rate, name: rate + '%'},
                            {value: 100 - rate}
                        ]
                    }
                ]
            };
            actproduct[0].resize();
            actproduct[0].setOption(option0);
            actproduct[1].resize();
            actproduct[1].setOption(option1);
        },
        statisticalAnalysis() {
            var that = this;
            planid = that.form.plan.substr(5)
            if (planid == '') {
                this.$message({
                    message: '请选择项目和计划',
                    type: 'error', center: true
                });
            } else {
                var analysisurl = '/homepage/statisticalAnalysis/?plan=' + planid
                // window.open(analysisurl)
                layer.open({
                    type: 2,
                    title: false,
                    shade: [0],
                    area: ['90%', '90%'],
                    anim: 2,
                    shadeClose: true,
                    content: [analysisurl, 'yes'], //iframe的url，no代表不显示滚动条
                });
            }
        }
    },
    created: function () {
        apphight = document.documentElement.clientHeight;
        footheight = apphight * 0.81 - 94;
        $("#app").css('height', apphight + 'px');
        $("#foot").css('height', footheight + 'px');
        this.getproduct();
    },
    watch: {
        'form.forceStopPlans': function (id) {
            var that = this;
            that.planStatereFlash()
        },
        'form.third_plan': function (id) {
            var that = this;
            _post_nl('/homepage/query_third_call/', {
                planid: id.substr(5),
                dbscheme: that.form.third_dbschemes
            }, function (data) {
                that.form.is_verify_url = data.is_verify_url;
                that.form.debug_url = data.debug_url
            })
        },
        'form.third_dbschemes': function (name) {
            var that = this;
            _post_nl('/homepage/query_third_call/', {
                planid: that.form.third_plan.substr(5),
                dbscheme: name
            }, function (data) {
                that.form.is_verify_url = data.is_verify_url;
                that.form.debug_url = data.debug_url
            })
        },
        'log_text': function () {
            setTimeout(function () {
                //设置滚动条到最底部
                document.getElementById('log-process').scrollTop = document.getElementById('log-process').scrollHeight;
            }, 100);
        },
    },
});
echartsRecords = echarts.init(document.getElementById('echarts-records'), 'me2');
coverlist = ['branchCoverage', 'classCoverage', 'instructionCoverage', 'complexityScore', 'lineCoverage', 'methodCoverage']
actjacoco = [];
coverlist.forEach(function (item, index) {
    actjacoco[index] = echarts.init(document.getElementById(item), 'me2');
    actjacoco[index].resize()
    actjacoco[index].setOption(app.jacocoRepConfig(0, 0, 0, 0))
});
window.onresize = function () {
    homesize();
    echartsRecords.resize();
};

productPiclist = ['productCount', 'productRate'];
actproduct = []
productPiclist.forEach(function (item, index) {
    actproduct[index] = echarts.init(document.getElementById(item), 'me2');
});

function ArraytoString(input) {
    let r = "";
    input.forEach(function (e) {
        r += " " + e;
    });
    return r.substr(1);
}

echartsRecords.on('click', function (params) {
    if (success_rate[params.dataIndex] !== 100) {
        taskid = taskids[params.dataIndex];
        app.queryOldBug(taskid);
        app.planHistoryVisible = true;
    } else {
        app.$message({
            message: '该次执行全部通过',
            type: 'success', center: true
        });
    }
});

window.onload = function () {
    homesize();
};

function homesize() {
    apphight = document.documentElement.clientHeight;
    footheight = apphight * 0.81 - 94;
    $("#app").css('height', apphight + 'px');
    $("#foot").css('height', footheight + 'px');
    actproduct[0].resize();
    actproduct[1].resize();
    coverlist.forEach(function (item, index) {
        actjacoco[index].resize()
    });

}