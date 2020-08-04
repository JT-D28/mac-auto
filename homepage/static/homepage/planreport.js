var app = new Vue({
    el: '#app',
    delimiters: ['${', '}'],
    data() {
        var vue = this;
        return {
            currentRunNum: '',
            lastRunNum: '',
            currentPassRate: '',
            lastPassRate: '',
            currentBusinessNum: '',
            currentRunBusiness: '',
            querytime: '',
            jenkinsUpdatetimes: '',
            coverytime: '',
            coverydata: {},
            oldcoverytime: '',
            options: [{
                value: '选项1',
                label: '黄金糕'
            }, {
                value: '选项2',
                label: '双皮奶'
            }, {
                value: '选项3',
                label: '蚵仔煎'
            }, {
                value: '选项4',
                label: '龙须面'
            }, {
                value: '选项5',
                label: '北京烤鸭'
            }],
            planid: [],
            product: '',
            oldcoverydata: {},
            pickerOptions: {
                shortcuts: [{
                    text: '今天',
                    onClick(picker) {
                        const endtime = new Date(new Date(new Date().getTime()).setHours(23, 59, 59, 999))
                        const start = app.setStartData(1);
                        picker.$emit('pick', [start, endtime]);
                    }
                }, {
                    text: '最近3天',
                    onClick(picker) {
                        const endtime = new Date(new Date(new Date().getTime()).setHours(23, 59, 59, 999))
                        const start = app.setStartData(3);
                        picker.$emit('pick', [start, endtime]);
                    }
                }, {
                    text: '最近7天',
                    onClick(picker) {
                        const endtime = new Date(new Date(new Date().getTime()).setHours(23, 59, 59, 999))
                        const start = app.setStartData(7);
                        picker.$emit('pick', [start, endtime]);
                    }
                }, {
                    text: '最近30天',
                    onClick(picker) {
                        const endtime = new Date(new Date(new Date().getTime()).setHours(23, 59, 59, 999))
                        const start = app.setStartData(30);
                        picker.$emit('pick', [start, endtime]);
                    }
                }, {
                    text: '最近90天',
                    onClick(picker) {
                        const endtime = new Date(new Date(new Date().getTime()).setHours(23, 59, 59, 999))
                        const start = app.setStartData(90);
                        picker.$emit('pick', [start, endtime]);
                    }
                }],
                // disabledDate(time) {
                //     return time.getTime() > Date.now();
                // }, onPick(time) {
                //     if (time.minDate && !time.maxDate) {
                //         vue.timeOptionRange = time.minDate;
                //     }
                //     if (time.maxDate) {
                //         vue.timeOptionRange = null;
                //     }
                // }
            },
            products: [],
            plans: [],
            jacocoVisible: false,
            gitCommits: [],
            runtimes: ''
        }
    },
    methods: {
        setStartData(num) {
            return new Date(new Date(new Date().getTime() - 24 * 60 * 60 * 1000 * (num - 1)).setHours(0, 0, 0, 0));
        },
        getproduct() {
            var that = this;
            _post_nl('/homepage/queryproduct/', {}, function (data) {
                var data = JSON.parse(data);
                that.products = data.data
            })
        },
        selectProduct() {
            var that = this;
            this.planid = [];
            _post_nl('/homepage/queryplanlist/', {id: this.product}, function (data) {
                that.plans = data.data;
                that.query()
            })
        },
        selectPlanVisible(obj) {
            if (!obj && this.planid.length != 0) {
                // this.query()
            }
        },
        query() {
            var that = this;
            var starttime = this.querytime[0].toString().substr(0, 10)
            var endtime = this.querytime[1].toString().substr(0, 10)
            var productid = this.product

            _post_nl('/homepage/HasJacoco/', {
                'productid': productid
            }, function (data) {
                if (data.has == 1) {
                    that.jacocoVisible = true
                    that.queryCoveryInfo(productid)
                } else {
                    that.jacocoVisible = false
                }
            })

            _post_nl('/homepage/queryGitCommit/', {
                    'productid': productid,
                    'starttime': starttime,
                    'endtime': endtime
                }, function (data) {
                    that.gitCommits = data.data
                }
            )
            _post_nl('/homepage/queryJenkinsUpdatetimes/', {
                    'productid': productid,
                    'starttime': starttime,
                    'endtime': endtime
                }, function (data) {
                    that.jenkinsUpdatetimes = data.data
                }
            )

            // _post_nl('/homepage/planBusinessNum/', {
            //     'id': that.plan,
            // }, function (data) {
            //     that.currentBusinessNum = data.currentBusinessNum
            //     that.currentRunBusiness = data.currentRunBusiness
            // })
        },
        queryCoveryInfo(productid) {
            var that = this
            _post_nl('/homepage/queryCoveryInfo/', {'productid': productid}, function (data) {
                that.coverytime = data.time
                that.coverydata = data.res
                that.oldcoverytime = data.oldtime
                that.oldcoverydata = data.lastres
            })
        },

    },
    created: function () {
        this.getproduct();
        this.querytime = [new Date(new Date().getTime()).setHours(0, 0, 0, 0),
            new Date(new Date().getTime()).setHours(23, 59, 59, 999)]
    },
    watch: {},
});
