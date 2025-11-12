from itertools import dropwhile
from signal import Handlers
from selenium import webdriver
from Selenium.webdriver.sipport.wait import WebDriverWait
# # 加载驱动
# driver_path = ""
# driver = webdriver.Chrome(executable_path="driver_path")
# 隐式等待
driver.implicitly_wait(10)
#显性等待
WebDriverWait(driver,"等待时间 ").until("判断条件","错误提示")
# 窗口最大化
driver.maximize_window()
url = "https://www.baidu.com"
driver.get(url)
# 多窗口打开
handlers = driver.window_handles # 获取所有窗口句柄
Handler = driver.cuurrent_window_handle # 获取当前窗口句柄
# 窗口切换
driver.switch_to.window(handlers[1]) # 切换到第二个窗口
driver.switch_to.window(handlers[0]) # 切换到第一个窗口
driver.switch_to.window(Handler) # 切换到当前窗口
# 窗口关闭
driver.close() # 关闭当前窗口
driver.quit() # 关闭所有窗口
# 元素定位
# 1.id定位
id_find = driver.find_element_by_id("id")
# 2.name定位定位
name_find = driver.find_element_by_name("name")
# 3.class_name定位
class_name_find = driver.find_element_by_class_name("class_name")
# 4.tag_name定位
tag_name_find = driver.find_element_by_tag_name("tag_name")
# 5.link_text定位(需find完整的标签内容)
link_text_find = driver.find_element_by_link_text("link_text")
# 6.partial_link_text定位(需find部分的标签内容)
partial_link_text = driver.find_element_by_partial_link_text("partial_link_text")
# 7.xpath定位
xpath_find = driver.find_element_by_xpath("路径")
# 8.css定位
css_selector_find = driver.find_element_by_css_selector("tag_name")
# 元素常用操作方法
# clear() 清除文本
# send_keys() 模拟输入
# click() 单击元素

# 鼠标操作 import ActionChains
# action = ActionChains(driver)
# action.xxx.perform()

# 下拉框操作  import select  所有options标签都存在selelct.options列表里
# select_by_index()
# select_by_value()
# select_by_visible_text()

# 警告框处理 alert confirm pormpt
# 切换到警告弹窗
alter = driver.switch_to.alert
# 警告框处理方法 text返回文字信息 accept()接受对话框选项 dismiss()取消对话框选项

# frame表单切换、多窗口切换
# driver.switch_to.frame()
# driver.switch_to.default_content() 返回默认页面
# driver.switch_to.parent_frame() 返回父级
# driver.current_window_handle 获取当前窗口句柄
# driver.window_handles 获取所有窗口句柄
# driver.switch_to.window(handle) 切换指定句柄窗口

# 窗口截图 验证吗处理
# driver.get_screenshot_as_file(imgpath)
driver.quit()

# # unittest
# import unittest
#
# class TestCase(unittest.TestCase):
#     # 在每条用例执行前执行
#     def setUp(self):
#         pass
#
#     # 在每条用例执行后执行
#     def tearDown(self):
#         pass
#
#     def testcase1(self):
#         # 断言 判断预期结果是否正确
#         try:
#             self.assertEqual()
#         except AttributeError as e:
#             print("报错信息", e)
#             raise
#
#     def testcase2(self):
#         pass
#
# # 执行测试用例方法
# # suite
# suite = unittest.TestSuite()
# # 以测试用例类里的每一个方法为单位添加
# suite.addTest(TestCase("testcase1"))
# # 以测试用例类为单位添加
# suite.addTest(unittest.makeSuite(TestCase))
#
# runner = unittest.TextTestRunner()
# runner.run(suite)
#
# discover = unittest.defaultTestLoader.discover("指定的目录", pattern="查找的文件格式")
# runner = unittest.TextTestRunner()
# runner.run(discover)
#
# # 生成测试报告 引用第三方包 HTMLTestRunner
# with open("", "") as f:
#     x = HTMLTestRunner(stream=f, title="测试报告", description="描述")
#     x.run(discover)