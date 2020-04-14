#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-08-29 08:43:52
# @Author  : Blackstone
# @to      :

# from manager import models

import requests, re, warnings, copy, os, traceback, base64, time, json, datetime, smtplib, base64
from collections import namedtuple
from login.models import User
from django.http import HttpResponse, JsonResponse
from hashlib import md5
from ME2.settings import logme
from . import models
from login import models as md
from .models import Function
from .builtin import *
from .db import Mysqloper as op
from pyDes import *
from django.conf import settings


# 用户变量缓存 key=user.varname
# __varcache=dict()

# #sql关键字
# __sql_key=('insert','delete','update','select')

# #内置支持的比较操作，还要支持包含操作
# __compare_word=('>=','<=','!=','=','>','<')


##三方调用

def clear_task_before(taskid):
	'''
	清除任务id之前可能存在的结果
	'''
	detaillist = list(models.ResultDetail.objects.filter(taskid=taskid))
	[x.delete() for x in detaillist]


def gen_third_invoke_url(planid):
	taskid = planid
	callername = models.Plan.objects.get(id=planid).author.name
	mwstr = 'callername=%s&taskid=%s' % (callername, taskid)
	return '%s/manager/third_party_call/?v=%s&planid=%s' % (
		settings.BASE_URL, EncryptUtils.base64_encrypt(EncryptUtils.des_encrypt(mwstr)), planid)


def decrypt_third_invoke_url_params(paramV):
	d = {}
	mwstr = EncryptUtils.des_decrypt(EncryptUtils.base64_decrypt(paramV))
	for x in mwstr.split('&'):
		key = x.split('=')[0]
		v = x.split('=')[1]
		d[key] = v
	
	return d


"""
计划&&用例相关
"""


def genorder(kind="case", parentid=None, childid=None):
	code = 0
	
	# logme.debug("type=%s parentid=%s childid=%s"%(kind,parentid,childid))
	
	try:
		if parentid is not None:
			# steps=models.Case.objects.get(id=parentid).steps
			start_group_id = 1
			start_index = 1
			
			if childid is None:
				# 根据创建时间重新排序
				# sorted_steps_order= models.Order.objects.filter(main_id=parentid,kind=kind).order_by('createtime')
				
				# 保持原来顺序重新排序
				sorted_steps_order = ordered(list(models.Order.objects.filter(main_id=parentid, kind=kind)))
				
				# logme.debug(len(sorted_steps_order))
				for order in sorted_steps_order:
					# logme.debug(order.id,order.main_id,order.follow_id)
					models.Order.objects.filter(id=order.id).update(value="%s.%s" % (start_group_id, start_index))
					# models.Order.objects.filter(id=order.id).update(value='1.4')
					start_index = start_index + 1
			
			else:
				##
				
				##更新指定step或case后的执行序号
				sorted_steps_order = [_ for _ in
				                      models.Order.objects.filter(main_id=parentid, kind=kind).order_by('value')]
				size = len(sorted_steps_order)
				if size == 1:
					order = models.Order.objects.get(main_id=parentid, kind=kind)
					order.value = '1.1'
					order.save()
				
				else:
					logme.debug("更新group..")
					is_update = False
					for order in sorted_steps_order:
						step_id = order.follow_id
						logme.debug(type(childid))
						if int(step_id) == int(childid):
							is_update = True
							value = models.Order.objects.get(main_id=parentid, follow_id=childid, kind=kind).value
							old_group_id = int(value.split(".")[0])
							start_group_id = int(old_group_id) + 1
							models.Order.objects.filter(id=order.id).update(
								value="%s.%s" % (start_group_id, start_index))
							start_index = int(start_index) + 1
						else:
							if is_update == True:
								if start_group_id == 1:
									raise Exception('groupid=>1')
								models.Order.objects.filter(id=order.id).update(
									value="%s.%s" % (start_group_id, start_index))
								start_index = int(start_index) + 1
	
	except Exception as e:
		code = 1
		traceback.logme.debug_exc(e)
	
	finally:
		return code


