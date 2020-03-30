#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-30 15:07:14
# @Author  : Blackstone
# @to      :
import os

from channels.generic.websocket import WebsocketConsumer
import json, threading, time
import redis
from django.conf import settings
class ChatConsumer(WebsocketConsumer):
	
	def sendmsg(self):
		while True:
			# print('check.')
			time.sleep(0.1)
			t = self.con.rpop('list')
			if t is not None:
				print(t.decode())
				self.send(text_data=t.decode())
	
	def connect(self):
		# 连接时触发
		self.accept()
		self.con = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
		print('收到一个websocket连接.')
		threading.Thread(target=self.sendmsg).start()
	
	def disconnect(self, code):
		# 关闭连接时触发
		pass
	
	def receive(self, text_data=None, bytes_data=None):
		# 收到消息后触发
		pass


class ConsoleConsumer(WebsocketConsumer):
	# console展现过
	__handled = []
	
	def __init__(self, args):
		super(ConsoleConsumer, self).__init__(args)
		self._flag = False
		self._next = False
	
	def terminate(self):
		self._flag = True
	
	def next(self):
		self._next = True
	
	def reset(self):
		try:
			self._flag = False
			if self.username:
				del self.username
			if self.taskid:
				del self.taskid
		except:
			pass

	
	def sendmsg(self, username, taskid):
		# msg = ""
		# self.keys = self.con.keys("console.msg::%s::%s" % (username, taskid))
		# print("查询到的任务id(%s)=>%s" % (len(self.keys), self.keys))
		# if self.keys:
		# 	key = self.keys[0]
		# 	while True:
		# 		if self._flag == True:
		# 			print('=' * 40)
		# 			print("================结束向用户[%s]控制台发送消息===============" % username)
		# 			print('=' * 40)
		# 			break
		# 		sep = self.con.rpop(key)
		# 		if sep is not None and "任务【<span style='color" in sep:
		# 			self.send(sep)
		# 			while True:
		# 				time.sleep(0.05)
		# 				if self._flag == True:
		# 					break
		# 				if self._next == True:
		# 					self._next = False
		# 					break;
		# 				sep = self.con.rpop(key)
		# 				if sep is not None:
		# 					self.send(sep)
		# 		else:
		# 			self.send("hasRead")
		# 			break
		# else:
		# 	self.send("hasRead")
	
		msg=""
		print(ConsoleConsumer.__handled)
		self.keys=[x for x in self.con.keys("console.msg::%s*"%username) if x not in ConsoleConsumer.__handled]
		self.keys.sort()
		#self.send("[key-value]"+",".join(self.keys))
		print("查询到的任务id(%s)=>%s"%(len(self.keys),self.keys))
		while True:
			if self._flag==True:
				print('='*40)
				print("================结束向用户[%s]控制台发送消息==============="%username)
				print('='*40)
				break
			for key in self.keys:
				if self._flag==True:
					break
				while True:
					time.sleep(0.05)
					if self._flag==True:
						break
					if self._next==True:
						self._next=False
						break;
					sep=self.con.rpop(key)
					if sep is not None:
						self.send(sep)
	

	def connect(self):
		# 连接时触发
		self.accept()
		pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)
		self.con = redis.Redis(connection_pool=pool)
	
	# print("connect=>",self.con)
	# print('consolemsg 连接.=>',self.con.keys("console.msg::%s*"%self.username))
	
	def disconnect(self, code):
		# 关闭连接时触发
		print("用户[%s]关闭console 结束会话" % self.username)
		ConsoleConsumer.__handled = ConsoleConsumer.__handled + self.keys
		print("当前过滤key值=>", ConsoleConsumer.__handled)
		self.terminate()
	
	def receive(self, text_data=None, bytes_data=None):
		# 收到消息后触发
		# self.username=text_data
		
		if text_data.startswith("console.msg::read"):
			self.reset()
			get = text_data.split("::")
			self.username = get[2]
			self.taskid = get[3]
			print("receive=>", self.username, self.taskid)
			
			self.thread = threading.Thread(target=self.sendmsg, args=(self.username, self.taskid))
			self.thread.setDaemon(True)
			self.thread.start()
		
		if text_data.startswith("console.msg::next"):
			self.next()


class logConsumer(WebsocketConsumer):
	def __init__(self, args):
		super(logConsumer, self).__init__(args)
	
	def sendmsg(self, taskid, is_running):
		logname = "./logs/" + taskid + ".log"
		done_msg = '结束计划'
		if os.path.exists(logname):
			with open(logname, 'r', encoding='utf-8') as f:
				if is_running in (0, '0'):
					log_text = f.readlines()
					count = len(log_text)
					self.send(text_data=json.dumps({'data': log_text, 'count': count}))
					self.disconnect()
				else:
					while True:
						log_text = f.readlines()
						count = len(log_text)
						self.send(text_data=json.dumps({'data': log_text, 'count': count}))
						for i in log_text:
							if done_msg in i:
								return
						time.sleep(0.1)
	
	def receive(self, text_data):
		self.is_running = text_data.split("::")[0]
		self.taskid = text_data.split("::")[1]
		print("receive=>", self.taskid)
		print("receive=>", self.is_running)
		self.thread = threading.Thread(target=self.sendmsg, args=(self.taskid, self.is_running))
		self.thread.setDaemon(True)
		self.thread.start()
	
	def disconnect(self, code=None):
		print("%s 的日志打印结束" % self.taskid)
