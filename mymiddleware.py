#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-11-01 15:39:20
# @Author  : Blackstone
# @to      :
from django.db.models import Q
from django.shortcuts import HttpResponseRedirect
from django.http import HttpResponse, JsonResponse
from ME2.settings import logme
from manager import models
from login import models as lm
from manager.core import simplejson
import re, os, traceback
from manager.context import get_operate_name
from manager.context import Me2Log as logger
try:
	from django.utils.deprecation import MiddlewareMixin  # Django 1.10.x
except ImportError:
	MiddlewareMixin = object  # Django 1.4.x - Django 1.9.x


class Interceptor(MiddlewareMixin):
	
	def _repeat_check(self, request):
		"""
		字段重复校验

		"""
		
		_meta = {
			'Function': 'description',
			'Interface': 'name',
			'Tag': 'name',
			# 'Variable': 'key',
			'DBCon': 'description',
			'Step': 'description',
			'Case': 'description',
			'Plan': 'description',
			'RemoteLog': 'description'
		}
		_m1 = {
			'Function': '函数',
			'Interface': '接口',
			# 'Variable': '变量',
			'DBCon': '数据连接',
			'Step': '步骤',
			'Case': '用例',
			'Plan': '计划',
			'RemoteLog': '远程日志',
			'Tag': '标签'
		}
		_m2 = {
			'name': '名称',
			'description': '描述',
			'key': '键名'
		}
		# op=None
		tmp = request.path.split('?')[0]
		# tmp=tmp.replace(tmp[-1],'')
		simplename = tmp.split('/')[-2]
		# logger.info('simplename=>',simplename)
		
		flag1 = simplename.startswith('add')
		flag2 = simplename.startswith('edit')
		
		# logger.info('flag=>',flag1,flag2)
		if flag1:
			key = simplename.replace('add', '').lower()
			# logger.info('key=>',key)
			mkey = getkey(_meta, key)
			if mkey:
				logger.info('==[新增]字段重复校验====')
				actionV = request.POST.get(_meta[mkey])
				callstr = "list(models.%s.objects.filter(%s='%s'))" % (mkey, _meta[mkey], actionV)
				if mkey == 'Function':
					callstr = "list(models.Function.objects.filter(name='%s'))" % \
					          re.findall('def (.*?)\(.*?\)', request.POST.get('body'))[0]
				if mkey == 'DBCon':
					schemevalue=request.POST.get('schemevalue')
					description=request.POST.get('description')
					callstr = "list(models.DBCon.objects.filter(description='%s',scheme='%s'))" % \
					          (description,schemevalue)
					qssize = len(eval(callstr))
					if qssize == 0:
						return 'success', ''
					else:
						return 'fail', "配置方案【%s】下已存在描述为【%s】的数据连接" % (schemevalue, description)
				qssize = len(eval(callstr))
				logger.info('callstr=>%s size=%s' % (callstr, qssize))
				logger.info('url[%s]字段[%s]重复验证 已存在[%s]条' % (request.path, _meta[mkey], qssize))
				if qssize == 0:
					return ('success', '')
				else:
					return ('fail', "%s%s重复" % (_m1[mkey], _m2[_meta[mkey]]))
			else:
				return ('success', '')
		
		elif flag2:
			repeatid = None
			call_str = ''
			try:
				key = simplename.replace('edit', '').lower()
				# logger.info('key=>',key)
				mkey = getkey(_meta, key)
				if mkey:
					logger.info('==[编辑]字段重复校验====')
					if mkey == 'DBCon':
						schemevalue = request.POST.get('schemevalue')
						description = request.POST.get('description')
						id=request.POST.get('id')
						oldcon = models.DBCon.objects.filter(~Q(id=id) & Q(description=description, scheme=schemevalue))
						qssize = len(oldcon)
						logger.info(oldcon)
						if qssize == 0:
							return 'success', ''
						else:
							msg = "配置方案【%s】下已存在描述为【%s】的数据连接" % (schemevalue, description) if schemevalue!='' else "已存在描述名为【%s】的全局数据连接配置"%description
							return 'fail', msg
					actionV = request.POST.get(_meta[mkey])
					call_str = "models.%s.objects.get(%s='%s').id" % (mkey, _meta[mkey], actionV)
					logger.info('callstr=>', call_str)
					call_id = request.POST.get('id')
					repeatid = eval(call_str)
					
					logger.info('repeatid=>', repeatid)
					
					if str(call_id) == str(repeatid):
						return ('success', '')
					else:
						if repeatid:
							return ('fail', "%s%s重复" % (_m1[mkey], _m2[_meta[mkey]]))
				else:
					return ('success', '')
			except:
				logger.error(traceback.format_exc())
				return ('success', '')
		
		else:
			return ('success', '')
	
	def _session_check(self, request):
		'''
		session校验
		'''
		if request.path.startswith('/manager'):
			if request.session.get('username', None):
				return True
			else:
				logger.info('session校验不通过 跳到登录页面')
				return False

		return True


	def _log_operation(self,request):
		'''操作日志记录
		'''
		opcode=''
		url=request.path
		params={**dict(request.GET),**dict(request.POST)}
		for ok in params:
			params[ok]=params.get(ok)[0]

		##tree操作
		if url.__contains__('treecontrol'):
			# if params.get('action') in ['view','loadpage']:
			# 	return;

			opcode=params.get('action')
			ol=models.OperateLog()
			ol.opcode=opcode
			ol.opname=get_operate_name(opcode)
			ol.description=''
			ol.author=lm.User.objects.get(name=request.session.get('username'))
			ol.save()
			logger.info('==记录树操作 %s'%ol)
		



	def _print_info_call_msg(self,request):
		if not request.path.startswith('/static'):
			logger.info("=============================【%s】调用[%s]=============================" %(request.session.get('username','未登录'),request.path))
		a=dict(request.GET)
		b=dict(request.POST)
		o={**a,**b}
		for ok in o:
			o[ok]=o.get(ok)[0]
		if o:
			logger.warn('请求参数:'+str(o))
			pass
		
	
	def process_request(self, request):

		self._print_info_call_msg(request)

		# self._log_operation(request)
		
		session_check_result = self._session_check(request)
		repeat_check_result = self._repeat_check(request)
		# field_common_check_result=self._field_common_check(request)
		username = request.session.get('username')
		if session_check_result == False:
			return HttpResponseRedirect('/account/login/')
		
		if repeat_check_result[0] is not 'success':
			return JsonResponse(simplejson(code=101, msg=repeat_check_result[1]), safe=False)


def getkey(d,key):
	for k in d:
		if key.lower() == k.lower():
			return k
	return None