def changepostion(kind, parentid, childid, move=1):
	# logme.debug('=='*100)
	# logme.debug(kind,parentid,childid,move)
	flag, msg = 'success', ''
	try:
		parentid = int(parentid)
		childid = int(childid)
		move = int(move)
		# logme.debug(parentid,childid,move)
		orderlist = ordered(list(models.Order.objects.filter(main_id=parentid, kind=kind).order_by('value')))
		# logme.debug("orderlist=>",orderlist)
		size = len(orderlist)
		# logme.debug('移动项所列表长度',size)
		pos = -1
		for item in orderlist:
			pos = pos + 1
			if item.follow_id == childid:
				break;
		
		if pos + move >= size or pos + move < 0:
			logme.debug("------------边界操作忽略...--------------")
			return 0
		
		# logme.debug("移动项所在位置=>",pos)
		
		tmp = orderlist[pos].value
		orderlist[pos].value = orderlist[pos + move].value
		orderlist[pos].save()
		orderlist[pos + move].value = tmp
		orderlist[pos + move].save()
	except:
		flag = 'error'
		msg = 'changepostion操作异常[%s]' % traceback.format_exc()
		logme.debug(traceback.format_exc())
	return (flag, msg)


def swap(kind, main_id, aid, bid):
	flag, msg = 'nosee', ''
	try:
		
		ao = models.Order.objects.get(kind=kind, main_id=main_id, follow_id=aid)
		bo = models.Order.objects.get(kind=kind, main_id=main_id, follow_id=bid)
		tmp = ao.value
		ao.value = bo.value
		bo.value = tmp
		
		ao.save()
		bo.save()
		flag, msg = 'success', '操作成功'
	
	
	except:
		logme.debug(traceback.format_exc())
		msg = 'swap操作异常%s' % traceback.format_exc()
		flag = 'error'
	
	return (flag, msg)


# def getpagedata(list_,request):
# 	"""
# 	获取分页数据
# 	"""
# 	page=int(request.GET.get("page"))
# 	limit=int(request.GET.get("limit"))

# 	logme.debug("获取分页数据 page=%s limit=%s"%(page,limit))

# 	start=(page-1)*limit+1
# 	end=page*limit+1
# 	return list_[start:end]


def testinterface(interface):
	try:
		url = interface.url
		body = interface.body
		method = interface.method
		
		cmdstr = 'requests.%s(%s,data=%s)' % (method, url, body)
		logme.debug("执行请求=>", cmdstr)
		res = eval(cmdstr)
		logme.debug("执行结果=>", res.text)
		return True
	except Exception as e:
		logme.debug(e)


def testfunc(functionstr):
	try:
		logme.debug("执行函数=>", functionstr)
		res = eval(functionstr)
		logme.debug("执行结果=>", res)
		return res
	except Exception as e:
		return False


# def runstep(step):
# 	type_=step.step_type
# 	if type_=='function':
# 		try:
# 			eval(step.body)
# 			return True
# 		except Exception as e:
# 			logme.debug(e)
# 			return False

# 	elif type_=='interface':

# 		try:
# 			url=step.interface.url
# 			body=step.body
# 			method=step.interface.method
# 			logme.debug("接口地址=>"%url)
# 			logme.debug("请求方式=>"%method)
# 			logme.debug("请求参数=>"%body)
# 			#requests.post(url,data=body)
# 			response=eval('requests.%s(url,data=body)'%method)
# 			d=eval(_responsefilter(response.text))
# 			db_check_items=step.db_check.split("||")
# 			itf_check_items=step.itf_check.split("||")

# 			##验证过程....

# 			#####

# 			return True
# 		except Exception as e:
# 			logme.debug(e)
# 			return False

# 	else:
# 		warnings.warn("不能识别的测试步骤类型=>%s"%type_)

# 	return False


