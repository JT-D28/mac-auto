#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-03-21 13:35:17
# @Author  : Blackstone
# @to      :报文结果校验 支持链式解析 列表项定位 如rows[0].text=xx

import json


class ResultChecker(object):
	
	def __init__(self, datastr, expectedresult=None, type="json"):
		self.datastr = datastr
		self.expectedresult = expectedresult
		self.type = type
	
	def check_all(self):
		kvs = self.expectedresult.split("|")
		for kv in kvs:
			k = kv.split("=")[0]
			v = kv.split("=")[1]
			
			if v == "true":
				v = "True"
			
			elif v == 'false':
				v = "False"
			
			if not self.check(k, v):
				print("匹配不一致=>期望:", k, v)
				return "error"
		
		return "pass"
	
	def check(self, chainstr, expected):
		p = None
		
		if self.type == "json":
			p = JSONParser(self.datastr)
			return p.check(chainstr, expected)
		
		else:
			raise NotImplementedError("XMLParser 链式识别没实现.")


class Struct(object):
	
	def __init__(self, data):
		self.datastr = str(data)
	
	def getValue(self, xpath):
		raise NotImplementedError("")
	
	def translate(self, chainstr):
		raise NotImplementedError("")


class XMLParser(Struct):
	
	def getValue(self, xpath):
		return ""


class JSONParser(Struct):
	
	def __init__(self, data):
		# print("88"*200)
		# print(data)
		data = data.replace("\'", "\"").replace("None", "null").replace("True", "true")
		# print(data)
		
		# self.obj=json.loads(data)
		
		self.obj = eval(self._apply_filter(data))
		
		print("待匹配数据=>", self.obj)
	
	def _apply_filter(self, msg):
		# print("leix=",type(msg))
		msg = msg.replace("true", "True").replace("false", "False").replace("null", "None")
		return msg
	
	def translate(self, chainstr):
		stages = chainstr.split(".")
		
		return "self.obj." + ".".join(
			["get('%s')[%s" % (stage.split("[")[0], stage.split("[")[1]) if "[" in stage else "get('%s')" % stage for
			 stage in stages])
	
	def getValue(self, chainstr):
		xpath = self.translate(chainstr)
		# print("tr=>"+xpath)
		r = eval(xpath)
		
		# print("type=>",type(r))
		
		return r
	
	def check(self, chainstr, expected):
		# print(type(self.getValue(chainstr)),type(expected))
		
		return str(self.getValue(chainstr)) == str(expected)


if __name__ == "__main__":
	data = '{\
    "code": "0",\
    "info": "操作成功！",\
    "value": "",\
    "success": true,\
    "data": null,\
    "rows": [\
        {\
            "text": "AS330106",\
            "value": "349c8247e4004783845aac95494efc18"\
        },\
        {\
            "text": "QT330001",\
            "value": "0d28d8b39357496a954df66297491047"\
        }\
    ],\
    "total": 2\
}'
	
	p = JSONParser(data)
	
	print(p.getValue("code"))
	print(p.getValue("success"))
	print(p.getValue("rows[1].text"))
