*frame:浏览器驱动脚本，日志打印设置脚本

*elementFactory:各种类型元素定位方法封装

*elementpath:页面元素对象，定位

*page:页面元素操作对象

*testsuites:业务逻辑测试用例

*testConfig:配置文件，运行的浏览器，URL等....

*caseExecute:测试用例执行文件.xml，testng.xml和build.xml

*test-output:测试报告存放

*testUtil:测试工具集成，excel，reportNG，Email等



# 文件命名规则
1. page
按页面路径命名
* 例：开工单页面
http://47.99.184.154:5880/launa/web/workOrder/woManage

包名为 launa.web.workOrder
文件名为 woManagePage

# Chrome Driver 下载地址
http://npm.taobao.org/mirrors/chromedriver
http://chromedriver.storage.googleapis.com/index.html

# 后缀为flow的方法定义规范
参数： webdriver + 实体类