# def _is_sql_call(str_):
# 	s=str_.strip()
# 	res=len(re.findall('|'.join(__sql_key),s))
# 	#logme.debug(res)
# 	if res>0:
# 		return True
# 	else:
# 		return False


# def _eval(str_):
# 	"""
# 	执行有意义的函数 or sql字符串
# 	"""

# 	if _is_sql_call(str_):
# 		return op().db_execute(str_)
# 	else:
# 		return eval(str_)


# def _responsefilter(msg):
# 	msg=msg.replace('true','True').replace('false','False').replace('null','None')
# 	return msg

# def _responsecheck(response,wait_check_list=None):
# 	'''
# 	可能的情况
# 	{{x}}=1 
# 	code=3
# 	list[0].text=1111
# 	'''
# 	if wait_check_list is None:
# 		warnings.warn("校验列表为空，默认通过..")
# 		return True

# 	#存储所有校验项的执行结果
# 	res=[]
# 	operator='='
# 	for item in wait_check_list:
# 		operator=_getoperator(item)
# 		if operator is None:
# 			warnings.warn('校验表达式无法解析=>%s'%item)
# 			return True

# 		left=item.split(operator)[0]
# 		right=item.split(operator)[1]


# def _getoperator(str_):
# 	"""
# 	获取操作符
# 	"""

# 	for x in __compare_word:
# 		if x in str_:
# 			return x

# 	return None

def packagemenu(list_):
	root = None
	for menu in list_:
		# logme.debug(menu.parentid)
		if menu.parentid == '0':
			root = menu
			break
	
	# logme.debug(root)
	
	_packagenodechildren(root, list_)
	
	return root


def _packagenodechildren(menu, list_):
	if getattr(menu, 'child', None) is None:
		menu.child = []
	
	for cmenu in list_:
		cmenu.child = []
		if cmenu.parentid == str(menu.id):
			logme.debug("uuuuuuuuuuuuuuuuuuuuuuuuuuuuu")
			menu.child.append(cmenu)
			alist = copy.deepcopy(list_)
			alist.remove(cmenu)
			_packagenodechildren(cmenu, alist)


# class MenuJsonEncoder(json.JSONEncoder):
# 	def default(self,obj):
# 		url=obj.url
# 		text=obj.text
# 		icon=obj.icon
# 		child=obj.child

# 		return {
# 		'urr':url,
# 		'text':text,
# 		'icon':icon,
# 		'child':child

# 		}


"""
实例json解析
"""


class XJsonEncoder(json.JSONEncoder):
	
	def __init__(self, attrs=None, **args):
		
		self._total = args.get('total', None)
		# logme.debug('self.total=>',self._total)
		if self._total is not None:
			del args['total']
		
		super(XJsonEncoder, self).__init__(**args)
		self._attrs = attrs
	
	# logme.debug('attrs=>',self._attrs)
	# logme.debug('args=>',args)
	
	def default(self, obj):
		_map = {}
		
		# logme.debug(len(self._attrs))
		for x in self._attrs:
			# logme.debug("name=>",x)
			v = ''
			
			try:
				v = getattr(obj, x)
				# if isinstance(v,datetime.datetime):
				# 	v=v[:18]
				
				v = str(v)
			
			except:
				# logme.debug(type(obj))
				# logme.debug('error',obj,x)
				v = str(obj)
			finally:
				_map[x] = v
		
		# logme.debug(_map)
		
		return _map
	
	def encode(self, obj):
		
		evalstr = super(XJsonEncoder, self).encode(obj)
		evalstr = evalstr.replace('false', 'False').replace('true', 'True')
		L = eval(evalstr)
		
		return {
			"code": 0,
			"msg": '操作成功',
			# "count":len(L),
			"count": self._total,
			# "data":[{'key':'host','value':'2.2.34.3'}],
			"data": L
		}


class ProductEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(ProductEncoder, self).__init__(['id', 'description', 'createtime', 'updatetime', 'author'], **args)


class VarEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(VarEncoder, self).__init__(
			['id', 'description', 'key', 'gain', 'value', 'createtime', 'updatetime', 'is_cache', 'tag', 'author'],
			**args)


class UserEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(UserEncoder, self).__init__(['id', 'createtime', 'updatetime', 'name', 'password'], **args)


class ItfEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(ItfEncoder, self).__init__(
			['id', 'name', 'headers', 'url', 'content_type', 'method', 'version', 'createtime', 'updatetime'], **args)


class CaseEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(CaseEncoder, self).__init__(
			['id', 'author', 'priority', 'description', 'steps', 'createtime', 'updatetime', 'db_id', 'count'], **args)
	
	def encode(self, obj):
		L = eval(super(XJsonEncoder, self).encode(obj))
		if not isinstance(L, (list)):
			L = [L]
		
		for x in L:
			try:
				o1 = list(models.Order.objects.filter(kind='plan_case', follow_id=int(x.get('id'))))
				o2 = list(models.Order.objects.filter(kind='case_case', follow_id=int(x.get('id'))))
				
				if len(o1) > 0:
					x['weight'] = o1[0].value
				else:
					if len(o2) > 0:
						x['weight'] = o2[0].value
					else:
						x['weight'] = '未知'
			
			except:
				logme.debug(traceback.format_exc())
				x['weight'] = '未知'
		
		return {
			"code": 0,
			"msg": '操作成功',
			# "count":len(L),
			"count": self._total,
			# "data":[{'key':'host','value':'2.2.34.3'}],
			"data": L
		}


class PlanEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(PlanEncoder, self).__init__(
			['id', 'author', 'last', 'description', 'cases', 'createtime', 'updatetime', 'run_type', 'run_value',
			 'mail_config_id', 'db_id', 'is_send_dingding', 'is_send_mail', 'schemename'], **args)
	
	def encode(self, obj):
		# logme.debug('hhhh'*100)
		L = eval(super(XJsonEncoder, self).encode(obj))
		code = 0
		if not isinstance(L, (list)):
			L = [L]
		
		# logme.debug('UU'*100)
		# logme.debug(L)
		
		for x in L:
			
			try:
				invoke_url = gen_third_invoke_url(x['id'])
				x['invoke_url'] = invoke_url
				
				config_id = x.get('mail_config_id')
				is_send_mail = models.MailConfig.objects.get(id=config_id).is_send_mail
				is_send_dingding = models.MailConfig.objects.get(id=config_id).is_send_dingding
				x['is_send_mail'] = is_send_mail
				x['is_send_dingding'] = is_send_dingding
			# logme.debug("uuuuuuuuuu=>",x)
			
			except:
				
				msg = '计划未关联邮件'
				x['is_send_mail'] = 'disabled'
				pass
		
		logme.debug(L)
		
		return {
			"code": 0,
			"msg": '操作成功',
			# "count":len(L),
			"count": self._total,
			# "data":[{'key':'host','value':'2.2.34.3'}],
			"data": L
		}


class ResultEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(ResultEncoder, self).__init__(
			['id', 'author', 'case', 'success', 'skip', 'fail', 'updatetime', 'createtime'], **args)


class ResultDetailEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(ResultDetailEncoder, self).__init__(['id', 'case', 'step', 'result', 'createtime', 'updatetime'], **args)


class FunctionEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(FunctionEncoder, self).__init__(
			['id', 'kind', 'author', 'name', 'description', 'flag', 'body', 'createtime', 'updatetime'], **args)


class StepEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(StepEncoder, self).__init__(
			['id', 'businesstitle', 'author', 'priority', 'interface', 'description', 'headers', 'body', 'db_check',
			 'itf_check', 'step_type', 'createtime', 'updatetime', 'tag_id', 'temp', 'url', 'content_type', 'method',
			 'db_id', 'count'], **args)
	
	def encode(self, obj):
		L = eval(super(XJsonEncoder, self).encode(obj))
		if not isinstance(L, (list)):
			L = [L]
		
		for x in L:
			# logme.debug("x=>",x)
			tag_id = x.get('tag_id')
			uid = x.get('id')
			try:
				
				logme.debug('weight=>', uid)
				x['weight'] = list(models.Order.objects.filter(kind='case_step', follow_id=int(uid)))[0].value
			
			except:
				logme.debug(traceback.format_exc())
				x['weight'] = '未知'
			
			try:
				tagname = models.Tag.objects.get(id=tag_id.strip()).name
				x['tagname'] = tagname
			except:
				x['tagname'] = ''

		return {
			"code": 0,
			"msg": '操作成功',
			# "count":len(L),
			"count": self._total,
			# "data":[{'key':'host','value':'2.2.34.3'}],
			"data": L
		}


class BusinessDataEncoder(XJsonEncoder):
	
	def __init__(self, **args):
		super(BusinessDataEncoder, self).__init__(
			['id', 'businessname', 'db_check', 'itf_check', 'params', 'postposition', 'preposition', 'count',
			 'parser_id', 'parser_check'], **args)
	
	def encode(self, obj):
		from .cm import getchild
		L = eval(super(XJsonEncoder, self).encode(obj))
		if not isinstance(L, (list)):
			L = [L]
		
		steps = models.Step.objects.all()
		
		for x in L:
			try:
				
				x['weight'] = list(models.Order.objects.filter(kind='step_business', follow_id=int(x.get('id'))))[
					0].value
			
			except:
				logme.debug('weight=>', traceback.format_exc())
				x['weight'] = '未知'
			
			# logme.debug('x[weight]=>',x['weight'])
			
			if x.get('count') == 'None':
				x['count'] = 1
			# logme.debug('count=>',x['count'])
			
			try:
				##找关联step
				stepinst = None
				for step in list(models.Step.objects.all()):
					businessids = [sb.id for sb in getchild('step_business', step.id)]
					# logme.debug(businessids)
					idd = x.get('id')
					try:
						idd = int(idd)
					except:
						pass
					
					if idd in businessids:
						stepinst = step
						break;
				
				if stepinst is None:
					warnings.warn('获取业务数据[id=%s]关联步骤操作失败' % x.get('id'))
				else:
					logme.debug('[获取业务数据关联步骤]step_id=%s' % stepinst.id)
					# stepinst=step_matchs[0]
					# tag_id=stepinst.tag_id
					x['stepname'] = stepinst.description
				x['businessname'] = x.get('businessname')
			
			# if tag_id.strip():
			# 	x['tagname']=models.Tag.objects.get(id=tag_id.strip()).name
			
			except:
				logme.debug(traceback.format_exc())
		# x['tagname']=''
		
		return {
			"code": 0,
			"msg": '操作成功',
			# "count":len(L),
			"count": self._total,
			# "data":[{'key':'host','value':'2.2.34.3'}],
			"data": L
		}


class TagEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(TagEncoder, self).__init__(['id', 'author', 'name', 'createtime', 'updatetime'], **args)


class MailConfigEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(MailConfigEncoder, self).__init__(
			['id', 'author', 'smtp_host', 'smtp_port', 'sender_name', 'sender_nick', 'sender_pass', 'is_send_mail',
			 'createtime', 'updatetime', 'description', 'to_receive', 'cc_receive', 'color_scheme', 'rich_text',
			 'dingdingtoken'], **args)


class OrderEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(OrderEncoder, self).__init__(
			['id', 'main_id', 'follow_id', 'value', 'kind', 'updatetime', 'createtime', 'author'], **args)


class DBEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(DBEncoder, self).__init__(
			['id', 'kind', 'dbname', 'host', 'port', 'username', 'password', 'description', 'author', 'scheme',
			 'createtime',
			 'updatetime'], **args)


class TemplateEncoder(XJsonEncoder):
	
	def __init__(self, **args):
		super(TemplateEncoder, self).__init__(
			['id', 'kind', 'name', 'description', 'author', 'createtime', 'updatetime'], **args)


