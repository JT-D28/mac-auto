import ast
import asyncio
import json
import os
import re
import socket
import sys
import time
import traceback
from urllib import parse
import requests
from django.db.models import Q
from requests import compat
from manager.builtin import *
from manager.context import Me2Log as logger, setRunningInfo, set_top_common_config, get_space_dir
from manager.core import ordered, getbuiltin, Fu
from manager.db import Mysqloper
from manager.invoker import _get_final_run_node_id, beforePlanCases, get_node_upper_case, _replace_property, \
	XMLParser, JSONParser, _get_step_params, _legal, \
	_eval_expression
from manager.models import Plan, DBCon, Order, Case, Step, BusinessData, Function, ResultDetail, User, Variable, Tag
from manager.operate.DesktopNotification import notification
from manager.operate.apiInfo import dump_request
from manager.operate.generateReport import dealruninfo
from manager.operate.mongoUtil import Mongo
from manager.operate.redisUtils import RedisUtils
from manager.operate.sendMail import processSendReport


def getHostIp():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.connect(('1.1.1.1', 80))
		ip = s.getsockname()[0]
	finally:
		s.close()
	return ip


color_res = {
	'success': 'green',
	'fail': 'red',
	'skip': 'orange',
	'omit': 'green',
}


class RunPlan:
	
	def __init__(self, taskId, planId, runKind, user, startNodeId=None):
		self.taskId = taskId
		self.planId = planId
		self.runKind = runKind
		self.startNodeId = startNodeId
		self.plan = Plan.objects.get(id=planId)
		self.redisCon = RedisUtils()
		self.taskSession = requests.session()
		self.user = User.objects.get(name=user)
		self.tempVar = {}
	
	def log(self, msg):
		try:
			what = "%s        %s<br>" % (
				time.strftime("[%m-%d %H:%M:%S]", time.localtime()), "".join([str(x) for x in msg if x]))
			Mongo.tasklog(self.taskId).insert_one({'time': time.time(), 'info': what})
		except Exception as e:
			logger.error("运行日志记录异常")
			logger.error(traceback.format_exc())
	
	def setDbUse(self, dbname, type):
		try:
			dbId = DBCon.objects.get(scheme=self.plan.schemename, description=dbname).id
		except:
			db = DBCon.objects.filter(scheme='全局', description=dbname).first()
			dbId = db.id if db else None
		if dbId:
			logger.info('plan dbid=>', dbId)
			desp = DBCon.objects.get(id=int(dbId)).description
			set_top_common_config(self.taskId, desp, src=type)
	
	def getReady(self):
		setRunningInfo(self.planId, self.taskId, self.runKind, self.plan.schemename)
		self.log("=======计划【%s】正在初始化中,任务类型【%s】=======" % (
			self.plan.description, {"1": "验证", "2": "调试", "3": "定时"}[self.runKind]))
		self.log("在主机ip：" + getHostIp() + "上执行")
		logger.info('开始执行计划：', self.planId)
		logger.info('startnodeid:', self.startNodeId)
		self.finalNode = _get_final_run_node_id(self.startNodeId)
		logger.info('准备传入的L:', self.finalNode)
		logger.info('runkind:', self.runKind)
		
		self.startTime = time.time()
		groupskip = []
		
		self.log(
			"=======开始执行【<span style='color:#FF3399'>%s</span>】,使用数据连接配置【%s】====" % (self.taskId, self.plan.schemename))
		
		if self.plan.proxy:
			self.proxy = {'http': self.plan.proxy}
			self.log("请求代理：%s" % self.plan.proxy)
		else:
			self.proxy = {}
	
	def start(self):
		self.getReady()
		try:
			# 获取用例级别的所有节点（包括预先执行的内容）
			if self.startNodeId.split('_')[0] == 'plan':
				caseslist = []
				beforeCases, before_des = beforePlanCases(self.planId)
				caseslist.extend(ordered(list(beforeCases)))
				self.log("加入前置计划/用例[<span style='color:#FF3399'>%s</span>]" % before_des)
				caseslist.extend(
					ordered(list(Order.objects.filter(main_id=self.plan.id, kind='plan_case', isdelete=0))))
				caseIds = [x.follow_id for x in caseslist]
			else:
				caseId = get_node_upper_case(self.startNodeId)
				caseIds = [caseId]
			
			logger.info('cases=>', caseIds)
			
			# 计划级设置数据库使用
			self.setDbUse(self.plan.db_id, 'plan')
			self.plan.last, color = 'success', 'green'
			# 执行用例（第一层）
			for cid in caseIds:
				case = Case.objects.get(id=cid)
				if not self.runCase(case):
					self.plan.last, color = 'fail', 'red'
				self.plan.save()
			self.log("结束计划[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-%s'>%s</span>" % (
				self.plan.description, color, self.plan.last))
			spendTime = time.time() - self.startTime
			asyncio.set_event_loop(asyncio.new_event_loop())
			loop = asyncio.get_event_loop()
			loop.run_until_complete(
				dealruninfo(self.planId, self.taskId,
				            {'spend': spendTime, 'dbscheme': self.plan.schemename, 'planname': self.plan.description,
				             'user': self.user.name, 'runkind': self.runKind}, self.startNodeId))
		
		except Exception as e:
			logger.error('执行计划未知异常：', traceback.format_exc())
			self.log('执行计划未知异常[%s]' % traceback.format_exc())
		
		finally:
			setRunningInfo(self.planId, self.taskId, '0')
			processSendReport(self.taskId, self.plan.mail_config_id, self.user.name,spendTime)
			notification(self.user.name,
			             "计划【%s】%s任务运行结束，前往查看" % (self.plan.description, {"1": "验证", "2": "调试", "3": "定时"}[self.runKind]))
	
	def runCase(self, case):
		caseSuccess = True
		groupSkip = []
		# 获取该用例下最终执行的节点
		case_run_nodes = _get_final_run_node_id('case_%s' % case.id)
		# 设置标记
		subFlag = True if set(case_run_nodes).issubset(self.finalNode) else False
		logger.info('用例[%s]下有测试点ID：%s' % (case.description, case_run_nodes))
		if case.count in [ None,"None"]:
			case.count = 1
			case.save()
		caseCount = 0 if case.count in [0, '0', ''] else int(case.count)

		if subFlag and caseCount!=0:
			self.log("开始执行用例[<span id='case_%s' style='color:#FF3399'>%s</span>]" % (case.id, case.description))
		# 获取用例的子节点（有用例和步骤两种情况，需要按照正常顺序）
		subList = ordered(list(Order.objects.filter(Q(kind='case_step') | Q(kind='case_case'), main_id=case.id)))
		for i in range(caseCount):
			self.setDbUse(case.db_id, 'case')
		
			for subNode in subList:
				try:
					if subNode.kind == 'case_case':
						subCase = Case.objects.get(id=subNode.follow_id)
						if not self.runCase(subCase):
							caseSuccess = False
					elif subNode.kind == 'case_step':
						stepId = subNode.follow_id
						step = Step.objects.get(id=stepId)
						if step.count in [None, "None"]:
							step.count = 1
							step.save()
						stepCount = 0 if step.count in [0, '0', '', None] else int(step.count)
						for i in range(stepCount):
							self.setDbUse(case.db_id, 'step')
							if not self.runStep(step, case.id,groupSkip):
								caseSuccess = False
				except:
					print(traceback.format_exc())
					continue
		if subFlag and caseCount!=0:
			color, succss = ('green', 'success') if caseSuccess else ('red', 'fail')
			self.log("结束用例[<span style='color:#FF3399'>%s</span>] 结果<span class='layui-bg-%s'>%s</span>" % (
				case.description, color, succss))
		
		return caseSuccess
	
	def runStep(self, step, caseId,groupSkip):
		case = Case.objects.get(id=caseId)
		stepSuccessFlag = True
		num = 0
		
		subTestPoints = ordered(list(Order.objects.filter(kind='step_business', main_id=step.id, isdelete=0)))
		for order in subTestPoints:
			groupSkip.append(order)
			groupId = order.value.split(".")[0]
			print('groupId', groupId)
			PointStart = time.time()
			point = BusinessData.objects.get(id=order.follow_id)
			if point.count in [None, "None"]:
				point.count = 1
				point.save()
			pointCount = 0 if point.count in [0, '0', '', None] else int(point.count)
			result, error = 'omit', ''
			if point.id not in self.finalNode:
				continue
			if groupId not in groupSkip:
				for i in range(0, pointCount):
					result, error = self.process_process(point, step.id)
					if result != 'success' and not result.startswith('db_'):
						stepSuccessFlag = False
						num += 1
						groupSkip.append(groupId)
						break
			else:
				result, error = ('omit', "测试点[%s]执行次数=0 略过." % point.businessname) if point.count == 0 else (
					'skip', 'skip')
			if result.startswith('db_'):
				# 测试步骤执行sql处理失败时，不中断后续内容
				result = result[3:]
			pointTineSpend = int((time.time() - PointStart) * 1000)
			try:
				logger.info("准备保存结果===")
				detail = ResultDetail(taskid=self.taskId, plan=self.plan, case=case,
				                      step=step,
				                      businessdata=point,
				                      result=result,
				                      error=error, spend=pointTineSpend, loop_id=1, is_verify=self.runKind).save()
			
			except:
				logger.info('保存结果异常=>', traceback.format_exc())
			
			result = "<span id='step_%s' class='layui-bg-%s'>%s</span>" % (
				step.id, color_res.get(result, 'orange'), result)
			
			if 'omit' not in result:
				stepinfo = "<span style='color:#FF3399' id='step_%s' caseid='%s' casedes='%s'>%s</span>" % (
					step.id, case.id, case.description, step.description)
				businessinfo = "<span style='color:#FF3399' id='business_%s'>%s</span>" % (
					point.id, point.businessname)
				error = '   原因=>%s' % error if 'success' not in result else ''
				self.log("步骤[%s]=>测试点[%s]=>执行结果%s   %s" % (stepinfo, businessinfo, result, error))
		return stepSuccessFlag if num > 0 else 'omit'
	
	def process_process(self, point, stepId):
		# 预处理测试点数据
		# 1. 超时时间
		timeout = 30.0 if not point.timeout else float(point.timeout)
		# 2. 前置、后置操作列表
		prepPosition_List = point.preposition.split("|") if point.preposition is not None else ''
		postPosition_List = point.postposition.split("|") if point.postposition is not None else ''
		# 3. 数据校验和接口返回校验
		db_check = point.db_check if point.db_check is not None else ''
		itf_check = point.itf_check if point.itf_check is not None else ''
		checkStr = '%s|%s' % (itf_check, db_check) if db_check != '' else itf_check
		# 根据步骤类型分别进行不同操作
		step = Step.objects.get(id=stepId)
		# 设置使用的数据库
		self.setDbUse(step.db_id, 'business')
		
		self.log("-" * 50)
		self.log(
			"开始执行步骤[<span style='color:#FF3399' id='step_%s'>%s</span>] 测试点[<span style='color:#FF3399' id='business_%s'>%s</span>]" % (
				step.id, step.description, point.id, point.businessname))
		
		# 进行前置操作
		status, res = self.extraHandle(prepPosition_List, "前置操作")
		if status is not 'success':
			return status, res
		
		if step.step_type == 'interface' and step.content_type=='xml' and int(time.mktime(step.updatetime.timetuple()))<1600845096:
			# 能够确定是socket请求 兼容老的数据，把socket筛选出来并且保存新的值
			isOk, url = self.ParameterReplace(step.url, "地址",show=False)
			if not isOk:
				return 'fail', url
			if not url.__contains__("http"):
				step.step_type='socket'
				step.content_type=''
				step.save()
				return self.runSocket(step,point,postPosition_List,checkStr,timeout)
		
		if step.step_type == 'interface':
			return self.runInterface(step,point,postPosition_List,checkStr,timeout)
		
		elif step.step_type == 'function':
			return self.runFunction(step,point,postPosition_List,checkStr)
		
		elif step.step_type =='socket':
			return self.runSocket(step,point,postPosition_List,checkStr,timeout)
	
	def runInterface(self,step,point,postPosition_List,checkStr,timeout):
		params = point.queryparams if point.queryparams else ''
		body = point.params if point.params else ''
		url = step.url
		method = step.method
		headers = step.headers
		content_type = step.content_type
		temporaryVariable = step.temp
		
		status, requestData = self.handleRequestContent(url, headers, content_type, params, body)
		if status != 'success':
			return status, requestData
		
		status, responseData = self.apiRequest(method, requestData, timeout)
		if status != 'success':
			return status, responseData
		# 打印请求报文
		self.log('<xmp>%s</xmp>' % dump_request(responseData))
		
		status_code = responseData.status_code
		response_headers = responseData.headers
		response_text = responseData.text
		if response_text.lstrip().startswith('<!DOCTYPE html>'):
			self.log("<span style='color:#009999;'>请求响应内容为HTML，不显示</span>")
		else:
			self.log('<pre><xmp style="color:#009999;">接口返回结果：\n%s</xmp></pre>' % response_text)
		print("接口返回结果", response_text)
		if status_code != 200:
			return 'fail', '响应状态码=%s' % status_code
		
		# 进行后置操作
		status, res = self.extraHandle(postPosition_List, "后置操作", response_text)
		if status is not 'success':
			return status, res
		self.saveProperty(temporaryVariable, response_text)
		# 进行数据校验
		if checkStr:
			isOk, checkStr = self.ParameterReplace(checkStr, '校验内容', response_text)
			if not isOk:
				return 'fail', checkStr
			parse_type = 'xml' if 'xml' in step.content_type else 'json'
			if content_type.__contains__("urlencode"):
				bodytype = 'urlencode'
			elif content_type.__contains__("xml"):
				bodytype = 'xml'
			else:
				bodytype = 'json'
			resultList = self.formulaCheck(checkStr, rps_text=response_text, parse_type=parse_type,
			                               rps_header=response_headers, request_body=responseData.request.body,
			                               body_type=bodytype)
			failFlag = False
			for res in resultList:
				if res[0] != 'success':
					failFlag = True
				self.log(res[1])
			if failFlag:
				logger.info("数据校验没有全部通过")
				return 'fail', '数据校验没有全部通过'
		return 'success', ''
	
	def runFunction(self,step,point,postPosition_List,checkStr):
		param = point.params
		functionId = step.related_id
		funcName = step.body
		self.log("调用函数=>%s" % step.body)
		isOk, param = self.ParameterReplace(param, '函数参数')
		if not isOk:
			return 'fail', param
		
		res, msg = executeFunction(funcName, param, self.taskId)
		self.log("函数%s(%s)执行结果=>%s" % (funcName, param, res))
		if res is not 'success':
			self.log("函数%s(%s)执行报错信息:%s" % (funcName, param, msg))
			return 'db_%s' % res, msg
		
		# 进行后置操作
		status, res = self.extraHandle(postPosition_List, "后置操作")
		if status is not 'success':
			return status, res
		# 进行数据校验
		if checkStr:
			isOk, checkStr = self.ParameterReplace(checkStr, '校验内容')
			if not isOk:
				return 'fail', checkStr
			resultList = self.formulaCheck(checkStr, parse_type='db')
			failFlag = False
			for res in resultList:
				if res[0] != 'success':
					failFlag = True
				self.log(res[1])
			if failFlag:
				logger.info("数据校验没有全部通过")
				return 'fail', '数据校验没有全部通过'
		return 'success', ''
	
	def runSocket(self,step,point,postPosition_List,checkStr,timeout):
		body = point.params if point.params else ''
		url = step.url
		temporaryVariable = step.temp
		self.log("处理socket请求中的变量：")
		if url:
			isOk, url = self.ParameterReplace(url, "地址")
			if not isOk:
				return 'fail', url
		if body:
			isOk, body = self.ParameterReplace(body, "请求内容")
			if not isOk:
				return 'fail', body
		cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		cs.settimeout(timeout)
		
		length = str(len(body.encode('GBK'))).rjust(8)
		sendmsg = 'Content-Length:' + str(length) + '\r\n' + body
		url = url.replace('http://', '')
		host = url.split(':')[0].strip()
		port = url.split(':')[1].strip()
		try:
			cs.connect((host, int(port)))
			self.log('执行socket请求 IP=>%s   端口=>%s' % (host, port))
			self.log("<span style='color:#009999;'>发送内容=><xmp style='color:#009999;'>%s</xmp></span>" % sendmsg)
			cs.sendall(bytes(sendmsg, encoding='GBK'))
			recvdata = ''
			try:
				lenstr = cs.recv(25)
				recvdata += lenstr.decode('GBK')
				data = cs.recv(int(lenstr[15:23]))
				data = data.decode('GBK')
				recvdata += data
			except:
				# 失败时读取所有
				temp = cs.recv(1024).decode('GBK')
				while temp != '':
					recvdata += temp
					temp = cs.recv(1024).decode('GBK')
			
			self.log("<span style='color:#009999;'>响应内容=><xmp style='color:#009999;'>%s</xmp></span>" % recvdata)
			
			# 进行后置操作
			status, res = self.extraHandle(postPosition_List, "后置操作")
			if status is not 'success':
				return status, res
			
			self.saveProperty(temporaryVariable, recvdata, 'xml')
			# 进行数据校验
			if checkStr:
				isOk, checkStr = self.ParameterReplace(checkStr, '校验内容', recvdata)
				if not isOk:
					return 'fail', checkStr
				resultList = self.formulaCheck(checkStr, rps_text=recvdata, parse_type='xml', rps_header='',
				                               request_body=body, body_type='xml')
				failFlag = False
				for res in resultList:
					if res[0] != 'success':
						failFlag = True
					self.log(res[1])
				if failFlag:
					logger.info("数据校验没有全部通过")
					return 'fail', '数据校验没有全部通过'
		except:
			logger.info(traceback.format_exc())
			return 'error', traceback.format_exc()
		finally:
			cs.close()
		return 'success', ''
	
	def extraHandle(self, handleList, kind, responseText=None):
		for s in handleList:
			s = s.replace('\n', '').strip()
			if s not in ['None', None, '']:
				self.log("执行%s:%s" % (kind, s))
				isSuccess, newStr = self.ParameterReplace(s, "%s内容" % kind, responseText)
				if not isSuccess:
					return isSuccess, newStr
				try:
					funcName = re.findall('(.*?)\(', s)[0]
					params = re.findall('{}\((.*)\)'.format(funcName), s)[0]
				except:
					return 'error', '解析%s[%s]失败[%s]' % (kind, s, traceback.format_exc())
				
				status, res = executeFunction(funcName, params, self.taskId)
				if status == 'success':
					self.log("执行[<span style='color:#009999;'>%s</span>]%s【成功】" % (kind, s))
					continue
				else:
					self.log("执行[<span style='color:#009999;'>%s</span>]%s【失败】" % (kind, s))
					return status, res
		return 'success', ''
	
	def ParameterReplace(self, original, type, responseText=None,show=True):
		# 替换属性
		isOk, str = self.replaceProperty(original)
		if not isOk:
			return False, str
		print("替换属性后返回的",isOk,str)

		isOk, str = self.replaceVariable(str, responseText)
		print("替换变量后返回的",isOk,str)
		if not isOk:
			return False, str
		isOk, str = self.replaceFunction(str)
		if not isOk:
			return False, str
		print("替换函数后返回的", isOk, str)
		if original != str and show:
			self.log(
				"<span style='color:#009999;'>原始的%s=><xmp style='color:#009999;'>%s</xmp></span>" % (type, original))
			self.log("<span style='color:#009999;'>替换变量后的%s=><xmp style='color:#009999;'>%s</xmp></span>" % (type, str))
		elif original.strip() != '{}' and show:
			self.log(
				"<span style='color:#009999;'>%s=><xmp style='color:#009999;'>%s</xmp></span>" % (type, original))
		return True, str
	
	def apiRequest(self, method, requestData, timeout):
		if method.upper()=='GET':
			if requestData['params'] in [None,'','{}',{}]:
				requestData['params'] = requestData['body'].decode()
				requestData['body'] = None
		print("++++++++请求参数+++++++\n",requestData)
		try:
			rps = self.taskSession.request(
				method=method,
				url=requestData['url'],
				headers=requestData['headers'],
				params=requestData['params'],
				data=requestData['body'],
				files=requestData['files'],
				timeout=(10, timeout),
				proxies=self.proxy)
		except Exception as e:
			logger.info("请求发生异常",e)
			if 'timed out' in e.__str__():
				info = 'fail'
				msg = '请求超时 %s' % e
			else:
				info = 'error'
				msg = '请求异常:%s' % traceback.format_exc()
			return info, msg
		return 'success', rps
	
	def handleRequestContent(self, url, headers, content_type, params, body):
		self.log("处理请求参数中的变量：")
		files = None
		if url:
			isOk, url = self.ParameterReplace(url, "地址")
			if not isOk:
				return 'fail', url
		if params:
			isOk, params = self.ParameterReplace(params, "查询参数")
			if not isOk:
				return 'fail', params
		if body:
			isOk, body = self.ParameterReplace(body, "请求内容")
			if not isOk:
				return 'fail', body
		if headers or content_type:
			isOk, headers = self.ParameterReplace(headers, "请求头")
			if not isOk:
				return 'fail', headers
			if headers=="":
				headers="{}"
			try:
				headers = eval(headers)
				if not headers.get('User-Agent', None):
					headers[
						'User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36"
			except:
				print(traceback.format_exc())
				return 'error', "headers转换失败，可能有误"
			# 兼容旧的数据
			if 'json' in content_type:
				headers["Content-Type"] = 'application/json;charset=UTF-8'
				# 	body最终由dict类型转换成json字符串
				p1 = lambda x: json.loads(x)  # 格式是{"a":1,"b":2} 正确json格式
				p2 = lambda x: eval(x.replace('null', 'None').replace('false', 'False').replace('true',
				                                                                                'True'))  # 格式是{'a':1,'b':2,'c':null}
				for proc in [p1, p2]:
					try:
						body = proc(body)
					except:
						continue
					else:
						break
				body = json.dumps(body)
				logger.info("json类型请求，body结果：", body, type(body))
			
			
			elif 'urlencode' in content_type:
				headers["Content-Type"] = 'application/x-www-form-urlencoded;charset=UTF-8'
				try:
					# 	body最终转换成a=1&b=2格式  字符串类型map 单引号双引号通用
					body = parse.urlencode(ast.literal_eval(body.replace('\r', '').replace('\n', '').replace('\t', '')))
				except:
					if body.startswith("{") and not body.startswith("{{") and '"' in body:
						try:
							body = parse.urlencode(json.loads(body)).replace("None",'null').replace("True",'true').replace("False",'false')
						except:
							return 'error', '请求内容转换失败，请检查格式'
					# 	转换失败则保留原格式
				body = body.encode('utf-8')
			elif 'xml' in content_type:
				headers["Content-Type"] = 'application/xml'
			elif any(['formdata' in content_type, 'form-data' in content_type]):
				headers["Content-Type"] = 'multipart/form-data'
				files = dict()
				try:
					for k, v in eval(body).items():
						if not k.__contains__('file'):
							files[k] = (None, v)
						else:
							if isinstance(v, (str,)):
								filepath = os.path.join(get_space_dir(), v)
								if os.path.exists(filepath):
									files[k] = (v, open(filepath, 'rb'))
									
								elif os.path.exists(os.path.join(get_space_dir(), '默认', v)):
									files[k] = (v, open(os.path.join(get_space_dir(), '默认', v), 'rb'))
								else:
									return 'fail', ''
				except:
					return 'error', 'form-data的参数内容转换失败'
				body = None
				del headers["Content-Type"]
			else:
				headers["Content-Type"] = content_type
		
		return "success", {
			'params': params,
			'body': body,
			'url': url,
			'headers': headers,
			'files': files
		}
	
	# 数据校验
	def formulaCheck(self, formula, rps_text='', parse_type='', rps_header='',request_body='',body_type='json'):
		resultlist = []
		try:
			checklist = [x for x in formula.strip().split("|") if len(x) > 0]
			rps_text = rps_text.replace('null', "'None'").replace('true', "'True'").replace('false', "'False'")
			for item in checklist:
				successMsg = '表达式<span style="color:#009999;">【%s】校验成功 </span>' % item
				failMsg = '表达式<span style="color:#FF6666;">【%s】校验失败  </span>' % item
				item = _legal(item)
				k, op, v = '', '', ''
				for o in ('>=', '<=', '!=', '==', '>', '<', '$'):
					if o in item:
						k = item.split(o)[0].strip()
						v = item.split(o)[1].strip()
						op = o
						break
				if op == '':
					resultlist.append(('fail', '表达式%s格式错误' % item))
					continue
				logger.info('获取的项=>', k, v, op)
				if parse_type != 'xml':
					for badstr in ['\\n', '\\r', '\n']:
						rps_text = rps_text.replace(badstr, '')
				rps_text = rps_text.replace('null', "'None'").replace('true', "'True'").replace("false",
				                                                                                "'False'").replace(
					"<br>", "")
				# 响应内容文本包含判断
				
				if k.startswith('response.text'):
					result = ('success', successMsg) if op == '$' and str(rps_text).__contains__(
						v) else ('fail', failMsg)
					resultlist.append(result)
				#  响应头
				elif k.startswith('response.header'):
					ak = k.split('.')[-1]
					# hk = _get_hearder_key(ak)
					rh = rps_header.get('ak', '')
					if op == '$':
						flag = rh.__contains__(v)
					elif op == '==':
						flag = rh == str(v).strip()
					else:
						return 'fail', '响应头校验暂时只支持=,$比较.'
					result = ('success', successMsg) if flag else ('fail', failMsg + '期望值【%s】,实际值【%s】</span>' % (v, rh))
					resultlist.append(result)
				elif k.startswith("request.body."):
					p = None
					if isinstance(request_body, bytes):
						try:
							request_body = parse.unquote(request_body.decode('utf-8'))
						except:
							pass
					else:
						request_body = parse.unquote(request_body)
					if body_type =='urlencode':
						obj = {}
						for item in request_body.split("&"):
							a,b = item.split("=")
							obj[a] = b
						p = JSONParser(json.dumps(obj))
					elif body_type == 'json':
						p = JSONParser(request_body)
					elif body_type == 'xml':
						p = XMLParser(request_body.replace('\n', '', 1))
					if p:
						key = p.getValue(k.replace("request.body.", ""))
						key = str(key.replace('\r','').replace('\n','').strip())
						
						self.calculation(resultlist,key,op,str(v),successMsg,failMsg)
					else:
						resultlist.append(('error', "不支持的请求内容解析类型"))
				else:
					p = None
					v = v.replace('true', 'True').replace('false', 'False').replace('null', 'None')
					try:
						if parse_type == 'json':
							p = JSONParser(rps_text)
							tempv = p.getValue(k)
						elif parse_type == 'xml':
							if rps_text.startswith("Content-Length"):
								rps_text = '\n'.join(rps_text.split('\n')[1:])
							p = XMLParser(rps_text.replace('\n', '', 1))
							tempv = p.getValue(k)
						else:
							# 	保持原生字符串
							tempv = k
						if tempv in ['None',None]:
							tempv = k
						logger.info('表达式合成{%s,%s,%s}' % (str(tempv), op, v))
						self.calculation(resultlist,str(tempv),op,str(v),successMsg,failMsg)
					except:
						logger.error(traceback.format_exc())
						resultlist.append(('fail', failMsg + '响应内容与预期不一致'))
						break
		
		except:
			logger.error(traceback.format_exc())
			resultlist.append(('error', traceback.format_exc()))
		
		return resultlist
	
	def calculation(self,resultlist,k,op,v,successMsg,failMsg):
		exp = "".join([k, op, v])
		print(exp,successMsg,failMsg)
		try:
			rr = eval(exp)
			result = ('success', successMsg) if rr else ('fail', failMsg+'期望值【%s】,实际值【%s】' % (v, k))
			resultlist.append(result)
		except:
			logger.info('表达式等号两边加单引号后尝试判断..')
			if op == '$':
				res = eval("'%s'.__contains__('%s')" % (k, v))
			else:
				res = eval('''"%s"%s"%s"''' % (k, op, v))
			logger.info('判断结果=>', res)
			result = ('success', successMsg) if res else (
				'fail', failMsg + '期望值【%s】,实际值【%s】' % (v, k))
			resultlist.append(result)
	
	# 属性变量保存
	def saveProperty(self, target, responsetext,type='json'):
		cur = None
		try:
			if target is None or len(target) == 0:
				return 'success', ''
			
			isOk, target = self.ParameterReplace(target, '属性取值', responsetext)
			if not isOk:
				return 'error', target
			
			target = eval(target)
			
			for key, v in target.items():
				cur = key
				print("储存临时属性变量 响应内容:\n%s" % (responsetext))
				p = JSONParser(responsetext) if type=='json' else XMLParser(responsetext)
				value = p.getValue(v)
				if value != 0 and not value:
					value = v
				print("储存临时属性变量 解析的值:\n%s" % (value))
				if isinstance(value, str):
					self.tempVar[key] = value
				else:
					self.tempVar[key] = json.dumps(value)
				self.log("储存临时属性变量 [%s]:\n%s" % (key, self.tempVar[key]))
		
		except Exception as e:
			logger.info(traceback.format_exc())
			self.log("临时属性变量缓存失败=>属性名【%s】,原因 %s" % (cur, e))
	
	# 属性变量替换
	def replaceProperty(self, text):
		tempVars = re.findall("\$\{(.*?)\}", text)
		for var in tempVars:
			logger.info(self.tempVar, var)
			value = self.tempVar.get(var, None)
			if value is None:
				return False, '请检查是否定义属性%s' % var
			text = text.replace(r"${%s}" % var, str(value))
		
		return True, text
	
	# 替换变量
	def replaceVariable(self, text, responseText='',needCacheVar=False):
		try:
			varnames = re.findall('{{(.*?)}}', text)
			logger.info('varnames:', varnames)
			for varname in varnames:
				oldvarname = varname
				if varname.startswith('CACHE_'):
					varname = varname.replace("CACHE_","")
					needCacheVar = True
				print("asdasdsad",varname)
				if varname.strip() == 'STEP_PARAMS':
					dictparams = self.get_step_params(text)
					logger.info('==获取内置变量STEP_PARAMS=>\n', dictparams)
					logger.info('==STEP_PARAMS替换前=>\n', text)
					text = text.replace('{{%s}}' % varname, str(dictparams))
					logger.info('==STEP_PARAMS替换后=>\n', text)
					continue
				
				elif varname.strip() == 'RESPONSE_TEXT':
					logger.info('==获取text/html响应报文用于替换 responsetext={}'.format(responseText))
					if responseText:
						text = text.replace('{{RESPONSE_TEXT}}', responseText)
						logger.info('==RESPONSE_TEXT替换后=>\n', text)
						continue
				# 筛选全局或者局部变量useVar
				vars = Variable.objects.raw(
					"select v.id, v.description,v.gain,v.value,v.is_cache, t.planids,t.isglobal from manager_variable v ,manager_tag t WHERE v.key='%s' and v.id=t.var_id" % varname)
				useVar = None
				globaleVar = None
				for var in vars:
					if int(var.isglobal) == 1:
						globaleVar = var
					if int(var.isglobal) == 0:
						planids = json.loads(var.planids)
						ob = planids.get(self.plan.description, None)
						if ob and ob[1] == str(self.planId):
							useVar = var
							self.log('使用局部变量 %s 描述：%s' % (varname, var.description))
							break
				if useVar is None and globaleVar:
					useVar = globaleVar
					self.log('使用全局变量 %s 描述：%s' % (varname, useVar.description))
				if len(vars) == 0 or useVar is None:
					return False, '字符串[%s]变量【%s】替换异常,未在局部变量和全局变量中找到，请检查是否已正确配置' % (text, varname)
				isOk, gain = self.replaceVariable(useVar.gain,needCacheVar=needCacheVar)
				if not isOk:
					return False, gain
				isOk, value = self.replaceVariable(useVar.value,needCacheVar=needCacheVar)
				if not isOk:
					return False, value
				
				if len(gain) > 0 and len(value) > 0:
					return False, '变量【%s】同时设定了获取方式和值，请修改' % varname
				elif len(gain) == 0 and len(value) > 0:
					text = text.replace('{{%s}}' % varname, value, 1)
					self.log('替换变量 {{%s}}=>%s' % (varname, value))
				elif len(gain) > 0 and len(value) == 0:
					print("计算 gain",gain)
					
					if useVar.is_cache is True or needCacheVar:
						varCache = self.redisCon.hget(self.taskId + '_varCache', varname)
						if varCache:
							gainValue = varCache
						else:
							isOk, gainValue = self.gainCompute(gain)
							if isOk is not 'success':
								return False,gainValue
							self.redisCon.hset(self.taskId + '_varCache', varname, gainValue)
							self.redisCon.expire(self.taskId + '_varCache', 3600)
					else:
						isOk, gainValue = self.gainCompute(gain)
						print("计算 gain", isOk, gainValue)
						if isOk is not 'success':
							return False, gainValue
						self.redisCon.hset(self.taskId + '_varCache', varname, gainValue)
						self.redisCon.expire(self.taskId + '_varCache',3600)
					
					# 通过获取方式计算的变量都加入缓存中，后面使用的会覆盖老的值，在进行校验步骤时先尝试从缓存中获取，没有的话再重新计算。开启了缓存按钮的变量从始至终保持。
					

					
					self.log('替换变量 {{%s}}=>%s' % (oldvarname, gainValue))
					text = text.replace('{{%s}}' % oldvarname, str(gainValue), 1)
				elif len(gain) == 0 and len(value) == 0:
					return False, '变量【%s】未设定获取方式或者值，请修改' % varname
			
			return True, text
		except Exception as e:
			print(traceback.format_exc())
			return False, e
	
	def get_step_params(self,paraminfo):
		'''
		获取内置变量STEP_PARAMS
		'''
		def _next(cur):
			if isinstance(cur, (dict,)):
				i = 0
				for k in list(cur.keys()):
					i += 1
					v = cur[k]
					try:
						v = eval(v)
					except:
						pass
					if isinstance(v, (str,)):
						find_var = len(re.findall('\{\{.*?\}\}', v))
						if find_var:
							if v.__contains__('{{STEP_PARAMS}}'):
								logger.info('字符串发现STEP_PARAMS', v)
								del cur[k]
							else:
								cur[k] = self.replaceVariable(v)[1]
					else:
						_next(v)
					print(k,cur)

			elif isinstance(cur, (list,)):
				itemindex = -1
				for sb in cur:
					itemindex  += 1
					if isinstance(sb, (str,)):
						find_var = len(re.findall('\{\{.*?\}\}', sb))
						if find_var:
							if sb.__contains__('{{STEP_PARAMS}}'):
								# del parent[key]
								cur.remove(sb)
							else:
								cur[itemindex] = self.replaceVariable(sb)[1]
					else:
						_next(sb)
		ps = paraminfo
		try:
			ps = eval(paraminfo)
			if isinstance(ps, (dict,)):
				logger.info('ps=>',ps)
				_next(ps)
				self.log('获取内置变量[字典模式]STEP_PARAMS=> %s ' % str(ps))
				return ps
		except:
			try:
				dl = dict()
				for s1 in ps.split('&'):
					# a=1&b=2
					p1 = s1.split('=')[0]  # a
					p2 = '='.join(s1.split('=')[1:])
					if p1.__contains__('?'):
						p1 = p1.split('?')[1]
					
					try:
						import json
						logger.info('p1=>', p1)
						dl[p1] = eval(p2)
					except:
						dl[p1] = p2
				_next(dl)
				self.log('获取内置变量[a=1&b=2模式]STEP_PARAMS=> %s ' % str(dl))
				return dl
			except:
				return ('error', 'a=1&b=2模式获取内置变量STEP_PARAMS异常')
			
	
	# 变量获取方式计算
	def gainCompute(self, gain):
		try:
			res_1 = re.findall('\s+', gain)
			res_2 = re.findall("\w{1,}\(.*?\)", gain)
			if len(res_1) == 0 and len(res_2) > 0:
				a = re.findall('(.*?)\((.*?)\)', gain)
				funcName = a[0][0]
				params = a[0][1]
				return executeFunction(funcName,params,self.taskId)
			
			else:
				op = Mysqloper()
				isok, gain = self.ParameterReplace(gain, '变量获取方式')
				if not isok:
					return gain
				
				if ';' in gain:
					return op.db_execute2(gain, taskid=self.taskId)
				else:
					return op.db_execute(gain, taskid=self.taskId)
		except Exception as e:
			# traceback.logger.info_exc()
			return 'error', traceback.format_exc()
	
	def replaceFunction(self, str_):
		resultlist = []
		functionsList = re.findall('\$\[(.*?)\((.*?)\)\]', str_)
		if len(functionsList) == 0: return True, str_
		
		for function in functionsList:
			funcName,params = function
			status, res = executeFunction(funcName, params, self.taskId)
			self.log('计算函数表达式:<br/>%s(%s) <br/>结果:<br/>%s' % (funcName,params, res if res else '成功'))
			resultlist.append((status, res))
			
			if status is 'success':
				old = '$[%s(%s)]' %(funcName, function[1])
				str_ = str_.replace(old, str(res))
				logger.info('替换函数引用 %s\n =>\n %s ' % (old, str(res)))
		
		if len([x for x in resultlist if x[0] is 'success']) == len(resultlist):
			logger.info('--成功计算引用表达式 结果=>', str_)
			return True, str_
		else:
			alist = [x[1] for x in resultlist if x[0] is not 'success']
			logger.info('--异常计算引用表达式=>', alist[0])
			return False, alist[0]




def executeFunction(funcName,params,taskid):
	params = params.replace('\n','')
	if "r'" not in params and 'r"' not in params:
		params = params.replace("\\\"", '"')
	isBuiltin = funcName in [x.name for x in getbuiltin()]
	if funcName.startswith('dbexecute'):
		execStr = '%s("""%s""",taskid="%s")' % (funcName, params, taskid)
	else:
		if params:
			execStr = '%s(%s,taskid="%s")' % (funcName, params, taskid)
		else:
			execStr = '%s(taskid="%s")' % (funcName,taskid)
	result = (None,'')
	try:
		if isBuiltin:
			result = eval(execStr)
			logger.info("调用内置函数表达式:%s 结果为:%s" % (execStr, result))

		else:
			function = Function.objects.filter(name=funcName.strip())
			if function:
				flag = function.first().flag
				f = __import__('manager.storage.private.Function.func_%s' % flag, fromlist=True)
				execStr = "f.%s" % execStr.replace('\n', '')
				result = eval(execStr)
				del sys.modules['manager.storage.private.Function.func_%s' % flag]
				logger.info("调用用户定义表达式:%s 结果为:%s" % (execStr, result))

	except:
		logger.error(traceback.format_exc())
		msg = '函数参数数量错误，请检查' if 'got an unexpected keyword' in traceback.format_exc() else traceback.format_exc()
		return 'error', '函数执行错误' + msg
	
	if isinstance(result, (tuple,)):
		return result
	
	elif isinstance(result, (bool,)):
		if result is False:
			return 'fail', '[%s]返回结果[false]不符合预期' % funcName
		else:
			return 'success',"执行成功"
	elif result is None or isinstance(result, (str,)):
		return 'success', result
	else:
		return 'error', '内置函数返回类型{None,bool,tuple}'
	
