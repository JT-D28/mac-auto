layui.config({
    base: '/static/homepage/layui/modules/'      //自定义layui组件的目录
}).extend({                             //设定组件别名
    common: 'common',
    echarts: 'echarts/echarts', // echarts图表扩展
    echartsTheme: 'echarts/echartsTheme', // echarts图表主题扩展
});
