#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-10-25 17:48:51
# @Author  : Blackstone
# @to      :

import sys, qtawesome
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import QWebEngineView


################################################
#######创建主窗口
################################################
class MainWindow(QMainWindow):
	'''
	fadfddaf
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setWindowTitle('My Browser')
		self.showMaximized()
		
		self.webview = WebEngineView()
		self.webview.load(QUrl("https://www.baidu.com"))
		self.setCentralWidget(self.webview)


################################################
#######创建浏览器
################################################
class WebEngineView(QWebEngineView):
	'''

	'''
	windowList = []
	
	# 重写createwindow()
	def createWindow(self, QWebEnginePage_WebWindowType):
		new_webview = WebEngineView()
		new_window = MainWindow()
		new_window.setCentralWidget(new_webview)
		# new_window.show()
		self.windowList.append(new_window)  # 注：没有这句会崩溃！！！
		return new_webview


################################################
#######程序入门
################################################
if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setWindowIcon(qtawesome.icon("fa.ils", color="red"))
	w = MainWindow()
	w.show()
	sys.exit(app.exec_())
