#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-09-11 10:29:52
# @Author  : Blackstone
# @to      :


import winreg


def connect_proxy():
	"""
	5s delay
	"""
	key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",access=983103) 

	print(winreg.QueryValue(key,'ProxyEnable'))
	print(winreg.QueryValue(key,'ProxyServer'))

	#winreg.SetValue(key, 'ProxyEnable', winreg.REG_SZ, '1')
	winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
	winreg.SetValue(key, 'ProxyServer', winreg.REG_SZ, '127.0.0.1:8888')



def disconnect_proxy():
	key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",access=983103) 
	winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, 0)





#connect_proxy()
disconnect_proxy()

#print(eval('0xF003F'))