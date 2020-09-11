var app = new Vue({
    el: '#app',
    delimiters: ['${', '}'],
    data() {
        var vue = this;
        return {
            querytime: '',
            jenkinsUpdatetimes: '',
            coverytime: '',
            coverydata: {},
            jobcovertimes: '',
            oldcoverytime: '',
            plansCheckBox: [],
            product: '',
            averageTimeSpent: '',
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
            gitCommitVisible: false,
            gitCommits: [],
            runtimes: ''
        }
    },
    methods: {
        downloadImage() {
            // var that = this
            var imgName = "cs.jpg";



            // html2canvas(cloneDom[0]).then(canvas => {
            //     var dataUrl = canvas.toDataURL('image/jpeg', 1.0);
            //     dataURIToBlob(imgName, dataUrl, callback);
            //     cloneDom.empty();
            //
            //     $("#tmp_datatable").remove();
            //
            // });


            // var getPixelRatio = function (context) { // 获取设备的PixelRatio
            //     var backingStore = context.backingStorePixelRatio ||
            //         context.webkitBackingStorePixelRatio ||
            //         context.mozBackingStorePixelRatio ||
            //         context.msBackingStorePixelRatio ||
            //         context.oBackingStorePixelRatio ||
            //         context.backingStorePixelRatio || 0.5;
            //     return (window.devicePixelRatio || 0.5) / backingStore;
            // };
            // //生成的图片名称

            // var width = shareContent.offsetWidth;
            // var height = shareContent.offsetHeight;
            // var canvas = document.createElement("canvas");
            // var context = canvas.getContext('2d');
            // var scale = getPixelRatio(context); //将canvas的容器扩大PixelRatio倍，再将画布缩放，将图像放大PixelRatio倍。
            // canvas.width = width * scale;
            // canvas.height = height * scale;
            // canvas.style.width = width + 'px';
            // canvas.style.height = height + 'px';
            // context.scale(scale, scale);

            // html2canvas(shareContent, opts).then(function (canvas) {
            //     context.imageSmoothingEnabled = false;
            //     context.webkitImageSmoothingEnabled = false;
            //     context.msImageSmoothingEnabled = false;
            //     context.imageSmoothingEnabled = false;
            //     var dataUrl = canvas.toDataURL('image/jpeg', 1.0);
            //     dataURIToBlob(imgName, dataUrl, callback);
            // });
            var dataURIToBlob = function (imgName, dataURI, callback) {
                var binStr = atob(dataURI.split(',')[1]),
                    len = binStr.length,
                    arr = new Uint8Array(len);

                for (var i = 0; i < len; i++) {
                    arr[i] = binStr.charCodeAt(i);
                }
                callback(imgName, new Blob([arr]));
            }
            var callback = function (imgName, blob) {
                var triggerDownload = $("<a>").attr("href", URL.createObjectURL(blob)).attr("download", imgName).appendTo("body").on("click", function () {
                    if (navigator.msSaveBlob) {
                        return navigator.msSaveBlob(blob, imgName);
                    }
                });
                triggerDownload[0].click();
                triggerDownload.remove();
            };
        },
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
                that.gitCommitVisible = false
                that.jacocoVisible = false
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
            _post_nl('/homepage/HasGit/', {
                'productid': productid
            }, function (data) {
                if (data.hasGit == 1) {
                    that.queryGitCommits(productid, starttime, endtime)
                } else {
                    that.gitCommitVisible = false
                }
            })

            _post_nl('/homepage/queryJenkinsUpdatetimes/', {
                    'productid': productid,
                    'starttime': starttime,
                    'endtime': endtime
                }, function (data) {
                    that.jenkinsUpdatetimes = data.jenkinsUpdatetimes
                    that.jobcovertimes = data.jobcovertimes
                    that.averageTimeSpent = data.averageTimeSpent
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
        queryGitCommits(productid, starttime, endtime) {
            var that = this
            _post_nl('/homepage/queryGitCommit/', {
                    'productid': productid,
                    'starttime': starttime,
                    'endtime': endtime
                }, function (data) {
                    if (data.data.length > 0) {
                        that.gitCommits = data.data
                        that.gitCommitVisible = true
                    }
                }
            )
        }

    },
    created: function () {
        this.getproduct();
        this.querytime = [new Date(new Date().getTime()).setHours(0, 0, 0, 0),
            new Date(new Date().getTime()).setHours(23, 59, 59, 999)]
    },
    watch: {},
});