class TemplateFieldEncoder(XJsonEncoder):
	def __init__(self, **args):
		super(TemplateFieldEncoder, self).__init__(
			['id', 'fieldcode', 'description', 'start', 'end', 'index', 'template'], **args)


def simplejson(code=0, msg='', **kw):
	_dict = {}
	
	_dict['code'] = code
	_dict['msg'] = msg
	
	for key, value in kw.items():
		_dict[key] = value
	
	return json.dumps(_dict)


def pkg(code=0, msg='', **kw):
	_dict = {}
	
	_dict['code'] = code
	_dict['msg'] = msg
	
	for key, value in kw.items():
		_dict[key] = value
	
	return _dict


def get_params(request):
	'''
	封装请求参数

	'''
	o = {**dict(request.POST), **dict(request.GET)}
	for ok in o:
		o[ok] = o.get(ok)[0]
	
	return o


def getpagedata(data, page, limit):
	'''
	返回分页数据与元数据大小
	'''
	logme.debug('page=>%s limit=>%s' % (page, limit))
	if page is None or limit is None:
		return data, len(data)
	
	if data is None:
		data = []
	
	old = copy.copy(data)
	start = (int(page) - 1) * int(limit)
	end = int(page) * int(limit)
	data = data[start:end]
	
	logme.debug("分页信息[分页数据大小=%s 返回%s-%s数据]" % (len(old), start + 1, end))
	# logme.debug(start,end)
	return data, len(old)


def ordered(iterator, key='value'):
	"""
	执行列表根据value从小到大排序
	"""
	try:
		for i in range(len(iterator) - 1):
			for j in range(i + 1, len(iterator)):
				# logme.debug(key,getattr(iterator[i],key).split(".")[0],int(str(getattr(iterator[i],key)).split(".")[0]))
				# logme.debug('attr value=>',iterator[i].value)
				
				groupa = int(str(getattr(iterator[i], key)).split(".")[0])
				groupb = int(str(getattr(iterator[j], key)).split(".")[0])
				
				if groupa > groupb:
					tmp = iterator[i]
					iterator[i] = iterator[j]
					iterator[j] = tmp
				
				elif groupa == groupb:
					indexa = int(getattr(iterator[i], key).split(".")[1])
					indexb = int(getattr(iterator[j], key).split(".")[1])
					if indexa > indexb:
						tmp = iterator[i]
						iterator[i] = iterator[j]
						iterator[j] = tmp
	
	except:
		logme.debug(traceback.format_exc())
	finally:
		return iterator


"""
任务调度
"""


def gettaskid(plan):
	"""
	任务id
	"""
	# s=str(time.time())
	# new_md5 = md5()
	# new_md5.update(s.encode(encoding='utf-8'))
	# return new_md5.hexdigest()
	taskid = base64.b64encode((re.findall('(?<=\[).*?(?=])', plan)[0] + '_' + str(time.time())).encode()).decode()
	return taskid


def getbuiltin(searchvalue=None, filename='builtin.py'):
	"""
	获取内置函数列表 model.Function形式组装
	"""
	
	path = os.path.join(os.path.dirname(__file__), filename)
	list_ = []
	with open(path, encoding='utf-8') as f:
		content = f.read()
		# logme.debug(content)
		methodnames = re.findall("def\s+(.*?)\(", content)
		logme.debug('builtin methodnames=>', methodnames)
		if searchvalue is None:
			for methodname in methodnames:
				if methodname.startswith('_'):
					continue;
				f = Function()
				f.name = methodname
				f.description = eval(methodname).__doc__.strip()
				f.kind = '内置函数'
				f.createtime = f.updatetime = '*'
				list_.append(f)
		else:
			for methodname in methodnames:
				if methodname.startswith('_'):
					continue;
				if (searchvalue in methodname) or (searchvalue in eval(methodname).__doc__.strip()):
					f = Function()
					f.name = methodname
					f.description = eval(methodname).__doc__.strip()
					f.kind = '内置函数'
					f.createtime = f.updatetime = '*'
					list_.append(f)
	return list_


"""
自定义函数管理
"""


class Fu:
	@classmethod
	def load_data(cls, id_=None):
		"""
		更新本地函数文件
		"""
		
		logme.debug("*" * 20)
		logme.debug("开始更新本地函数信息..")
		
		try:
			list_ = list(models.Function.objects.all())
			for x in list_:
				
				author = str(x.author)
				filename = "func_%s" % x.flag
				body = x.body
				# path = os.path.join(os.path.dirname(__file__), 'Function', author)
				path = os.path.join(os.path.dirname(__file__), 'storage', 'private', 'Function', author)
				
				if not os.path.exists(path):
					os.makedirs(path)
				# logme.debug("path=>",path)
				# add __init__.py
				initpath = os.path.join(path, "__init__.py")
				if not os.path.exists(initpath):
					with open(initpath, 'w'):
						pass
				
				path = os.path.join(path, filename + '.py')
				with open(path, 'w', encoding='utf-8') as f:
					# logme.debug("body=>",body)
					# logme.debug(type(body))
					a = base64.b64decode(body).decode(encoding='utf-8')
					# logme.debug(a)
					f.write(a)
				
				if id_ is not None and id_ == x.id:
					logme.debug("*" * 20)
					logme.debug("更新函数:%s 完毕." % x.name)
					logme.debug("*" * 20)
					return 0
			
			logme.debug("*" * 20)
			logme.debug("更新所有函数完毕.")
			logme.debug("*" * 20)
			return 0
		
		except Exception as e:
			logme.debug(e)
			# traceback.logme.debug_exc(e)
			logme.debug("*" * 20)
			logme.debug("更新函数失败.")
			logme.debug("*" * 20)
			return 1
	
	@classmethod
	def _md5(cls, s):
		"""
		函数文件名标识
		"""
		new_md5 = md5()
		new_md5.update(s.encode(encoding='utf-8'))
		return new_md5.hexdigest()
	
	@classmethod
	def tzm_compute(cls, src, pattern):
		"""
		计算方法特征码
		通过pattern从src字符串获取方法名和参数串计算特征码
		"""
		pool = [chr(x) for x in range(97, 123)]
		m = re.findall(pattern, src)
		funcname = m[0][0]
		paramlist = m[0][1].split(",")
		
		# 带关键字参数和可变参数的 都按a()计算
		# 参数带=好 记为关键参数 去除
		logme.debug('函数的所有参数数据=>',paramlist)
		paramlist = [p for p in paramlist if not p.startswith('*') and not p.__contains__('=') and p.strip()]
		logme.debug('函数的去除无效参数数据=>',paramlist)
		size = len(paramlist)
		logme.debug('大小=>',size)
		paramstr = ",".join(pool[0:size])
		final = "%s(%s)" % (funcname, paramstr)
		logme.debug('\n获取函数特征码铭文=>\n', final)
		md5_=cls._md5(final)
		logme.debug('\n获取函数特征码密文=>\n', md5_)
		
		return md5_
	
	@classmethod
	def call(cls, funcobj, call_str, builtin=False, username=None, taskid=None):
		# logme.debug("内置=>",builtin)
		# logme.debug('调用=》',call_str)
		try:
			res = None
			if builtin is True:
				try:
					call_str = call_str.replace('\n', '')
					# logme.debug('调用原表达式=>', call_str)
					#无效代码可以去掉
					# if call_str.startswith('dbexecute') and taskid not in call_str:
					# 	call_str = call_str.replace(')', ',taskid="%s",callername="%s")' % (taskid, username))
					

					res = eval(call_str)
					logme.debug("调用内置函数表达式:%s 结果为:%s" % (call_str, res))
					if isinstance(res, (tuple,)):
						if res[0] is not 'success':
							return res
					
					elif isinstance(res, (bool,)):
						if res is False:
							return ('fail', '[%s]没按预期执行 提前结束' % re.findall('(.*?)\(', call_str)[0])
					elif res is None:
						pass
					
					elif isinstance(res, (str,)):
						pass
					else:
						return ('error', '内置函数返回类型{None,bool,tuple}')
				
				except:
					try:
						methodname = call_str.split('(')[0]
						logme.debug('methodname=>', methodname)
						
						s1 = re.findall('\((.*?),taskid=', call_str)[0]  # sql
						s2 = re.findall('taskid=(.*?),', call_str)[0]  # taskid
						s3 = re.findall('callername=(.*?)\)', call_str)[0]  # callername
						
						logme.debug('s1=%s\ns2=%s\ns3=%s' % (s1, s2, s3))
						
						argstr = re.findall('\((.*)\)', call_str)[0]
						# arglist=argstr.split(',')
						# logme.debug('arglist=>',arglist)
						# logme.debug('size=>',len(arglist))
						# logme.debug('methodname=>',methodname)
						# logme.debug('argstr=>',argstr)
						call_str = ''
						if argstr.strip():
							if methodname.startswith('db'):
								call_str = '%s(\"%s\",taskid=%s,callername=%s)' % (methodname, s1, s2, s3)
							# logme.debug('参数加双引号后表达式=>', call_str)
							else:
								call_str = '%s(%s,taskid=%s,callername=%s)' % (methodname, s1, s2, s3)
						
						else:
							call_str = '%s()' % (methodname,)
						# call_str1='createPhone()'
						# logme.debug(eval(call_str1))
						
						# logme.debug('最终计算=>', call_str)
						res = eval(call_str)
						if res[0] is not 'success':
							return res
					
					except:
						logme.debug(traceback.format_exc())
						return ('error', "非法表达式[%s]" % call_str)
			
			else:
				logme.debug('fucobj=>', funcobj)
				user = funcobj.author
				flag = funcobj.flag
				f = __import__('manager.storage.private.Function.%s.func_%s' % (user, flag), fromlist=True)
				callstr = "f.%s" % (call_str)
				# logme.debug(callstr)
				callstr = callstr.replace('\n', '')
				logme.debug('ccc=>\n', callstr)
				logme.debug('\n' in callstr)
				res = eval(callstr)
				logme.debug("调用用户定义表达式:%s 结果为:%s" % (callstr, res))
			
			return ('success', res)
		
		except Exception as e:
			logme.debug(traceback.format_exc())
			return ('error', '调用表达式[%s]异常[%s]' % (call_str, traceback.format_exc()))
	
	@classmethod
	def getfuncname(cls, body):
		return re.findall("def[\s+]{1,}(.*?)\(.*?\):", body)


class EncryptUtils:
	'''
	加密工具
	'''
	# Des CBC
	# 自定IV向量
	Des_IV = 'itfdesiv'
	key = 'blackstone20191111'
	
	@staticmethod
	def des_encrypt(str_):
		# str 明文password
		# key uid
		Des_Key = (EncryptUtils.key + "0000")[0:8]
		k = des(Des_Key, CBC, EncryptUtils.Des_IV, pad=None, padmode=PAD_PKCS5)
		EncryptStr = k.encrypt(str_)
		return base64.b64encode(EncryptStr).decode()  # 转base64编码返回
	
	@staticmethod
	def des_decrypt(str_):
		# str 密文password
		# key uid
		Des_Key = (EncryptUtils.key + "0000")[0:8]
		EncryptStr = base64.b64decode(str_)
		# logme.debug(EncryptStr)
		k = des(Des_Key, CBC, EncryptUtils.Des_IV, pad=None, padmode=PAD_PKCS5)
		DecryptStr = k.decrypt(EncryptStr)
		return DecryptStr.decode()
	
	@staticmethod
	def base64_encrypt(str_):
		return base64.b64encode(str_.encode('utf-8')).decode()
	
	@staticmethod
	def base64_decrypt(str_):
		return base64.b64decode(str_).decode(encoding='utf-8')
	
	@staticmethod
	def md5_encrypt(str_):
		return md5(str_.encode('utf-8')).hexdigest()
